#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time

# BCM Pines
STBY1 = 17
STBY2 = 26
PWM_FR = 24
#FR JA ESTÀ BÉ
PWM_FL = 23
PWM_BL = 5
PWM_BR = 6
AIN1_B = 25
AIN2_B = 16
BIN1_B = 21
BIN2_B = 20

# PWM Frequency (software PWM)
FREQ = 500  # Hz

def main():
    GPIO.setmode(GPIO.BCM)
    # Configures ports
    GPIO.setup(STBY1, GPIO.OUT)
    GPIO.setup(STBY2, GPIO.OUT)
    GPIO.setup(PWM_FR, GPIO.OUT)
    GPIO.setup(PWM_FL, GPIO.OUT)
    GPIO.setup(PWM_BR, GPIO.OUT)
    GPIO.setup(PWM_BL, GPIO.OUT)

    GPIO.setup(AIN1_B, GPIO.OUT)
    GPIO.setup(AIN2_B, GPIO.OUT)
    GPIO.setup(BIN1_B, GPIO.OUT)
    GPIO.setup(BIN2_B, GPIO.OUT)

    pwm_Front_Right = GPIO.PWM(PWM_FR, FREQ)
    pwm_Front_Left = GPIO.PWM(PWM_FL, FREQ)
    pwm_Back_Right = GPIO.PWM(PWM_BR, FREQ)
    pwm_Back_Left = GPIO.PWM(PWM_BL, FREQ)

    # Inicializamos PWM en 0%
    pwm_Front_Right.start(0)
    pwm_Front_Left.start(0)
    pwm_Back_Right.start(0)
    pwm_Back_Left.start(0)

    # Take out of standby
    GPIO.output(STBY1, GPIO.HIGH)
    GPIO.output(STBY2, GPIO.HIGH)

    # Set direction: forward
    GPIO.output(AIN1_B, GPIO.LOW)
    GPIO.output(AIN2_B, GPIO.HIGH)
    GPIO.output(BIN1_B, GPIO.HIGH)
    GPIO.output(BIN2_B, GPIO.LOW)

    time.sleep(0.1)

    try:
        print("Going Straight")
        pwm_Front_Right.ChangeDutyCycle(100)
        pwm_Front_Left.ChangeDutyCycle(95)
        pwm_Back_Right.ChangeDutyCycle(100)
        pwm_Back_Left.ChangeDutyCycle(95)
        time.sleep(10)

        print("Tourning left")
        pwm_Front_Right.ChangeDutyCycle(92)
        pwm_Front_Left.ChangeDutyCycle(30)
        pwm_Back_Right.ChangeDutyCycle(92)
        pwm_Back_Left.ChangeDutyCycle(32)
        time.sleep(10)

        print("Going straight")
        pwm_Front_Right.ChangeDutyCycle(92)
        pwm_Front_Left.ChangeDutyCycle(100)
        pwm_Back_Right.ChangeDutyCycle(92)
        pwm_Back_Left.ChangeDutyCycle(100)
        time.sleep(7)

        print("Tourning right")
        pwm_Front_Right.ChangeDutyCycle(100)
        pwm_Front_Left.ChangeDutyCycle(95)
        pwm_Back_Right.ChangeDutyCycle(100)
        pwm_Back_Left.ChangeDutyCycle(95)
        time.sleep(10)

        # Stop
        print("Stopping motors")
        pwm_Front_Right.ChangeDutyCycle(0)
        pwm_Front_Left.ChangeDutyCycle(0)
        pwm_Back_Right.ChangeDutyCycle(0)
        pwm_Back_Left.ChangeDutyCycle(0)
        time.sleep(1)

    finally:
        pwm_Front_Right.stop()
        pwm_Front_Left.stop()
        pwm_Back_Right.stop()
        pwm_Back_Left.stop()
        GPIO.output(PWM_BR, GPIO.LOW)
        GPIO.output(PWM_BL, GPIO.LOW)
        GPIO.output(AIN1_B, GPIO.LOW)
        GPIO.output(AIN2_B, GPIO.LOW)
        GPIO.output(BIN1_B, GPIO.LOW)
        GPIO.output(BIN2_B, GPIO.LOW)
        GPIO.output(STBY2, GPIO.LOW)
        GPIO.cleanup()
        print("GPIO limpiados, fin del script.")

if __name__ == "__main__":
    main()
