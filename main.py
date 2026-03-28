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

cycle=0.2 #seconds

time.sleep(2)

speed_divisor = float(input("Enter speed divisor (e.g. 1 for normal, 2 for half speed): "))
shallow_threshold = float(input("Enter shallow threshold in cm (e.g. 20): "))
max_shallow_speed = float(input("Enter max shallow sink speed in cm/s (e.g. 0.1): "))
target_depth = float(input("Enter first target depth in cm: "))
target_depth2 = float(input("Enter second target depth in cm: "))
hold_duration = 40  # seconds to hold at target_depth before switching
sensor.read(ms5837.OSR_8192)
starting_sensor_depth = sensor.depth() * 100 # convert to cm 


previous_depth = 0

table = DepthEval.load_speed_table("speeds.csv")
table = [(offset, speed / speed_divisor) for offset, speed in table]
print(f"Loaded {len(table)} entries.")
at_depth1 = False         # whether we've reached target_depth for the first time
depth1_hold_start = None  # timestamp when we first hit target_depth
switched_to_depth2 = False
startup()


try:
    while True:
        print("Starting Main Loop")
        #current_depth = float(input("Enter current depth in cm: ")) #should be updated automatically == will be MS5837 read
        try:
            sensor.read(ms5837.OSR_8192)
            current_depth = sensor.depth() * 100 - starting_sensor_depth# convert to cm and adjust for the depth of the sensor on the robot
        except:
            print("                 ***FAILED READING***")
            continue


        # calculate speed
        actual_speed = (current_depth - previous_depth) / cycle  # positive when sinking

        # calculate offset
        depth_offset = current_depth - target_depth # negative means too high, positive means too low
        depth_offset2 = current_depth - target_depth2

        # check DepthCSV logic
        #target_speed = DepthEval.get_speed(table, depth_offset)

       # --- Depth 1 hold timer and switch to depth 2 ---
    if not switched_to_depth2:
        # Consider "at depth" when within 5 cm of target
        if abs(depth_offset) <= 5:
            if depth1_hold_start is None:
                depth1_hold_start = time.time()
                msg = "Reached target depth 1 - hold timer started"
                print(msg)
                logging.info(msg)
            elif time.time() - depth1_hold_start >= hold_duration:
                switched_to_depth2 = True
                msg = f"Hold complete - switching to target depth 2 ({target_depth2} cm)"
                print(msg)
                logging.info(msg)
        else:
            # Drifted out of range, reset the timer
            if depth1_hold_start is not None:
                depth1_hold_start = None
                msg = "Drifted from depth 1 - hold timer reset"
                print(msg)
                logging.info(msg)

    # Use the active target depth for control
    active_offset = depth_offset2 if switched_to_depth2 else depth_offset
    target_speed = DepthEval.get_speed(table, active_offset)

    # Near the surface, cap sink speed to ease through the waterline
    if current_depth < shallow_threshold and target_speed > 0:
        target_speed = min(target_speed, max_shallow_speed)

    speed_offset = actual_speed - target_speed

    if depth_offset > 0:  # too deep, need to rise
        print("Depth too low")
        if speed_offset > 0:  # rising too slow
            print("Speed too slow")
            print("Water out")
            action = 2  # Water out
        else:  # rising too fast
            print("Speed too fast")
            print("Water in")
            action = 1  # Water In
    else:  # too high (too shallow, need to sink)
        print("Depth too high")
        if speed_offset > 0:  # sinking too fast
            print("Speed too fast")
            print("Water out")
            action = 2  # Water out
        else:  # sinking too slow
            print("Speed too slow")
            print("Water in")
            action = 1  # Water in

    # Print logs to screen and file
    #msg = (f"depth={current_depth:.2f}cm  speed={actual_speed:.3f}cm/s  "
            #f"depth offset={depth_offset:.2f}cm speed_offset={speed_offset} action={'WaterIn' if action==1 else 'WaterOut'}")
    
    phase = "PHASE2" if switched_to_depth2 else "PHASE1"
    msg = (f"[{phase}] depth={current_depth:.2f}cm speed={actual_speed:.3f}cm/s "
        f"depth offset={active_offset:.2f}cm speed_offset={speed_offset:.3f} action={'WaterIn' if action==1 else 'WaterOut'}")
    
    print(msg)
    logging.info(msg)


    # TURN ON PUMP HERE BASED ON ACTION
    pump(action)


    previous_depth = current_depth

    time.sleep(cycle)


except KeyboardInterrupt:
    #press Ctrl+C, clean up the config
    GPIO.cleanup()
