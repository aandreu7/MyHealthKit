import RPi.GPIO as GPIO
import time

# Pines que estamos usando
STBY = 17    # STBY del driver
PWMA = 23    # PWM del Motor A
PWMB = 24    # PWM del Motor B

# Configuración
GPIO.setmode(GPIO.BCM)
GPIO.setup(STBY, GPIO.OUT)
GPIO.setup(PWMA, GPIO.OUT)
GPIO.setup(PWMB, GPIO.OUT)

# Configuramos PWM a 500 Hz
pwm_a = GPIO.PWM(PWMA, 500)
pwm_b = GPIO.PWM(PWMB, 500)
pwm_a.start(50)  # 50% duty cycle
pwm_b.start(50)  # 50% duty cycle

# Activar el driver
GPIO.output(STBY, GPIO.HIGH)

try:
    print("Los motores deberían girar ahora...")
    time.sleep(10)  # Mantener girando 10 segundos
finally:
    pwm_a.stop()
    pwm_b.stop()
    GPIO.cleanup()
    print("Motores parados y GPIO limpiados")
