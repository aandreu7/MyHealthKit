# This file should be located in /usr/local/bin
#!/bin/bash

sleep 10

# Waits till wlan0 has an IP assigned
while true; do
  IP=$(ip addr show wlan0 | grep "inet " | awk '{print $2}')
  if [ -n "$IP" ]; then
    echo "WiFi connected with IP $IP"
    break
  else
    echo "Waiting for a WiFi connection..."
    sleep 2
  fi
done

# Export ROS variables
export ROS_MASTER_URI=http://$IP:11311
export ROS_HOSTNAME=$IP

# Launches roscore in the background
roscore &

sleep 5

# Launches RPLidar C1
roslaunch rplidar_ros rplidar_c1.launch &


sleep 5

# Launches Hector SLAM
roslaunch hector_slam_launch myhealthkit.launch
