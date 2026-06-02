import time
import os
import cgi
import cgitb
import configparser
import glob as globmod
import shutil
import DepthEval
import ms5837
import smbus
import RPi.GPIO as GPIO
import threading
import logging

cgitb.enable()

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

sensor = ms5837.MS5837_02BA()

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
ENGINE_HEIGHT = 50.0  # cm — difference between the baseline and the bottom
TOP_OFFSET = -17.0  # cm — top of engine is 17cm above baseline
DEPTH_WINDOW = 33.0       # cm — allowed deviation from target depth
REQUIRED_CONSECUTIVE = 7  # consecutive 5s readings needed within window

speed_divisor = 1.0
shallow_threshold = 0.0
max_shallow_speed = 0.0
target_depth = 0.0
target_depth_1 = 0.0
target_depth_2 = 0.0
hold_duration = 0.0
starting_sensor_depth = 0.0
leg = 1
current_depth = 0.0
top = 0
phase = "sinking"
hold_start_time = None
hold_tolerance = 5.0  # cm — considered "at target" if within this range

table = []
mission_complete = threading.Event()
consecutive_in_window = 0

def initialize_dive():
    global speed_divisor, shallow_threshold, max_shallow_speed
    global target_depth, target_depth_1, target_depth_2, hold_duration
    global starting_sensor_depth, leg, table

    time.sleep(2)
    startup()

    config = configparser.ConfigParser()
    config.read("config.ini")
    cfg = config["buoyancy"]
    speed_divisor     = float(cfg["speed_divisor"])
    shallow_threshold = float(cfg["shallow_threshold"])
    max_shallow_speed = float(cfg["max_shallow_speed"])
    target_depth      = float(cfg["target_depth"])
    target_depth_2    = float(cfg["target_depth_2"])
    hold_duration     = float(cfg["hold_duration"])
    sensor.read(ms5837.OSR_8192)
    starting_sensor_depth = sensor.depth() * 100 # convert to cm

    target_depth_1 = target_depth  # save original to return to after depth2
    leg = 1  # 1: depth1 hold, 2: depth2 hold, 3: depth1 hold again, 4: depth2 forever

    table = DepthEval.load_speed_table("speeds.csv")
    table = [(offset, speed / speed_divisor) for offset, speed in table]
    print(f"Loaded {len(table)} entries.")

def get_depth_reading():
    global sensor, starting_sensor_depth, top
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

def move_motor(current_depth, actual_speed, depth_offset):
    global phase, hold_start_time
    phase = "no phase"

    target_speed = DepthEval.get_speed(table, depth_offset)

    #Check for shallow depth and adjust speed targets
    if current_depth < shallow_threshold and target_speed > 0:
        msg = (f"SHALLOW DEPTH")
        print(msg)
        logging.info(msg)
        target_speed = min(target_speed, max_shallow_speed)

    #calulcate too fast/too slow
    speed_offset = actual_speed - target_speed

    # # Transition: sinking -> holding
    # if phase == "sinking" and abs(depth_offset) <= hold_tolerance:
    #     phase = "holding"
    #     hold_start_time = time.time()
    #     msg = f"Reached target depth {target_depth:.2f}cm. Holding for {hold_duration:.0f}s."
    #     print(msg)
    #     logging.info(msg)

    # which way should the pump move?
    action = get_pump_action(depth_offset, speed_offset)

    msg = (f"[{phase.upper()}] depth={current_depth:.2f}cm  speed={actual_speed:.3f}cm/s  "
           f"depth offset={depth_offset:.2f}cm speed_offset={speed_offset} action={'WaterIn' if action==1 else 'WaterOut'}")
    print(msg)
    logging.info(msg)
    pump(action)
    return False


def data_logger():
    global consecutive_in_window
    elapsed = 0
    while True:
        now = time.time()
        next_log = (int(now) // 5 + 1) * 5
        time.sleep(next_log - now)
        elapsed += 5

        if abs(current_depth - target_depth) <= DEPTH_WINDOW:
            consecutive_in_window += 1
        else:
            consecutive_in_window = 0

        depth_baseline = current_depth
        depth_top = current_depth + TOP_OFFSET
        depth_bottom = current_depth + ENGINE_HEIGHT
        msg = f"0371A : {elapsed} : {depth_baseline:.2f} : {depth_top:.2f} : {depth_bottom:.2f} : {consecutive_in_window}/{REQUIRED_CONSECUTIVE}"
        with open("collect_data.txt", "a") as f:
            f.write(msg + "\n")

        if consecutive_in_window >= REQUIRED_CONSECUTIVE:
            mission_complete.set()

def dive():
    global consecutive_in_window, current_depth, target_depth, leg

    initialize_dive()
    open("collect_data.txt", "w").close()  # erase on startup
    mission_complete.clear()
    consecutive_in_window = 0
    previous_depth = 0

    logger_thread = threading.Thread(target=data_logger, daemon=True)
    logger_thread.start()

    while True:
        print("Starting Main Loop")
        current_depth = get_depth_reading()

        # calculate speed
        actual_speed = (current_depth - previous_depth) / cycle  # positive when sinking

        # calculate offset
        depth_offset = current_depth - target_depth  # negative means too high, positive means too low

        if move_motor(current_depth, actual_speed, depth_offset):
            break

        if mission_complete.is_set():
            if leg == 1:
                msg = f"Leg 1 complete. Moving to depth2 {target_depth_2:.2f}cm."
                target_depth = target_depth_2
                leg = 2
            elif leg == 2:
                msg = f"Leg 2 complete. Returning to depth1 {target_depth_1:.2f}cm."
                target_depth = target_depth_1
                leg = 3
            elif leg == 3:
                msg = f"Leg 3 complete. Staying at depth2 {target_depth_2:.2f}cm forever."
                target_depth = target_depth_2
                leg = 4
            elif leg == 4:
                msg = f"Leg 4: 7 consecutive in-window readings achieved. Continuing to hold at {target_depth_2:.2f}cm."
            print(msg)
            logging.info(msg)
            consecutive_in_window = 0
            mission_complete.clear()

        previous_depth = current_depth

        time.sleep(cycle)


def sample():
    msg = "Sample button pressed. sample() placeholder has not been implemented yet."
    print(msg)
    logging.info(msg)


def battery_level():
    msg = "Battery level: 5.7 volts"
    print(msg)
    logging.info(msg)


def run_button_action():
    form = cgi.FieldStorage()
    print("Content-Type: text/plain\n")

    if "dive" in form:
        dive()
    elif "sample" in form:
        sample()
    elif "battery" in form:
        battery_level()
    else:
        print("No recognized button was pressed.")


if __name__ == "__main__":
    try:
        run_button_action()
    except KeyboardInterrupt:
        GPIO.cleanup()
    except Exception as e:
        msg = f"main.py failed: {e}"
        print(msg)
        logging.exception(msg)
