import RPi.GPIO as GPIO
from time import sleep
import argparse

# --------------------------
# GPIO pins configuration for one motor
MOTOR_IN1 = 19      # AIN1 - Direction
MOTOR_IN2 = 18      # AIN2 - PWM
STBY_PIN = 17       # STBY must be set HIGH to enable the driver

# --------------------------
# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(MOTOR_IN1, GPIO.OUT)
GPIO.setup(MOTOR_IN2, GPIO.OUT)
GPIO.setup(STBY_PIN, GPIO.OUT)

# Enable the motor driver by setting STBY high
GPIO.output(STBY_PIN, GPIO.HIGH)

# Initialize PWM on MOTOR_IN2 (AIN2)
pwm = GPIO.PWM(MOTOR_IN2, 1000)  # 1kHz frequency
pwm.start(0)

# --------------------------
def move_motor(speed=0.6, duration=3):
    """
    Rotate the motor forward at a given speed for a given duration.
    :param speed: float [0.0 .. 1.0]
    :param duration: seconds
    """
    GPIO.output(MOTOR_IN1, GPIO.LOW)           # Set direction forward
    pwm.ChangeDutyCycle(speed * 100)           # Apply PWM to AIN2

    sleep(duration)
    stop_motor()

def stop_motor():
    """
    Stop the motor.
    """
    pwm.ChangeDutyCycle(0)                     # Stop PWM
    GPIO.output(MOTOR_IN1, GPIO.LOW)           # Set both IN1 and IN2 to LOW

# --------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Move one DC motor using PWM.")
    parser.add_argument('--speed', type=float, default=0.6, help='Speed value (0.0 to 1.0). Default: 0.6')
    parser.add_argument('--duration', type=float, default=3.0, help='Duration in seconds. Default: 3.0')
    args = parser.parse_args()

    try:
        print("Running motor...")
        move_motor(speed=args.speed, duration=args.duration)
        print("Motor stopped.")
    finally:
        pwm.stop()
        GPIO.cleanup()
