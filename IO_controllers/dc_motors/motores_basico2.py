#!/usr/bin/env python3
from gpiozero import PWMOutputDevice, DigitalOutputDevice
from time import sleep

# Pines BCM
STBY   = DigitalOutputDevice(17)  # STBY a GPIO17
motorA = PWMOutputDevice(23)      # PWMA a GPIO23
motorB = PWMOutputDevice(24)      # PWMB a GPIO24

try:
    # Habilita el driver
    STBY.on()
    sleep(0.1)

    print("Motores al 60% durante 5 s…")
    motorA.value = 0.6
    motorB.value = 0.6
    sleep(5)

    print("Motores al 30% durante 5 s…")
    motorA.value = 0.3
    motorB.value = 0.3
    sleep(5)

    print("Deteniendo motores…")
    motorA.value = 0
    motorB.value = 0
    sleep(1)

finally:
    motorA.close()
    motorB.close()
    STBY.close()
    print("GPIO limpiados, fin del script.")
