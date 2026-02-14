import RPi.GPIO as GPIO
import time



# Set the GPIO mode (BOARD)
GPIO.setmode(GPIO.BCM)

# Define the GPIO pin controls the pump via the relay module
RELAY_PIN = 5

# Set the relay pin as an output pin
GPIO.setup(RELAY_PIN, GPIO.OUT)

try:
    # Run the loop function forever
    while True:
        # Turn the relay on to turn on the pump
        GPIO.output(RELAY_PIN, GPIO.HIGH)
        time.sleep(5)
        print("Turning on")
        
        # Turn the relay off to turn off the pump
        GPIO.output(RELAY_PIN, GPIO.LOW)
        time.sleep(5)
        print("Turning off")

except KeyboardInterrupt:
    #press Ctrl+C, clean up the config
    GPIO.cleanup()
