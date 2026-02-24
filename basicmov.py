import RPi.GPIO as GPIO
import time



# Set the GPIO mode (BOARD)
GPIO.setmode(GPIO.BCM)

# Define the GPIO pin controls the pump via the relay module
RELAY_PIN = 5
RELAY_PIN2 = 6
# Set the relay pin as an output pin
GPIO.setup(RELAY_PIN, GPIO.OUT)

try:
    # Run the loop function forever
    GPIO.output(RELAY_PIN2, GPIO.LOW)
    while True:
        # Turn the relay on to turn on the pump
        print("Turning on")
        GPIO.output(RELAY_PIN, GPIO.HIGH)
        time.sleep(5)
        
        
        # Turn the relay off to turn off the pump
        print("Turning off")
        GPIO.output(RELAY_PIN, GPIO.LOW)
        time.sleep(5)
        

except KeyboardInterrupt:
    #press Ctrl+C, clean up the config
    GPIO.cleanup()
