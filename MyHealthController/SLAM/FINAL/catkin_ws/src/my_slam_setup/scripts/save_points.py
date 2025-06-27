import rospy
from geometry_msgs.msg import PoseStamped
import yaml

points = []

def callback(msg):
    # Create a point dictionary with unique ID and full pose (position + orientation)
    point = {
        'id': len(points) + 1,  # Unique integer ID starting from 1
        'x': msg.pose.position.x,
        'y': msg.pose.position.y,
        'z': msg.pose.position.z,
        'qx': msg.pose.orientation.x,
        'qy': msg.pose.orientation.y,
        'qz': msg.pose.orientation.z,
        'qw': msg.pose.orientation.w
    }
    points.append(point)
    # Save all points to file each time a new point is added
    with open('./saved_points.yaml', 'w') as f:
        yaml.dump(points, f)
    rospy.loginfo(f"Point saved with ID {point['id']}: {point}")

def main():
    rospy.init_node('point_saver')
    # Subscribe to 2D Nav Goal topic published by RViz
    rospy.Subscriber('/move_base_simple/goal', PoseStamped, callback)
    rospy.loginfo("Point saver node started, listening to /move_base_simple/goal")
    rospy.spin()

if __name__ == '__main__':
    main()
