"""Run locally with unittest, or through catkin_add_nosetests on Noetic."""
import ast
import importlib.util
import math
from pathlib import Path
import sys
import threading
import tempfile
import types
import unittest
from unittest.mock import Mock, patch
import xml.etree.ElementTree as ET

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE / 'src'))
from myhealthkit_navigation.core import PoseVelocity, angle_delta, wheel_duties, validate_point


class GeometryTests(unittest.TestCase):
    def test_straight_velocity_in_body_frame(self):
        est = PoseVelocity(tau=0)
        self.assertIsNone(est.update(1, 0, 0, math.pi/2))
        vx, vy, wz = est.update(1.1, 0, .02, math.pi/2)
        self.assertAlmostEqual(vx, .2)
        self.assertAlmostEqual(vy, 0)
        self.assertAlmostEqual(wz, 0)

    def test_angle_wrap_is_small_positive_turn(self):
        est = PoseVelocity(tau=0)
        est.update(1, 0, 0, math.pi-.01)
        self.assertAlmostEqual(est.update(1.1, 0, 0, -math.pi+.01)[2], .2)

    def test_duplicate_and_out_of_order_do_not_change_baseline(self):
        est = PoseVelocity(tau=0)
        est.update(1, 0, 0, 0)
        self.assertIsNone(est.update(.9, 10, 0, 0))
        self.assertIsNone(est.update(1, 10, 0, 0))
        self.assertAlmostEqual(est.update(1.1, .01, 0, 0)[0], .1)

    def test_gap_reinitializes_velocity(self):
        est = PoseVelocity(tau=0)
        est.update(1, 0, 0, 0)
        self.assertIsNone(est.update(2, 0, 0, 0))
        self.assertAlmostEqual(est.update(2.1, .01, 0, 0)[0], .1)

    def test_jump_and_nonfinite_rejected(self):
        est = PoseVelocity()
        est.update(1, 0, 0, 0)
        for sample in [(1.1, 1, 0, 0), (1.1, 0, 0, 2), (1.1, float('nan'), 0, 0)]:
            with self.assertRaises(ValueError):
                est.update(*sample)

    def test_stationary_and_filter(self):
        est = PoseVelocity(tau=.1)
        est.update(1, 0, 0, 0)
        self.assertEqual(est.update(1.1, 0, 0, 0), (0, 0, 0))
        self.assertAlmostEqual(est.update(1.2, .02, 0, 0)[0], .1)

    def test_differential_drive_calibration(self):
        self.assertEqual(wheel_duties(.1, 0, .2, .5), (.2, .2))
        self.assertEqual(wheel_duties(0, 1, .2, .5), (-.2, .2))
        self.assertEqual(wheel_duties(-.1, 0, .2, .5), (-.2, -.2))

    def test_saturation_preserves_turn_ratio(self):
        left, right = wheel_duties(1, 2, .2, .5)
        self.assertAlmostEqual(right, 1)
        self.assertAlmostEqual(left/right, .8/1.2)

    def test_bad_calibration_and_commands(self):
        for args in [(0, 0, 0, .5), (0, 0, .2, 0), (float('nan'), 0, .2, .5)]:
            with self.assertRaises(ValueError):
                wheel_duties(*args)

    def test_planar_goal_validation_and_normalization(self):
        result = validate_point(dict(x=1, y=2, qz=2, qw=2))
        for actual, expected in zip(result, (1, 2, math.sqrt(.5), math.sqrt(.5))):
            self.assertAlmostEqual(actual, expected)
        for point in [dict(x=1, y=2, qz=0, qw=0), dict(x=1, y=2, z=1), dict(x=float('inf'), y=2)]:
            with self.assertRaises(ValueError):
                validate_point(point)


