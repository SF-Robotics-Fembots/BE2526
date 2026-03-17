import time
import DepthEval
import ms5837
import smbus
import RPi.GPIO as GPIO
import datetime
import threading

sensor = ms5837.MS5837_02BA()
DEBUG = 1

GPIO_IN = 5
GPIO_OUT = 6
# Set the relay pin as an output pin
GPIO.setup(GPIO_IN, GPIO.OUT)
GPIO.setup(GPIO_OUT, GPIO.OUT)
GPIO.output(GPIO_IN, GPIO.LOW)
GPIO.output(GPIO_OUT, GPIO.LOW)

def startup():
#	print("prep to init")
	sensor.init()
	time.sleep(1)
#	print("prep to read")
	sensor.read(ms5837.OSR_256)
#	print("prep to set density")
	sensor.setFluidDensity(ms5837.DENSITY_FRESHWATER)

def pump(direction):
    if direction == 1:  # Water In
        GPIO.output(GPIO_IN, GPIO.HIGH)
        GPIO.output(GPIO_OUT, GPIO.LOW)
    else:  # Water Out
        GPIO.output(GPIO_IN, GPIO.LOW)
        GPIO.output(GPIO_OUT, GPIO.HIGH)

cycle=0.2 #seconds

time.sleep(2)


target_depth = float(input("Enter target depth in cm: "))
previous_depth = 0

table = DepthEval.load_speed_table("speeds.csv")
print(f"Loaded {len(table)} entries.")
startup()

while True:
    print("Starting Main Loop")
    #current_depth = float(input("Enter current depth in cm: ")) #should be updated automatically == will be MS5837 read
    try:
        sensor.read(ms5837.OSR_256)
        current_depth = sensor.depth() * 100 # convert to cm
    except:
        print("                 ***FAILED READING***")
        continue


    # calculate speed
    actual_speed = (previous_depth - current_depth)/cycle # cm/s

    # calculate offset
    depth_offset = target_depth - current_depth # positive means too high, negative means too low

    # check DepthCSV logic
    target_speed = DepthEval.get_speed(table, depth_offset)
    speed_offset = target_speed - actual_speed

    if depth_offset > 0:  # too high
        if speed_offset > 0:  # too slow
            action = 1  # Water In
        else:  # too fast
            action = 2  # Water Out
    else:  # too low
        if speed_offset > 0:  # too slow
            action = 2  # Water Out
        else:  # too fast
            action = 1  # Water In

    # Print logs to screen
    print("Current Depth:", current_depth)
    print("Actual Speed:", actual_speed, "cm/s")
    print("Depth Offset:", depth_offset)
    print("Action:", action)


    # TURN ON PUMP HERE BASED ON ACTION
    pump(action)


    previous_depth = current_depth

    time.sleep(cycle)
