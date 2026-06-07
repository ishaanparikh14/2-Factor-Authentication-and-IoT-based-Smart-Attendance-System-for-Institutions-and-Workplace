import RPi.GPIO as GPIO
import time

# Pin definitions
IR_PIN = 17
GREEN_LED = 23
RED_LED = 24

GPIO.setmode(GPIO.BCM)

GPIO.setup(IR_PIN, GPIO.IN)

GPIO.setup(GREEN_LED, GPIO.OUT)
GPIO.setup(RED_LED, GPIO.OUT)

# Initial state
GPIO.output(GREEN_LED, GPIO.LOW)
GPIO.output(RED_LED, GPIO.HIGH)

print("IR Sensor + LED Test Started")
print("Place your hand in front of the IR sensor")
print("Press CTRL+C to exit\n")

try:
    while True:

        if GPIO.input(IR_PIN):

            print("NO OBJECT DETECTED")

            GPIO.output(GREEN_LED, GPIO.HIGH)
            GPIO.output(RED_LED, GPIO.LOW)

        else:

            print(" OBJECT DETECTED")

            GPIO.output(GREEN_LED, GPIO.LOW)
            GPIO.output(RED_LED, GPIO.HIGH)

        time.sleep(0.2)

except KeyboardInterrupt:

    print("\nStopping Test")

finally:

    GPIO.output(GREEN_LED, GPIO.LOW)
    GPIO.output(RED_LED, GPIO.LOW)

    GPIO.cleanup()