def load_with_ros_stubs(script):
    modules = {name: types.ModuleType(name) for name in
               ['rospy', 'tf2_ros', 'geometry_msgs', 'geometry_msgs.msg',
                'nav_msgs', 'nav_msgs.msg', 'sensor_msgs', 'sensor_msgs.msg',
                'std_msgs', 'std_msgs.msg', 'gpiozero', 'actionlib',
                'actionlib_msgs', 'actionlib_msgs.msg', 'move_base_msgs', 'move_base_msgs.msg']}
    modules['actionlib_msgs.msg'].GoalStatus = types.SimpleNamespace(SUCCEEDED=3)
    modules['move_base_msgs.msg'].MoveBaseAction = object
    modules['move_base_msgs.msg'].MoveBaseGoal = lambda: types.SimpleNamespace(target_pose=types.SimpleNamespace(
        header=types.SimpleNamespace(), pose=types.SimpleNamespace(
            position=types.SimpleNamespace(), orientation=types.SimpleNamespace())))
    for module, names in [('geometry_msgs.msg', ['Twist', 'PoseStamped', 'TransformStamped']),
                          ('nav_msgs.msg', ['Odometry']), ('sensor_msgs.msg', ['LaserScan']),
                          ('std_msgs.msg', ['Bool']), ('gpiozero', ['PWMOutputDevice', 'DigitalOutputDevice'])]:
        for name in names:
            setattr(modules[module], name, lambda **kw: types.SimpleNamespace(**kw))
    modules['rospy'].logerr_throttle = Mock()
    spec = importlib.util.spec_from_file_location(script, PACKAGE / 'scripts' / (script+'.py'))
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, modules):
        spec.loader.exec_module(module)
    return module


