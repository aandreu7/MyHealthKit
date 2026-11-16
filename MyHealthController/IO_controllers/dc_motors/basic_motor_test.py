import RPi.GPIO as GPIO
import time

# BCM GPIO assignments.
STBY = 17    # Driver standby
PWMA = 23    # Motor A PWM
PWMB = 24    # Motor B PWM

GPIO.setmode(GPIO.BCM)
GPIO.setup(STBY, GPIO.OUT)
GPIO.setup(PWMA, GPIO.OUT)
GPIO.setup(PWMB, GPIO.OUT)

pwm_a = GPIO.PWM(PWMA, 500)
pwm_b = GPIO.PWM(PWMB, 500)
pwm_a.start(50)  # 50% duty cycle
pwm_b.start(50)  # 50% duty cycle

GPIO.output(STBY, GPIO.HIGH)

try:
    print("The motors should now be running...")
    time.sleep(10)  # Mantener girando 10 segundos
finally:
    pwm_a.stop()
    pwm_b.stop()
    GPIO.cleanup()
    print("Motors stopped and GPIO resources released")
