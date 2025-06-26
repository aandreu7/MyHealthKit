import rospy
from geometry_msgs.msg import Twist
from gpiozero import PWMOutputDevice, DigitalOutputDevice

# --------------------------
# GPIO pins configuration
# Each motor uses 2 pins for direction and PWM control
#
# Left side motors
LEFT_FRONT_IN1 = 18
LEFT_FRONT_IN2 = 27
LEFT_REAR_IN1 = 24
LEFT_REAR_IN2 = 25

# Right side motors
RIGHT_FRONT_IN1 = 22
RIGHT_FRONT_IN2 = 23
RIGHT_REAR_IN1 = 5
RIGHT_REAR_IN2 = 6

# Standby pin (required by TB6612FNG motor driver)
STBY_PIN = 21  # Adjust this GPIO pin as needed

# --------------------------
# Initialize PWMOutputDevice for each motor pin
# This allows software PWM for speed control in both directions

# Left motors
left_front_in1 = PWMOutputDevice(LEFT_FRONT_IN1)
left_front_in2 = PWMOutputDevice(LEFT_FRONT_IN2)
left_rear_in1 = PWMOutputDevice(LEFT_REAR_IN1)
left_rear_in2 = PWMOutputDevice(LEFT_REAR_IN2)

# Right motors
right_front_in1 = PWMOutputDevice(RIGHT_FRONT_IN1)
right_front_in2 = PWMOutputDevice(RIGHT_FRONT_IN2)
right_rear_in1 = PWMOutputDevice(RIGHT_REAR_IN1)
right_rear_in2 = PWMOutputDevice(RIGHT_REAR_IN2)

# Initialize STBY pin to enable motor driver
stby = DigitalOutputDevice(STBY_PIN)
stby.on()  # Set HIGH to enable the motor driver

# --------------------------
def set_motor_speed(in1_front, in2_front, in1_rear, in2_rear, speed):
    """
    Controls speed and direction of two motors on one side.
    :param in1_front: PWMOutputDevice for front motor IN1
    :param in2_front: PWMOutputDevice for front motor IN2
    :param in1_rear: PWMOutputDevice for rear motor IN1
    :param in2_rear: PWMOutputDevice for rear motor IN2
    :param speed: float [-1.0 .. 1.0], positive = forward, negative = backward
    """
    if speed > 0:
        # Forward motion: PWM on IN1, 0 on IN2
        in1_front.value = speed
        in2_front.value = 0
        in1_rear.value = speed
        in2_rear.value = 0
    elif speed < 0:
        # Reverse motion: PWM on IN2, 0 on IN1
        in1_front.value = 0
        in2_front.value = -speed
        in1_rear.value = 0
        in2_rear.value = -speed
    else:
        # Stop motors
        in1_front.value = 0
        in2_front.value = 0
        in1_rear.value = 0
        in2_rear.value = 0

# --------------------------
def cmd_vel_callback(msg):
    """
    Callback for /cmd_vel topic.
    Converts linear and angular velocities to left and right motor speeds.
    """
    linear = msg.linear.x      # Forward/backward speed (m/s)
    angular = msg.angular.z    # Rotation speed (rad/s)

    # Distance between wheels (meters), adjust to your robot
    wheel_base = 0.20

    # Compute speed for left and right side (differential drive)
    speed_right = linear + (angular * wheel_base / 2.0)
    speed_left = linear - (angular * wheel_base / 2.0)

    # Normalize speeds so neither exceeds abs(1.0)
    max_speed = max(abs(speed_left), abs(speed_right), 1.0)
    speed_left /= max_speed
    speed_right /= max_speed

    # Apply speeds to motors
    set_motor_speed(left_front_in1, left_front_in2, left_rear_in1, left_rear_in2, speed_left)
    set_motor_speed(right_front_in1, right_front_in2, right_rear_in1, right_rear_in2, speed_right)

# --------------------------
def main():
    rospy.init_node('motor_controller')
    rospy.Subscriber('/cmd_vel', Twist, cmd_vel_callback)
    rospy.loginfo("Motor controller node started, waiting for /cmd_vel messages...")
    rospy.spin()

if __name__ == '__main__':
    main()
