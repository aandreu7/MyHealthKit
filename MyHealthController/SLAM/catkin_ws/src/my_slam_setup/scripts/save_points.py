#!/usr/bin/env python3
"""Capture map-frame destinations on a dedicated topic without moving the robot."""
import os
import tempfile
import threading
import rospy
import yaml
from geometry_msgs.msg import PoseStamped
from myhealthkit_navigation.core import validate_point


class PointSaver:
    def __init__(self):
        self.path = os.path.expanduser(rospy.get_param('/myhealthkit/points_file',
                                  '~/.ros/myhealthkit/saved_points.yaml'))
        self.lock = threading.Lock()
        rospy.Subscriber('/myhealthkit/save_point', PoseStamped, self.callback, queue_size=1)

    def callback(self, msg):
        if msg.header.frame_id != 'map':
            rospy.logerr('Point must be expressed in map')
            return
        with self.lock:
            try:
                position, q = msg.pose.position, msg.pose.orientation
                point = dict(x=position.x, y=position.y, z=position.z,
                             qx=q.x, qy=q.y, qz=q.z, qw=q.w)
                x, y, qz, qw = validate_point(point)
                session = rospy.get_param('/myhealthkit/map_session', '')
                if not session:
                    raise ValueError('Start LiDAR navigation before recording points')
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                if os.path.exists(self.path):
                    with open(self.path, encoding='utf-8') as stream:
                        points = yaml.safe_load(stream) or []
                else:
                    points = []
                if not isinstance(points, list):
                    raise ValueError('Points file must be a list')
                point = dict(id=max([int(p['id']) for p in points]+[0])+1,
                             x=x, y=y, z=0.0, qx=0.0, qy=0.0, qz=qz, qw=qw,
                             map_session=session)
                points.append(point)
                fd, temp = tempfile.mkstemp(dir=os.path.dirname(self.path), suffix='.yaml')
                try:
                    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                        yaml.safe_dump(points, stream)
                    os.replace(temp, self.path)
                finally:
                    if os.path.exists(temp):
                        os.unlink(temp)
                rospy.loginfo('Saved point %s in %s', point['id'], self.path)
            except (ValueError, TypeError, KeyError, OSError, yaml.YAMLError) as exc:
                rospy.logerr('Cannot save point: %s', exc)


if __name__ == '__main__':
    rospy.init_node('point_saver')
    PointSaver()
    rospy.spin()
