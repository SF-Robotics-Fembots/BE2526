import RPi.GPIO as GPIO
import time

# GPIO setup

# Define pump control pins
PUMP_IN_PIN = 17   # GPIO pin to pump fluid into the chamber
PUMP_OUT_PIN = 27  # GPIO pin to pump fluid out of the chamber

GPIO.setup(PUMP_IN_PIN, GPIO.OUT)
GPIO.setup(PUMP_OUT_PIN, GPIO.OUT)

# Duration to run pump for each action (in seconds)
PUMP_DURATION = 2.0

def pump_in():
    print("Pumping fluid in...")
    GPIO.output(PUMP_OUT_PIN, GPIO.LOW)  # Ensure out pump is off
    GPIO.output(PUMP_IN_PIN, GPIO.HIGH)
    time.sleep(PUMP_DURATION)
    GPIO.output(PUMP_IN_PIN, GPIO.LOW)

def pump_out():
    print("Pumping fluid out...")
    GPIO.output(PUMP_IN_PIN, GPIO.LOW)  # Ensure in pump is off
    GPIO.output(PUMP_OUT_PIN, GPIO.HIGH)
    time.sleep(PUMP_DURATION)
    GPIO.output(PUMP_OUT_PIN, GPIO.LOW)

def buoyancy_control(depth_target):
    # Placeholder logic for depth control
    current_depth = 0  # Replace with actual sensor reading
    if depth_target > current_depth:
        pump_in()
    elif depth_target < current_depth:
        pump_out()
    else:
        print("Depth is stable.")

try:
    while True:
        # Example loop: alternate pumping in and out
        buoyancy_control(depth_target=1)
        time.sleep(5)
        buoyancy_control(depth_target=-1)
        time.sleep(5)

except KeyboardInterrupt:
    print("Exiting...")
    GPIO.cleanup()