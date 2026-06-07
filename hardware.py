import RPi.GPIO as GPIO
import time

IR = 17
BUZZER = 18
GREEN = 23
RED = 24

GPIO.setmode(GPIO.BCM)

GPIO.setup(IR, GPIO.IN)
GPIO.setup(BUZZER, GPIO.OUT)
GPIO.setup(GREEN, GPIO.OUT)
GPIO.setup(RED, GPIO.OUT)

def person_detected():
    return GPIO.input(IR) == 0

def green_on():
    GPIO.output(GREEN, 1)
    GPIO.output(RED, 0)

def red_on():
    GPIO.output(RED, 1)
    GPIO.output(GREEN, 0)

def all_off():
    GPIO.output(GREEN, 0)
    GPIO.output(RED, 0)

def success_beep():
    GPIO.output(BUZZER, 1)
    time.sleep(0.2)
    GPIO.output(BUZZER, 0)

def error_beep():
    for _ in range(3):
        GPIO.output(BUZZER, 1)
        time.sleep(0.15)
        GPIO.output(BUZZER, 0)
        time.sleep(0.15)
