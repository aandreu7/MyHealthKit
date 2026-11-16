#!/usr/bin/env python3
"""Compatibility entry point. Source the catkin workspace before running."""
import os
os.execvp('rosrun', ['rosrun', 'my_slam_setup', 'motor_controller.py'])
