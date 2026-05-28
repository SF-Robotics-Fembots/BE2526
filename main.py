import time
import os
import glob as globmod
import shutil
import DepthEval
import ms5837
import smbus
import RPi.GPIO as GPIO
import datetime
import threading
import logging

# Archive existing buoy.log to next numbered file
if os.path.exists("buoy.log"):
    existing = globmod.glob("buoy_*.log")
    nums = [int(f.replace("buoy_", "").replace(".log", "")) for f in existing if f.replace("buoy_", "").replace(".log", "").isdigit()]
    next_num = max(nums) + 1 if nums else 1
    shutil.copy2("buoy.log", f"buoy_{next_num}.log")
    open("buoy.log", "w").close()

logging.basicConfig(
    filename="buoy.log",
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

print("Starting sensor")
sensor = ms5837.MS5837_02BA()
print("Sensor started")

DEBUG = 1

GPIO_IN = 5
GPIO_OUT = 6

# Set the GPIO mode (BOARD)
GPIO.setmode(GPIO.BCM)


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
	sensor.read(ms5837.OSR_8192)
#	print("prep to set density")
	sensor.setFluidDensity(ms5837.DENSITY_FRESHWATER)

def pump(direction):
    if direction == 1:  # Water In
        GPIO.output(GPIO_IN, GPIO.HIGH)
        GPIO.output(GPIO_OUT, GPIO.LOW)
        msg = (f"Water IN EXECUTION  ")
        print(msg)
        logging.info(msg)
    else:  # Water Out
        GPIO.output(GPIO_IN, GPIO.LOW)
        GPIO.output(GPIO_OUT, GPIO.HIGH)
        msg = (f"Water OUT EXECUTION  ")
        print(msg)
        logging.info(msg)

cycle=0.1 #seconds
TOP_OFFSET = -17.0    # cm added to average depth to define top
BOTTOM_OFFSET = 50.2  # cm added to average depth to define bottom

time.sleep(2)

startup()

speed_divisor = float(input("Enter speed divisor (e.g. 1 for normal, 2 for half speed): "))
shallow_threshold = float(input("Enter shallow threshold in cm (e.g. 20): "))
max_shallow_speed = float(input("Enter max shallow sink speed in cm/s (e.g. 0.1): "))
target_depth = float(input("Enter target depth in cm for the bottom: "))
hold_duration = float(input("Enter hold duration at target depth in seconds (e.g. 30): "))
target_depth_2 = float(input("Enter second target depth in cm for the bottom: "))
sensor.read(ms5837.OSR_8192)
starting_sensor_depth = sensor.depth() * 100 # convert to cm 


previous_depth = 0
top = 0
bottom = 0
phase = "sinking"
hold_start_time = None
hold_tolerance = 5.0  # cm — considered "at target" if within this range

table = DepthEval.load_speed_table("speeds.csv")
table = [(offset, speed / speed_divisor) for offset, speed in table]
print(f"Loaded {len(table)} entries.")

def get_depth_reading():
    global sensor, starting_sensor_depth, top, bottom
    attempts = 0
    while attempts < 3:
        readings = []
        for _ in range(3):
            try:
                sensor.read(ms5837.OSR_8192)
                current_depth = sensor.depth() * 100 - starting_sensor_depth  # convert to cm and adjust
                readings.append(current_depth)
            except Exception:
                print("                 ***FAILED READING***")

        if len(readings) >= 2:  # Check if we have at least two good readings
            # Calculate the mean, excluding outliers
            filtered_readings = [depth for depth in readings if depth <= 400 and depth >= -10]
            if len(filtered_readings) >= 2:  # Check if we have at least two good readings after filtering
                avg = sum(filtered_readings) / len(filtered_readings)
                top = avg + TOP_OFFSET
                bottom = avg + BOTTOM_OFFSET
                return avg

        attempts += 1
    print("                 ***FAILED THREE READINGS***")
    return 0


def get_pump_action(depth_offset, speed_offset):
    if depth_offset > 0:  # too deep, need to rise
        print("Depth too low")
        if speed_offset > 0:  # rising too slow
            print("Speed too slow")
            print("Water out")
            return 2  # Water out
        else:  # rising too fast
            print("Speed too fast")
            print("Water in")
            return 1  # Water In
    else:  # too high (too shallow, need to sink)
        print("Depth too high")
        if speed_offset > 0:  # sinking too fast
            print("Speed too fast")
            print("Water out")
            return 2  # Water out
        else:  # sinking too slow
            print("Speed too slow")
            print("Water in")
            return 1  # Water in

def run_phase(current_depth, actual_speed, depth_offset):
    global phase, hold_start_time

    target_speed = DepthEval.get_speed(table, depth_offset)

    if current_depth < shallow_threshold and target_speed > 0:
        target_speed = min(target_speed, max_shallow_speed)

    speed_offset = actual_speed - target_speed

    # Transition: sinking -> holding
    if phase == "sinking" and abs(depth_offset) <= hold_tolerance:
        phase = "holding"
        hold_start_time = time.time()
        msg = f"Reached target depth {target_depth:.2f}cm. Holding for {hold_duration:.0f}s."
        print(msg)
        logging.info(msg)

    action = get_pump_action(depth_offset, speed_offset)

    msg = (f"[{phase.upper()}] depth={current_depth:.2f}cm  speed={actual_speed:.3f}cm/s  "
           f"depth offset={depth_offset:.2f}cm speed_offset={speed_offset} action={'WaterIn' if action==1 else 'WaterOut'}")
    print(msg)
    logging.info(msg)
    pump(action)
    return False


try:
    while True:
        print("Starting Main Loop")
        current_depth = get_depth_reading()

        # calculate speed
        actual_speed = (current_depth - previous_depth) / cycle  # positive when sinking

        # calculate offset
#        depth_offset = current_depth - target_depth  # negative means too high, positive means too low
        depth_offset = bottom - target_depth  # negative means too high, positive means too low

#        if run_phase(current_depth, actual_speed, depth_offset):
        if run_phase(bottom, actual_speed, depth_offset):
            break

        previous_depth = current_depth

        time.sleep(cycle)


except KeyboardInterrupt:
    #press Ctrl+C, clean up the config
    GPIO.cleanup()
