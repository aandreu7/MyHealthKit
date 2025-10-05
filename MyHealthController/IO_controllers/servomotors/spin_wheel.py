import RPi.GPIO as GPIO
import time
import sys
import os

def set_angle(angle, servo_pin, pwm):
    filepath = "current_position.txt"

    # Read current duty from file
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            line = f.readline().strip()
            try:
                current_duty = float(line.split('=')[1])
            except (IndexError, ValueError):
                raise RuntimeError("File malformed")
    else:
        raise RuntimeError("File not found")

    print("Currenty duty: ", current_duty)

    # Calculate target duty for desired angle
    target_duty = 2 + (angle / 18)

    # Calculate number of steps and step size
    

    current_pos = (current_duty - 2)*18 / 22.5
    target_pos = angle / 22.5
    pos_diff = target_pos - current_pos

    steps_per_position = 1 # Number of steps per position change
    time_per_step = 2  # Time to wait per step in seconds
    overshootProtection=False  # Enable overshoot protection

    if (pos_diff > 0):
        total_steps = int(target_pos - current_pos) * steps_per_position
    else:   
        total_steps = int(current_pos - target_pos) * steps_per_position
        if (total_steps == 0):
            total_steps = 1
    total_steps = 1 # For simplicity, we can set it to 1 for immediate movement
    duty_diff = target_duty - current_duty
    step = duty_diff / total_steps
    duty = current_duty

    for i in range(total_steps):
        duty += step
        print("Moving to... ", duty)
        # Clamp duty to not overshoot
        if (step > 0 and duty > target_duty) or (step < 0 and duty < target_duty):
            duty = target_duty

        GPIO.output(servo_pin, True)
        pwm.ChangeDutyCycle(duty)
        time.sleep(time_per_step)  # delay for servo movement (adjust if needed)
        if (overshootProtection):
            if (step > 0 and duty > target_duty):
                # move a little backwards to ensure we don't overshoot
                GPIO.output(servo_pin, True)
                pwm.ChangeDutyCycle(duty - 10) # 0.1 dutty ~= 1.8 degrees
                time.sleep(time_per_step)
            elif (step < 0 and duty < target_duty):
                # move a little backwards to ensure we don't overshoot
                GPIO.output(servo_pin, True)
                pwm.ChangeDutyCycle(duty + 10)
                time.sleep(time_per_step)
        GPIO.output(servo_pin, False)
        pwm.ChangeDutyCycle(0)

    # Final precise position
    GPIO.output(servo_pin, True)
    pwm.ChangeDutyCycle(target_duty)
    time.sleep(0.5)
    GPIO.output(servo_pin, False)
    pwm.ChangeDutyCycle(0)

    # Save new duty value to file
    with open(filepath, "w") as f:
        f.write(f"current_wheel_position={target_duty:.2f}\n")


def main():
    # Check for correct number of arguments
    if len(sys.argv) != 2:
        print("Usage: python3 servo_move.py <position 0-7>")
        sys.exit(1)

    try:
        position = int(sys.argv[1])
        if not 0 <= position <= 7:
            raise ValueError
    except ValueError:
        print("Invalid input: position must be an integer between 0 and 7.")
        sys.exit(1)

    # Convert position to angle
    angle = (position + 1) * 22.5  # 0 → 22.5°, 1 → 45°, ..., 7 → 180°

    SERVO_PIN = 14

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SERVO_PIN, GPIO.OUT)

    pwm = GPIO.PWM(SERVO_PIN, 50)  # 50 Hz (20 ms period)
    pwm.start(0)

    try:
        print("Spinning wheel...")
        set_angle(angle, SERVO_PIN, pwm)
    except KeyboardInterrupt:
        pass
    finally:
        pwm.stop()
        GPIO.cleanup()

if __name__=="__main__":
    main()
