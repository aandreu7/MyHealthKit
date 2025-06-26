#!/usr/bin/env python
import rospy
from actionlib_msgs.msg import GoalID

def cancel_all_goals():
    rospy.init_node('cancel_move_base_goal')
    pub = rospy.Publisher('/move_base/cancel', GoalID, queue_size=1)
    rospy.sleep(1)
    pub.publish(GoalID()) # Void message

if __name__ == '__main__':
    cancel_all_goals()
