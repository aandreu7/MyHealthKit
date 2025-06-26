#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time
import os

SERVO_PIN = 14
FREQ_HZ = 50
FILEPATH = "current_position.txt"

def angle_to_duty(angle):
    return 2 + (angle / 18)  # Para 0° → 2%, 180° → ~12%

def read_last_duty():
    if os.path.exists(FILEPATH):
        with open(FILEPATH, "r") as f:
            line = f.readline().strip()
            try:
                return float(line.split('=')[1])
            except (IndexError, ValueError):
                print("Archivo mal formado, se usará posición por defecto (0°)")
    else:
        print("Archivo no encontrado, se usará posición por defecto (0°)")
    return angle_to_duty(0)  # Por defecto

def save_duty(duty):
    with open(FILEPATH, "w") as f:
        f.write(f"current_wheel_position={duty:.2f}\n")

def move_to_angle(angle, pwm):
    target_duty = angle_to_duty(angle)
    print(f"Moviendo a {angle}° → duty {target_duty:.2f}")

    pwm.ChangeDutyCycle(target_duty)
    time.sleep(0.5)
    pwm.ChangeDutyCycle(0)
    save_duty(target_duty)

def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SERVO_PIN, GPIO.OUT)
    pwm = GPIO.PWM(SERVO_PIN, FREQ_HZ)
    pwm.start(0)

    try:
        current_duty = read_last_duty()
        current_angle = (current_duty - 2) * 18  # inverso de angle_to_duty

        print(f"Ángulo actual estimado: {current_angle:.2f}°")

        # 1. Mover al ángulo mínimo
        move_to_angle(22.5, pwm)
        time.sleep(1)

        # 2. Mover al ángulo máximo
        move_to_angle(180.0, pwm)
        time.sleep(1)

    except KeyboardInterrupt:
        print("Interrumpido por el usuario.")
    finally:
        pwm.stop()
        GPIO.cleanup()
        print("GPIO limpio. Fin del programa.")

if __name__ == "__main__":
    main()