class WatchdogTests(unittest.TestCase):
    def setUp(self):
        self.module = load_with_ros_stubs('motor_controller')
        self.node = self.module.MotorController.__new__(self.module.MotorController)
        n = self.node
        n.lock = threading.RLock()
        n.closed = False
        n.devices = [types.SimpleNamespace(value=0, close=Mock()) for _ in range(8)]
        n.stby = Mock()
        n.healthy = True
        n.last_health = n.last_command = 10.0
        n.timeout, n.health_timeout = .3, .2
        n.wheel_base, n.full_speed = .2, .5
        n.max_linear, n.max_angular = .15, .4
        n.signs = [1, 1, 1, 1]
        n.command = (.1, 0)

    def test_fresh_commands_drive_expected_channels(self):
        with patch.object(self.module.time, 'monotonic', return_value=10.1):
            self.node.step()
        self.assertEqual([d.value for d in self.node.devices], [.2, 0]*4)
        self.node.stby.on.assert_called_once()

    def test_expired_command_stops_even_with_fresh_health(self):
        self.node.last_health = 10.4
        with patch.object(self.module.time, 'monotonic', return_value=10.4):
            self.node.step()
        self.assertTrue(all(d.value == 0 for d in self.node.devices))
        self.node.stby.on.assert_not_called()

    def test_dead_localization_node_stops_even_with_fresh_command(self):
        self.node.last_command = 10.3
        with patch.object(self.module.time, 'monotonic', return_value=10.3):
            self.node.step()
        self.node.stby.on.assert_not_called()

    def test_unhealthy_invalidates_old_command(self):
        self.node.health(types.SimpleNamespace(data=False))
        self.assertIsNone(self.node.last_command)
        self.node.stby.off.assert_called()

    def test_nan_command_stops(self):
        self.node.cmd(types.SimpleNamespace(linear=types.SimpleNamespace(x=float('nan')),
                                           angular=types.SimpleNamespace(z=0)))
        self.assertIsNone(self.node.last_command)
        self.node.stby.off.assert_called()

    def test_shutdown_releases_gpio_and_disables_bridge(self):
        self.node.close()
        self.node.close()
        self.node.stby.close.assert_called_once()
        for device in self.node.devices:
            device.close.assert_called_once()

    def test_lidar_timeout_latches_until_restart(self):
        module = load_with_ros_stubs('lidar_odometry')
        node = module.LidarOdometry.__new__(module.LidarOdometry)
        node.lock = threading.RLock()
        node.timeout = .5
        node.ready, node.fault = True, False
        node.last_scan = node.last_pose = 10
        node.health = Mock()
        with patch.object(module.time, 'monotonic', return_value=11):
            node.tick(None)
        self.assertTrue(node.fault)
        self.assertFalse(node.health.publish.call_args[0][0].data)
        node.last_scan = node.last_pose = 11
        with patch.object(module.time, 'monotonic', return_value=11):
            node.tick(None)
        self.assertFalse(node.health.publish.call_args[0][0].data)

    def test_lidar_publishes_coherent_tf_pose_and_body_twist(self):
        module = load_with_ros_stubs('lidar_odometry')
        ns = types.SimpleNamespace
        module.Odometry = lambda: ns(header=ns(), child_frame_id='',
            pose=ns(pose=ns(position=ns(), orientation=ns()), covariance=[0.0]*36),
            twist=ns(twist=ns(linear=ns(), angular=ns()), covariance=[0.0]*36))
        module.TransformStamped = lambda: ns(transform=ns(translation=ns()))
        node = module.LidarOdometry.__new__(module.LidarOdometry)
        node.lock = threading.RLock()
        node.fault = node.ready = False
        node.timeout = .5
        node.last_scan = 10
        node.estimator = PoseVelocity(tau=0)
        node.fresh_stamp = lambda stamp: True
        node.tf, node.odom = Mock(), Mock()
        def pose(stamp, y):
            return ns(header=ns(frame_id='map', stamp=ns(to_sec=lambda: stamp)),
                      pose=ns(position=ns(x=0, y=y),
                              orientation=ns(x=0,y=0,z=math.sqrt(.5),w=math.sqrt(.5))))
        with patch.object(module.time, 'monotonic', return_value=10):
            node.pose(pose(1, 0))
            node.pose(pose(1.1, .02))
        odom = node.odom.publish.call_args[0][0]
        transform = node.tf.sendTransform.call_args[0][0]
        self.assertEqual((odom.header.frame_id, odom.child_frame_id), ('odom', 'base_link'))
        self.assertEqual(transform.header.stamp.to_sec(), 1.1)
        self.assertEqual(transform.child_frame_id, odom.child_frame_id)
        self.assertAlmostEqual(odom.twist.twist.linear.x, .2)
        self.assertAlmostEqual(odom.twist.twist.linear.y, 0)
        self.assertAlmostEqual(transform.transform.translation.y, odom.pose.pose.position.y)


class WiringTests(unittest.TestCase):
    def test_hector_has_no_competing_tf_or_odometry_publisher(self):
        root = ET.parse(PACKAGE / 'launch/myhealthkit.launch').getroot()
        hector = next(n for n in root.findall('node') if n.get('name') == 'hector_mapping')
        params = {p.get('name'): p.get('value') for p in hector.findall('param')}
        for name in ['pub_map_odom_transform', 'pub_map_scanmatch_transform', 'pub_odometry', 'use_tf_pose_start_estimate']:
            self.assertEqual(params[name], 'false')
        names = {n.get('name') for n in root.findall('node')}
        self.assertIn('lidar_odometry', names)
        self.assertNotIn('fake_odom_publisher', names)

    def test_server_qr_validation_matches_real_service(self):
        source = PACKAGE.parents[3] / 'server/services.py'
        tree = ast.parse(source.read_text(encoding='utf-8'))
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'validate_qr_code')
        import re
        namespace = dict(re=re)
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), 'exec'), namespace)
        parse = namespace['validate_qr_code']
        self.assertEqual(parse('location12'), 12)
        for value in ['', None, {}, 'location-1', 'location1\n', 'junk']:
            self.assertEqual(parse(value), -1)


