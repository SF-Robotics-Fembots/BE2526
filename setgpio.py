import RPi.GPIO as GPIO
import time

# Set the GPIO mode (BOARD)
GPIO.setmode(GPIO.BCM)


try:
    # Run the loop function forever
    while True:
      pin = int(input("Enter GPIO number"))
      state = int(input("1 for High, 0 for Low"))

      # Set the relay pin as an output pin
      GPIO.setup(pin, GPIO.OUT)

      # Turn the relay off to turn off the pump
      GPIO.output(pin, state)
        

except KeyboardInterrupt:
    #press Ctrl+C, clean up the config
    GPIO.cleanup()
