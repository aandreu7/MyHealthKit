#!/usr/bin/env python3
import rospy
import tf2_ros
import geometry_msgs.msg
from geometry_msgs.msg import PoseStamped
import tf_conversions

class FakeOdomPublisher:
    def __init__(self):
        self.tf_broadcaster = tf2_ros.TransformBroadcaster()
        self.sub = rospy.Subscriber('/slam_out_pose', PoseStamped, self.pose_callback)
        rospy.loginfo("FakeOdomPublisher node started, listening to /slam_out_pose")

    def pose_callback(self, msg):
        t = geometry_msgs.msg.TransformStamped()

        t.header.stamp = msg.header.stamp
        #t.header.stamp = rospy.Time.now()
        t.header.frame_id = "odom"
        t.child_frame_id = "base_link"

        # Copy position from slam_out_pose
        t.transform.translation.x = msg.pose.position.x
        t.transform.translation.y = msg.pose.position.y
        t.transform.translation.z = msg.pose.position.z

        # Copy orientation
        t.transform.rotation = msg.pose.orientation

        self.tf_broadcaster.sendTransform(t)
        rospy.logdebug(f"Published fake odom transform from slam_out_pose")

def main():
    rospy.init_node('fake_odom_publisher')
    fake_odom = FakeOdomPublisher()
    rospy.spin()

if __name__ == '__main__':
    main()
