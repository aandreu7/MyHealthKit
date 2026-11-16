#!/usr/bin/env python3
import argparse
from dispenser import rotate, servo_lock, move_servo

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('angle', type=float)
    args = parser.parse_args()
    with servo_lock():
        try:
            move_servo(15, 110.15)
            rotate(args.angle)
        finally:
            move_servo(15, 110.15)
