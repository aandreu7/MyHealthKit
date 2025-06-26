import RPi.GPIO as GPIO
import time
import sys

def set_angle(angle, servo_pin, pwm):
    """
    Move the servo to a specific angle.
    :param angle: Desired angle in degrees (0 to 180)
    """
    duty = 2 + (angle / 18)  # Convert angle to duty cycle
    GPIO.output(servo_pin, True)
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)
    GPIO.output(servo_pin, False)
    pwm.ChangeDutyCycle(0)

def main():
    # Check argument
    if len(sys.argv) != 2:
        print("Usage: python3 open_trapdoor.py <1|0> \n 1 -> Open Trapdoor \n 0 -> Close Trapdoor.")
        sys.exit(1)

    try:
        position = int(sys.argv[1])
        if not 0 <= position <= 1:
            raise ValueError
    except ValueError:
        print("Invalid input: Trapdoor action must be an integer either 0 or 1.")
        sys.exit(1) 

    # Set GPIO pin where the servo is connected
    SERVO_PIN = 15

    # Setup GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SERVO_PIN, GPIO.OUT)

    pwm = GPIO.PWM(SERVO_PIN, 50)  # 50 Hz
    pwm.start(0)

    try:
        if position == 1:
            print("Opening trapdoor...")
            set_angle(170, SERVO_PIN, pwm)
        elif position == 0:
            print("Closing trapdoor...")
            set_angle(110.15, SERVO_PIN, pwm)
    finally:
        time.sleep(2)
        pwm.stop()
        GPIO.cleanup()

if __name__ == "__main__":
    main()
