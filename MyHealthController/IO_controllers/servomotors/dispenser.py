#!/usr/bin/env python3
"""Serialize complete servo operations across HTTP workers and command-line tools."""
import argparse
import math
import os
from pathlib import Path
import tempfile
import time
from filelock import FileLock

SERVO_DIR = Path(__file__).resolve().parent
CONTROLLER_DIR = SERVO_DIR.parents[1]
_state = Path(os.getenv('MYHEALTHKIT_SERVO_STATE', str(SERVO_DIR / 'current_position.txt'))).expanduser()
STATE_PATH = _state if _state.is_absolute() else CONTROLLER_DIR / _state
LOCK_PATH = STATE_PATH.with_suffix('.lock')


def servo_lock():
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    return FileLock(str(LOCK_PATH), timeout=30)


def move_servo(pin, angle):
    if not math.isfinite(angle) or not 0 <= angle <= 180:
        raise ValueError('Servo angle must be between 0 and 180 degrees')
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT)
    pwm = None
    try:
        pwm = GPIO.PWM(pin, 50)
        pwm.start(0)
        pwm.ChangeDutyCycle(2 + angle / 18)
        time.sleep(0.8)
    finally:
        if pwm is not None:
            pwm.stop()
        # Never clean unrelated GPIO, especially the wheel motor controller.
        GPIO.cleanup(pin)


def save_position(angle):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=str(STATE_PATH.parent))
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write('current_wheel_position=%.2f\n' % (2 + angle / 18))
        os.replace(name, str(STATE_PATH))
    finally:
        if os.path.exists(name):
            os.unlink(name)


def rotate(angle):
    move_servo(14, angle)
    # Diagnostic last command only; absolute positioning needs no assumed old pose.
    save_position(angle)


def actuate(position, release=False):
    if type(position) is not int or not 0 <= position < 8:
        raise ValueError('Compartment must be between 0 and 7')
    with servo_lock():
        try:
            move_servo(15, 110.15)  # Ensure closed before rotating.
            rotate((position + 1) * 22.5)
            if release:
                move_servo(15, 170)
                time.sleep(2)
        finally:
            move_servo(15, 110.15)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('position', type=int)
    parser.add_argument('--release', action='store_true')
    args = parser.parse_args()
    actuate(args.position, args.release)


if __name__ == '__main__':
    main()
