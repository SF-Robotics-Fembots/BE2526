import RPi.GPIO as GPIO
import time

# Set the GPIO mode (BOARD)
GPIO.setmode(GPIO.BCM)

# Define the GPIO pin controls the pump via the relay module
RELAY_PIN = 5
RELAY_PIN2 = 6
# Set the relay pin as an output pin
GPIO.setup(RELAY_PIN2, GPIO.OUT)
GPIO.setup(RELAY_PIN, GPIO.OUT)

try:
    # Run the loop function forever
    GPIO.output(RELAY_PIN2, GPIO.LOW)
    GPIO.output(RELAY_PIN, GPIO.LOW)
    while True:

        # Turn the relay off to turn off the pump
        print("Pumping IN")
        GPIO.output(RELAY_PIN, GPIO.LOW)
        GPIO.output(RELAY_PIN2, GPIO.HIGH)
        time.sleep(60)



        # Turn the relay on to turn on the pump
        print("Pumping OUT")
        GPIO.output(RELAY_PIN, GPIO.HIGH)
        GPIO.output(RELAY_PIN2, GPIO.LOW)
        time.sleep(60)
        
        
        

except KeyboardInterrupt:
    #press Ctrl+C, clean up the config
    GPIO.cleanup()
