#!/usr/bin/env python
import rospy
import yaml
import sys
from geometry_msgs.msg import PoseStamped

def load_point_by_id(file_path, point_id):
    with open(file_path, 'r') as f:
        points = yaml.safe_load(f)
    for point in points:
        if point.get('id') == point_id:
            return point
    return None

def send_goal(point):
    pub = rospy.Publisher('/move_base_simple/goal', PoseStamped, queue_size=1)
    rospy.sleep(1)  # Give time to connect to publisher

    goal = PoseStamped()
    goal.header.stamp = rospy.Time.now()
    goal.header.frame_id = "map"  # Important: goal in global frame

    goal.pose.position.x = point['x']
    goal.pose.position.y = point['y']
    goal.pose.position.z = point['z']
    goal.pose.orientation.x = point.get('qx', 0.0)
    goal.pose.orientation.y = point.get('qy', 0.0)
    goal.pose.orientation.z = point.get('qz', 0.0)
    goal.pose.orientation.w = point.get('qw', 1.0)

    rospy.loginfo("Sending goal to move_base:")
    rospy.loginfo(goal)
    pub.publish(goal)

def main():
    rospy.init_node('go_to_point_node')

    if len(sys.argv) < 2:
        rospy.logerr("Usage: rosrun my_slam_setup go_to_point.py <ID>")
        sys.exit(1)

    point_id = int(sys.argv[1])
    file_path = rospy.get_param("~points_file", "./saved_points.yaml")

    point = load_point_by_id(file_path, point_id)
    if not point:
        rospy.logerr(f"Point with ID {point_id} not found in {file_path}")
        sys.exit(1)

    send_goal(point)

if __name__ == "__main__":
    main()