class GoalTests(unittest.TestCase):
    def setUp(self):
        self.module = load_with_ros_stubs('go_to_point')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'points.yaml'
        self.path.write_text('- {id: 12, x: 1, y: 2, map_session: current}\n', encoding='utf-8')
        ros = self.module.rospy
        ros.myargv = lambda: ['go_to_point.py', '12']
        ros.init_node = Mock()
        ros.get_param = lambda key, default: str(self.path) if key.endswith('points_file') else 'current'
        ros.Duration = lambda seconds: seconds
        ros.Time = types.SimpleNamespace(now=lambda: 1)
        ros.wait_for_message = Mock(return_value=types.SimpleNamespace(data=True))
        self.client = Mock()
        self.module.actionlib.SimpleActionClient = Mock(return_value=self.client)
        self.client.wait_for_server.return_value = True
        self.client.send_goal.side_effect = lambda goal, done_cb, active_cb: active_cb()

    def test_action_goal_acknowledged_and_has_map_coordinates(self):
        with patch('builtins.print'):
            self.module.main()
        goal = self.client.send_goal.call_args[0][0].target_pose
        self.assertEqual(goal.header.frame_id, 'map')
        self.assertEqual((goal.pose.position.x, goal.pose.position.y), (1, 2))
        self.client.wait_for_result.assert_not_called()

    def test_old_session_refused_before_moving(self):
        self.path.write_text('- {id: 12, x: 1, y: 2, map_session: old}\n', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.module.main()
        self.client.send_goal.assert_not_called()

    def test_unhealthy_lidar_refuses_goal(self):
        self.module.rospy.wait_for_message.return_value.data = False
        with self.assertRaises(RuntimeError):
            self.module.main()
        self.client.send_goal.assert_not_called()

    def test_missing_server_refuses_goal(self):
        self.client.wait_for_server.return_value = False
        with self.assertRaises(RuntimeError):
            self.module.main()
        self.client.send_goal.assert_not_called()

    def test_rejected_goal_is_not_reported_as_accepted(self):
        self.client.send_goal.side_effect = lambda goal, done_cb, active_cb: done_cb(5, None)
        with self.assertRaises(RuntimeError):
            self.module.main()

    def test_arrival_timeout_cancels_goal(self):
        self.module.rospy.myargv = lambda: ['go_to_point.py', '12', '--wait', '--timeout', '1']
        self.client.wait_for_result.return_value = False
        with self.assertRaises(RuntimeError):
            self.module.main()
        self.client.cancel_goal.assert_called_once()


class ApiTests(unittest.TestCase):
    def setUp(self):
        source = PACKAGE.parents[3] / 'server/app.py'
        tree = ast.parse(source.read_text(encoding='utf-8'))
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'request_myhealthkit')
        function.decorator_list = []
        self.send = Mock()
        self.request = types.SimpleNamespace(get_json=Mock(return_value={'message': 'location12'}))
        self.namespace = dict(request=self.request, jsonify=lambda **kw: kw,
                              validate_qr_code=lambda s: 12 if s == 'location12' else -1,
                              send_robot=self.send, app=types.SimpleNamespace(logger=Mock()))
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), 'exec'), self.namespace)

    def test_request_actually_dispatches_and_reports_acceptance(self):
        data, status = self.namespace['request_myhealthkit']()
        self.assertEqual(status, 202)
        self.assertEqual(data['status'], 'accepted')
        self.send.assert_called_once_with(12)

    def test_invalid_json_never_dispatches(self):
        for value in [None, [], 'wrong', {'message': ''}]:
            self.request.get_json.return_value = value
            self.assertEqual(self.namespace['request_myhealthkit']()[1], 400)
        self.send.assert_not_called()

    def test_subprocess_failure_is_service_unavailable(self):
        self.send.side_effect = RuntimeError('No navigation')
        self.assertEqual(self.namespace['request_myhealthkit']()[1], 503)


if __name__ == '__main__':
    unittest.main()
