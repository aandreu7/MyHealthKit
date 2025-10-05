#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time
import getch

# Pines BCM
STBY1 = 17
STBY2 = 26
PWM_FR = 24
PWM_FL = 23
PWM_BL = 5
PWM_BR = 6
AIN1_B = 25
AIN2_B = 16
BIN1_B = 21
BIN2_B = 20

FREQ = 500

def setup_motors():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup([STBY1, STBY2, PWM_FR, PWM_FL, PWM_BR, PWM_BL,
                AIN1_B, AIN2_B, BIN1_B, BIN2_B], GPIO.OUT)

    pwm_FR = GPIO.PWM(PWM_FR, FREQ)
    pwm_FL = GPIO.PWM(PWM_FL, FREQ)
    pwm_BR = GPIO.PWM(PWM_BR, FREQ)
    pwm_BL = GPIO.PWM(PWM_BL, FREQ)

    pwm_FR.start(0)
    pwm_FL.start(0)
    pwm_BR.start(0)
    pwm_BL.start(0)

    GPIO.output(STBY1, GPIO.HIGH)
    GPIO.output(STBY2, GPIO.HIGH)

    # Dirección por defecto: adelante
    GPIO.output(AIN1_B, GPIO.LOW)
    GPIO.output(AIN2_B, GPIO.HIGH)
    GPIO.output(BIN1_B, GPIO.HIGH)
    GPIO.output(BIN2_B, GPIO.LOW)

    return pwm_FR, pwm_FL, pwm_BR, pwm_BL

def stop_motors(pwms):
    for pwm in pwms:
        pwm.ChangeDutyCycle(0)

def set_forward_direction():
    GPIO.output(AIN1_B, GPIO.LOW)
    GPIO.output(AIN2_B, GPIO.HIGH)
    GPIO.output(BIN1_B, GPIO.HIGH)
    GPIO.output(BIN2_B, GPIO.LOW)

def set_reverse_turn_direction():
    GPIO.output(AIN1_B, GPIO.HIGH)
    GPIO.output(AIN2_B, GPIO.LOW)
    GPIO.output(BIN1_B, GPIO.LOW)
    GPIO.output(BIN2_B, GPIO.HIGH)

def main():
    pwm_FR, pwm_FL, pwm_BR, pwm_BL = setup_motors()
    pwms = [pwm_FR, pwm_FL, pwm_BR, pwm_BL]

    print("Control WASD:")
    print("W = Adelante | A/D = Gira avanzando | S = Lento | X = Gira marcha atrás")
    print("ESPACIO = FRENAR | Q = Salir")

    try:
        while True:
            key = getch.getch().lower()

            if key == 'w':
                print("Adelante recto")
                set_forward_direction()
                pwm_FR.ChangeDutyCycle(100)
                pwm_FL.ChangeDutyCycle(100)
                pwm_BR.ChangeDutyCycle(100)
                pwm_BL.ChangeDutyCycle(100)

            elif key == 'a':
                print("Gira izquierda")
                set_forward_direction()
                pwm_FR.ChangeDutyCycle(100)
                pwm_FL.ChangeDutyCycle(30)
                pwm_BR.ChangeDutyCycle(100)
                pwm_BL.ChangeDutyCycle(30)

            elif key == 'd':
                print("Gira derecha")
                set_forward_direction()
                pwm_FR.ChangeDutyCycle(30)
                pwm_FL.ChangeDutyCycle(100)
                pwm_BR.ChangeDutyCycle(30)
                pwm_BL.ChangeDutyCycle(100)

            elif key == 's':
                print("Más lento recto")
                set_forward_direction()
                pwm_FR.ChangeDutyCycle(50)
                pwm_FL.ChangeDutyCycle(50)
                pwm_BR.ChangeDutyCycle(50)
                pwm_BL.ChangeDutyCycle(50)

            elif key == 'x':
                print("🔁 Gira marcha atrás (mantener pulsado)")
                set_reverse_turn_direction()
                pwm_FR.ChangeDutyCycle(100)
                pwm_FL.ChangeDutyCycle(100)
                pwm_BR.ChangeDutyCycle(100)
                pwm_BL.ChangeDutyCycle(100)

            elif key == ' ':
                print("🚨 FRENADO")
                stop_motors(pwms)

            elif key == 'q':
                print("Saliendo...")
                stop_motors(pwms)
                break

            else:
                print("Tecla no válida. Usa W/A/S/D/X/ESPACIO/Q")
                stop_motors(pwms)

    finally:
        stop_motors(pwms)
        for pwm in pwms:
            pwm.stop()
        GPIO.output(STBY1, GPIO.LOW)
        GPIO.output(STBY2, GPIO.LOW)
        GPIO.cleanup()
        print("GPIO limpiados. Programa finalizado.")

if __name__ == "__main__":
    main()
