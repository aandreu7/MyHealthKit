#!/usr/bin/env python3
import argparse
from dispenser import actuate

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('position', type=int)
    args = parser.parse_args()
    actuate(args.position, release=False)
