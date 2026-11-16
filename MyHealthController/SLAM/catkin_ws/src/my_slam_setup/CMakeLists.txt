cmake_minimum_required(VERSION 3.0.2)
project(my_slam_setup)
find_package(catkin REQUIRED COMPONENTS rospy geometry_msgs nav_msgs sensor_msgs
  std_msgs tf2_ros actionlib actionlib_msgs move_base_msgs)
catkin_python_setup()
catkin_package()
catkin_install_python(PROGRAMS
  scripts/lidar_odometry.py scripts/motor_controller.py scripts/go_to_point.py
  scripts/cancel_movement.py scripts/save_points.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})
install(DIRECTORY launch config DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})
if(CATKIN_ENABLE_TESTING)
  catkin_add_nosetests(tests)
endif()
