#!/usr/bin/env python3
"""Cancel all move_base goals; the motor watchdog also enforces command expiry."""
import sys
import time
import actionlib
import rospy
from move_base_msgs.msg import MoveBaseAction


def main():
    rospy.init_node('cancel_movement', anonymous=True)
    client = actionlib.SimpleActionClient('/move_base', MoveBaseAction)
    if not client.wait_for_server(rospy.Duration(5)):
        raise RuntimeError('move_base action server unavailable')
    client.cancel_all_goals()
    time.sleep(0.3)  # Let the established TCP connection flush cancellation.
    print('Cancellation requested; verify /move_base/status and zero /cmd_vel')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
