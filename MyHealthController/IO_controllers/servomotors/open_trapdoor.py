#!/usr/bin/env python3
import argparse
from dispenser import move_servo, servo_lock

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('control', type=int, choices=[0, 1])
    args = parser.parse_args()
    with servo_lock():
        move_servo(15, 170 if args.control else 110.15)
