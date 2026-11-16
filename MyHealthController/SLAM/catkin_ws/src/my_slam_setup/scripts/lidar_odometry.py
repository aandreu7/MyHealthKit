#!/usr/bin/env python3
"""Derive odom + body velocity from Hector; never extrapolate missing scans."""
import math
import threading
import time
import uuid

import rospy
import tf2_ros
from geometry_msgs.msg import PoseStamped, TransformStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool
from myhealthkit_navigation.core import PoseVelocity


class LidarOdometry:
    def __init__(self):
        self.lock = threading.RLock()
        self.timeout = float(rospy.get_param('~data_timeout', 0.5))
        self.estimator = PoseVelocity(
            rospy.get_param('~max_linear', 0.6), rospy.get_param('~max_angular', 1.5),
            self.timeout, rospy.get_param('~velocity_filter_tau', 0.15))
        self.last_pose = self.last_scan = None
        self.ready = False
        self.fault = False
        rospy.set_param('/myhealthkit/map_session', str(uuid.uuid4()))
        self.odom = rospy.Publisher('/odom', Odometry, queue_size=1)
        self.health = rospy.Publisher('/navigation/healthy', Bool, queue_size=1)
        self.tf = tf2_ros.TransformBroadcaster()
        rospy.Subscriber('/scan', LaserScan, self.scan, queue_size=1)
        rospy.Subscriber('/slam_out_pose', PoseStamped, self.pose, queue_size=1)
        self.timer = rospy.Timer(rospy.Duration(0.05), self.tick)

    def fresh_stamp(self, stamp):
        age = (rospy.Time.now() - stamp).to_sec()
        return stamp.to_sec() > 0 and -0.05 <= age <= self.timeout

    def scan(self, msg):
        # Empty/all-invalid scans cannot establish that the environment is observable.
        count = sum(math.isfinite(r) and msg.range_min <= r <= msg.range_max for r in msg.ranges)
        with self.lock:
            if self.fresh_stamp(msg.header.stamp) and count >= 8:
                self.last_scan = time.monotonic()

    def fail(self, reason):
        self.fault = True
        self.ready = False
        rospy.logerr_throttle(2, '%s; stop navigation and restart after inspection', reason)

    def pose(self, msg):
        with self.lock:
            if self.fault or not self.fresh_stamp(msg.header.stamp):
                return
            if msg.header.frame_id != 'map':
                self.fail('Hector pose is not in map')
                return
            q = msg.pose.orientation
            norm = math.sqrt(q.x*q.x + q.y*q.y + q.z*q.z + q.w*q.w)
            if not math.isfinite(norm) or norm < 1e-6:
                self.fail('Invalid Hector orientation')
                return
            qx, qy, qz, qw = (v/norm for v in (q.x, q.y, q.z, q.w))
            yaw = math.atan2(2*(qw*qz+qx*qy), 1-2*(qy*qy+qz*qz))
            try:
                velocity = self.estimator.update(msg.header.stamp.to_sec(),
                                                 msg.pose.position.x, msg.pose.position.y, yaw)
            except ValueError as exc:
                self.fail(str(exc))
                return
            if velocity is None:
                return
            if self.last_scan is None or time.monotonic()-self.last_scan > self.timeout:
                return
            self.last_pose = time.monotonic()
            self.ready = True
            odom = Odometry()
            odom.header.stamp = msg.header.stamp
            odom.header.frame_id = 'odom'
            odom.child_frame_id = 'base_link'
            odom.pose.pose.position.x = msg.pose.position.x
            odom.pose.pose.position.y = msg.pose.position.y
            odom.pose.pose.orientation.z = math.sin(yaw/2)
            odom.pose.pose.orientation.w = math.cos(yaw/2)
            odom.twist.twist.linear.x, odom.twist.twist.linear.y, odom.twist.twist.angular.z = velocity
            # Conservative nominal uncertainty, not a scan-matching confidence metric.
            for i, variance in zip((0, 7, 14, 21, 28, 35), (0.04, 0.04, 1e6, 1e6, 1e6, 0.09)):
                odom.pose.covariance[i] = variance
                odom.twist.covariance[i] = variance
            transform = TransformStamped()
            transform.header = odom.header
            transform.child_frame_id = odom.child_frame_id
            transform.transform.translation.x = msg.pose.position.x
            transform.transform.translation.y = msg.pose.position.y
            transform.transform.rotation = odom.pose.pose.orientation
            self.tf.sendTransform(transform)
            self.odom.publish(odom)

    def tick(self, _event):
        with self.lock:
            now = time.monotonic()
            fresh = all(t is not None and now-t <= self.timeout for t in (self.last_scan, self.last_pose))
            if self.ready and not fresh:
                self.fail('LiDAR/SLAM data timed out')
            self.health.publish(Bool(data=self.ready and fresh and not self.fault))


if __name__ == '__main__':
    rospy.init_node('lidar_odometry')
    LidarOdometry()
    rospy.spin()
