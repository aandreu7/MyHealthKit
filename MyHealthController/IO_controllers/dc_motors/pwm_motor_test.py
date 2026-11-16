#!/usr/bin/env python3
from gpiozero import PWMOutputDevice, DigitalOutputDevice
from time import sleep

# BCM GPIO assignments.
STBY   = DigitalOutputDevice(17)  # Standby: GPIO17
motorA = PWMOutputDevice(23)      # Channel A PWM: GPIO23
motorB = PWMOutputDevice(24)      # Channel B PWM: GPIO24

try:
    STBY.on()
    sleep(0.1)

    print("Running motors at 60% for 5 seconds...")
    motorA.value = 0.6
    motorB.value = 0.6
    sleep(5)

    print("Running motors at 30% for 5 seconds...")
    motorA.value = 0.3
    motorB.value = 0.3
    sleep(5)

    print("Stopping motors...")
    motorA.value = 0
    motorB.value = 0
    sleep(1)

finally:
    motorA.close()
    motorB.close()
    STBY.close()
    print("GPIO resources released; script finished.")
