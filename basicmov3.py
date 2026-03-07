import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

# Define pins
PIN5 = 5
PIN6 = 6

GPIO.setup(PIN5, GPIO.OUT)
GPIO.setup(PIN6, GPIO.OUT)

def get_level(pin_name):
    while True:
        val = input(f"Set {pin_name} HIGH or LOW? ").strip().lower()
        if val in ["high", "h", "1"]:
            return GPIO.HIGH
        elif val in ["low", "l", "0"]:
            return GPIO.LOW
        else:
            print("Invalid input. Type HIGH or LOW.")

try:
    # Ask user for desired states
    level5 = get_level("GPIO 5")
    level6 = get_level("GPIO 6")

    # Apply states
    GPIO.output(PIN5, level5)
    GPIO.output(PIN6, level6)

    print(f"GPIO 5 set to {'HIGH' if level5 == GPIO.HIGH else 'LOW'}")
    print(f"GPIO 6 set to {'HIGH' if level6 == GPIO.HIGH else 'LOW'}")

    # Keep pins in that state until user exits
    input("Press Enter to exit and clean up...")

finally:
    GPIO.cleanup()
    print("GPIO cleaned up.")