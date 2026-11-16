#!/usr/bin/env python3
"""Manual test using the same GPIO lock and absolute state path as the server."""
from dispenser import actuate

if __name__ == '__main__':
    actuate(0)
    actuate(7)
