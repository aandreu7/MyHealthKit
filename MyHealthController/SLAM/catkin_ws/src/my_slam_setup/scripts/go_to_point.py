#!/usr/bin/env python3
"""Submit a saved map-frame goal through move_base's action server."""
import argparse
import math
import os
import threading
import sys

import actionlib
import rospy
import yaml
from actionlib_msgs.msg import GoalStatus
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from std_msgs.msg import Bool
from myhealthkit_navigation.core import validate_point


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('point_id', type=int)
    parser.add_argument('--wait', action='store_true', help='Wait for arrival, not only acceptance')
    parser.add_argument('--timeout', type=float, default=180.0)
    args = parser.parse_args(rospy.myargv()[1:])
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        raise ValueError('Timeout must be positive')
    rospy.init_node('go_to_point', anonymous=True)
    default_path = os.path.expanduser('~/.ros/myhealthkit/saved_points.yaml')
    path = os.path.expanduser(rospy.get_param('/myhealthkit/points_file', default_path))
    with open(path, encoding='utf-8') as stream:
        points = yaml.safe_load(stream) or []
    if not isinstance(points, list):
        raise ValueError('Points file must contain a list')
    matches = [point for point in points if point.get('id') == args.point_id]
    if len(matches) != 1:
        raise ValueError('Goal ID missing or duplicated: %s' % args.point_id)
    session = rospy.get_param('/myhealthkit/map_session', '')
    if not session or matches[0].get('map_session') != session:
        raise ValueError('Destination belongs to another map session; record it again')
    x, y, qz, qw = validate_point(matches[0])
    healthy = rospy.wait_for_message('/navigation/healthy', Bool, timeout=2.0)
    if not healthy.data:
        raise RuntimeError('LiDAR localization is not healthy')
    client = actionlib.SimpleActionClient('/move_base', MoveBaseAction)
    if not client.wait_for_server(rospy.Duration(5)):
        raise RuntimeError('move_base action server unavailable')
    goal = MoveBaseGoal()
    goal.target_pose.header.frame_id = 'map'
    goal.target_pose.header.stamp = rospy.Time.now()
    goal.target_pose.pose.position.x = x
    goal.target_pose.pose.position.y = y
    goal.target_pose.pose.orientation.z = qz
    goal.target_pose.pose.orientation.w = qw
    acknowledged = threading.Event()
    terminal = []
    def done(status, result):
        terminal.append(status)
        acknowledged.set()
    client.send_goal(goal, done_cb=done, active_cb=acknowledged.set)
    if not acknowledged.wait(3.0):
        client.cancel_goal()
        raise RuntimeError('No goal acknowledgement from move_base')
    if terminal and terminal[0] != GoalStatus.SUCCEEDED:
        raise RuntimeError('Goal rejected/aborted: %s' % terminal[0])
    if args.wait:
        if not client.wait_for_result(rospy.Duration(args.timeout)):
            client.cancel_goal()
            raise RuntimeError('Navigation timed out; cancellation requested')
        if client.get_state() != GoalStatus.SUCCEEDED:
            raise RuntimeError('Navigation failed: %s' % client.get_goal_status_text())
        print('ARRIVED')
    else:
        print('ACCEPTED (arrival not yet confirmed)')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
