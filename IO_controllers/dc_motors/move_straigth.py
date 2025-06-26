from gpiozero import PWMOutputDevice
from time import sleep
import argparse

# --------------------------
# GPIO pins configuration
LEFT_FRONT_IN1 = 18
LEFT_FRONT_IN2 = 27
LEFT_REAR_IN1 = 24
LEFT_REAR_IN2 = 25

RIGHT_FRONT_IN1 = 22
RIGHT_FRONT_IN2 = 23
RIGHT_REAR_IN1 = 5
RIGHT_REAR_IN2 = 6

# --------------------------
# Initialize PWMOutputDevice for each motor pin
left_front_in1 = PWMOutputDevice(LEFT_FRONT_IN1)
left_front_in2 = PWMOutputDevice(LEFT_FRONT_IN2)
left_rear_in1 = PWMOutputDevice(LEFT_REAR_IN1)
left_rear_in2 = PWMOutputDevice(LEFT_REAR_IN2)

right_front_in1 = PWMOutputDevice(RIGHT_FRONT_IN1)
right_front_in2 = PWMOutputDevice(RIGHT_FRONT_IN2)
right_rear_in1 = PWMOutputDevice(RIGHT_REAR_IN1)
right_rear_in2 = PWMOutputDevice(RIGHT_REAR_IN2)

# --------------------------
def move_forward(speed=0.6, duration=3):
    """
    Move the robot forward at a given speed for a given duration.
    :param speed: float [0.0 .. 1.0]
    :param duration: seconds
    """
    # Forward motion: IN1 = speed, IN2 = 0
    left_front_in1.value = speed
    left_front_in2.value = 0
    left_rear_in1.value = speed
    left_rear_in2.value = 0

    right_front_in1.value = speed
    right_front_in2.value = 0
    right_rear_in1.value = speed
    right_rear_in2.value = 0

    sleep(duration)
    stop()

def stop():
    """
    Stop all motors.
    """
    left_front_in1.value = 0
    left_front_in2.value = 0
    left_rear_in1.value = 0
    left_rear_in2.value = 0

    right_front_in1.value = 0
    right_front_in2.value = 0
    right_rear_in1.value = 0
    right_rear_in2.value = 0

# --------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Move the robot forward using PWM.")
    parser.add_argument('--speed', type=float, default=0.6, help='Speed value (0.0 to 1.0). Default: 0.6')
    parser.add_argument('--duration', type=float, default=3.0, help='Duration in seconds. Default: 3.0')
    args = parser.parse_args()

    print(f"Moving forward...")
    move_forward(speed=args.speed, duration=args.duration)
    print("Robot stopped.")
