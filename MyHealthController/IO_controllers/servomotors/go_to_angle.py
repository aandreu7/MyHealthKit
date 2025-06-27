import RPi.GPIO as GPIO
import time
import sys

def set_angle(angle, servo_pin, pwm):
    duty = 2 + (angle / 18)
    GPIO.output(servo_pin, True)
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)
    GPIO.output(servo_pin, False)
    pwm.ChangeDutyCycle(0)

def main():
    # Check for correct number of arguments
    if len(sys.argv) != 2:
        print("Usage: python3 servo_move.py <angle 0-180>")
        sys.exit(1)

    try:
        position = float(sys.argv[1])
        if not 0 <= position <= 180:
            raise ValueError
    except ValueError:
        print("Invalid input: position must be an float between 0 and 180.")
        sys.exit(1)

    # Convert position to angle
    SERVO_PIN = 14

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SERVO_PIN, GPIO.OUT)

    pwm = GPIO.PWM(SERVO_PIN, 50)  # 50 Hz (20 ms period)
    pwm.start(0)

    try:
        print("Spinning wheel...")
        set_angle(position, SERVO_PIN, pwm)
    except KeyboardInterrupt:
        pass
    finally:
        pwm.stop()
        GPIO.cleanup()

if __name__=="__main__":
    main()
