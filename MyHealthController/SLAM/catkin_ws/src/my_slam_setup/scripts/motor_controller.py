#!/usr/bin/env python3
"""GPIO consumer with command and localization watchdogs, using wall time."""
import math
import threading
import time

import rospy
from geometry_msgs.msg import Twist
from gpiozero import PWMOutputDevice, DigitalOutputDevice
from std_msgs.msg import Bool
from myhealthkit_navigation.core import wheel_duties


class MotorController:
    def __init__(self):
        self.lock = threading.RLock()
        self.closed = False
        self.command = (0.0, 0.0)
        self.last_command = self.last_health = None
        self.healthy = False
        self.timeout = rospy.get_param('~cmd_timeout', 0.3)
        self.health_timeout = rospy.get_param('~health_timeout', 0.2)
        self.wheel_base = rospy.get_param('~wheel_base', 0.20)
        self.full_speed = rospy.get_param('~speed_at_full_duty', 0.5)
        self.max_linear = rospy.get_param('~max_linear', 0.15)
        self.max_angular = rospy.get_param('~max_angular', 0.4)
        self.pwm_frequency = rospy.get_param('~pwm_frequency', 100)
        if not all(math.isfinite(v) and v > 0 for v in (self.timeout, self.health_timeout,
                   self.max_linear, self.max_angular, self.pwm_frequency)):
            raise ValueError('Motor limits, timeouts and frequency must be positive')
        wheel_duties(0, 0, self.wheel_base, self.full_speed)
        self.signs = rospy.get_param('~motor_signs', [1, 1, 1, 1])
        if len(self.signs) != 4 or any(v not in (-1, 1) for v in self.signs):
            raise ValueError('motor_signs must contain four values in {-1, 1}')
        self.stby = DigitalOutputDevice(rospy.get_param('~stby_pin', 21), initial_value=False)
        self.devices = []
        try:
            pins = rospy.get_param('~motor_pins', [[18, 27], [24, 25], [22, 23], [5, 6]])
            if len(pins) != 4 or any(len(pair) != 2 for pair in pins):
                raise ValueError('motor_pins must have four IN1/IN2 pairs')
            for pair in pins:
                for pin in pair:
                    self.devices.append(PWMOutputDevice(pin, frequency=self.pwm_frequency, initial_value=0))
        except Exception:
            for device in self.devices:
                device.close()
            self.stby.close()
            raise
        rospy.on_shutdown(self.close)
        rospy.Subscriber('/cmd_vel', Twist, self.cmd, queue_size=1)
        rospy.Subscriber('/navigation/healthy', Bool, self.health, queue_size=1)

    def cmd(self, msg):
        with self.lock:
            values = (msg.linear.x, msg.angular.z)
            if not all(math.isfinite(v) for v in values):
                self.last_command = None
                self.stop()
                return
            self.command = (max(-self.max_linear, min(self.max_linear, values[0])),
                            max(-self.max_angular, min(self.max_angular, values[1])))
            self.last_command = time.monotonic()

    def health(self, msg):
        with self.lock:
            self.healthy = msg.data
            self.last_health = time.monotonic()
            if not self.healthy:
                self.last_command = None
                self.stop()

    def stop(self):
        if self.closed:
            return
        self.stby.off()
        for device in self.devices:
            device.value = 0

    def step(self):
        with self.lock:
            now = time.monotonic()
            if not self.healthy or self.last_health is None or now-self.last_health > self.health_timeout or self.last_command is None or now-self.last_command > self.timeout:
                self.stop()
                return
            left, right = wheel_duties(*self.command, self.wheel_base, self.full_speed)
            # Disable bridge during direction changes; never energize both IN pins.
            self.stby.off()
            for index, (speed, sign) in enumerate(zip((left, left, right, right), self.signs)):
                a, b = self.devices[2*index:2*index+2]
                a.value = b.value = 0
                speed *= sign
                a.value, b.value = max(speed, 0), max(-speed, 0)
            self.stby.on()

    def close(self):
        with self.lock:
            if not self.closed:
                self.stop()
                for device in self.devices:
                    device.close()
                self.stby.close()
                self.closed = True


if __name__ == '__main__':
    rospy.init_node('motor_controller')
    node = MotorController()
    try:
        # Wall time keeps the watchdog running even if ROS time stops.
        while not rospy.is_shutdown():
            node.step()
            time.sleep(0.02)
    finally:
        node.close()
