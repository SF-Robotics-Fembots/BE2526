import time
import os
import sys
import configparser
import glob as globmod
import shutil
import signal
import subprocess
import DepthEval
import ms5837
import smbus
import RPi.GPIO as GPIO
import threading
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

def setup_logging(rotate=False):
    if rotate and os.path.exists("buoy.log"):
        try:
            existing = globmod.glob("buoy_*.log")
            nums = [int(f.replace("buoy_", "").replace(".log", "")) for f in existing if f.replace("buoy_", "").replace(".log", "").isdigit()]
            next_num = max(nums) + 1 if nums else 1
            shutil.copy2("buoy.log", f"buoy_{next_num}.log")
            open("buoy.log", "w").close()
        except OSError:
            pass

    try:
        logging.basicConfig(
            filename="buoy.log",
            level=logging.INFO,
            format="%(asctime)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    except OSError:
        logging.basicConfig(level=logging.INFO, handlers=[logging.NullHandler()])

sensor = ms5837.MS5837_02BA()

DEBUG = 1

GPIO_IN = 5
GPIO_OUT = 6
LOW_BATTERY_LED_GPIO = 11  # BCM GPIO 11
LOW_BATTERY_THRESHOLD = 7.0
RELAY_ACTIVE_LOW = False
RELAY_ACTIVE_LEVEL = GPIO.LOW if RELAY_ACTIVE_LOW else GPIO.HIGH
RELAY_INACTIVE_LEVEL = GPIO.HIGH if RELAY_ACTIVE_LOW else GPIO.LOW
LOW_BATTERY_LED_ON = GPIO.HIGH
LOW_BATTERY_LED_OFF = GPIO.LOW

# Set the GPIO mode (BOARD)
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)


# Set the relay pin as an output pin
GPIO.setup(GPIO_IN, GPIO.OUT)
GPIO.setup(GPIO_OUT, GPIO.OUT)
GPIO.setup(LOW_BATTERY_LED_GPIO, GPIO.OUT, initial=LOW_BATTERY_LED_OFF)
GPIO.output(GPIO_IN, RELAY_INACTIVE_LEVEL)
GPIO.output(GPIO_OUT, RELAY_INACTIVE_LEVEL)

def set_pump_pins_inactive(repeats=3, delay=0.05):
    for _ in range(repeats):
        GPIO.output(GPIO_IN, RELAY_INACTIVE_LEVEL)
        GPIO.output(GPIO_OUT, RELAY_INACTIVE_LEVEL)
        if delay:
            time.sleep(delay)

def startup():
#	print("prep to init")
	sensor.init()
	time.sleep(1)
#	print("prep to read")
	sensor.read(ms5837.OSR_8192)
#	print("prep to set density")
	sensor.setFluidDensity(ms5837.DENSITY_FRESHWATER)

def calibrate_baseline():
    global starting_sensor_depth
    sensor.read(ms5837.OSR_8192)
    starting_sensor_depth = sensor.depth() * 100 # convert to cm
    msg = f"Baseline calibrated at {starting_sensor_depth:.2f} cm"
    print(msg)
    logging.info(msg)
    return starting_sensor_depth

def pump(direction):
    if direction == 1:  # Water In
        GPIO.output(GPIO_OUT, RELAY_INACTIVE_LEVEL)
        GPIO.output(GPIO_IN, RELAY_ACTIVE_LEVEL)
        msg = (f"Water IN EXECUTION  ")
        print(msg)
        logging.info(msg)
    else:  # Water Out
        GPIO.output(GPIO_IN, RELAY_INACTIVE_LEVEL)
        GPIO.output(GPIO_OUT, RELAY_ACTIVE_LEVEL)
        msg = (f"Water OUT EXECUTION  ")
        print(msg)
        logging.info(msg)

def pump_stop():
    try:
        GPIO.output(GPIO_IN, 0)
        GPIO.output(GPIO_OUT, 0)
        msg = "Pump Trying to Stop."
        print(msg)
        logging.info(msg)
        print(f"Alexa Pump stop")
 #       set_pump_pins_inactive(repeats=5)
    except Exception as e:
        msg = "Pump Exception."
        print(msg)
        logging.info(msg)
        print(f"Pump stop failed: {e}")
        logging.exception("Pump stop failed")
        return

    msg = "Pump stopped."
    print(msg)
    logging.info(msg)

def remove_pid_file():
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    except OSError:
        pass

def create_stop_request():
    try:
        with open(STOP_FILE, "w") as f:
            f.write(str(time.time()))
    except OSError:
        pass

def remove_stop_request():
    try:
        if os.path.exists(STOP_FILE):
            os.remove(STOP_FILE)
    except OSError:
        pass

def stop_requested():
    return os.path.exists(STOP_FILE)

def shutdown_handler(signum=None, frame=None):
    msg = "Stop requested. Shutting down."
    print(msg)
    logging.info(msg)
    pump_stop()
    remove_pid_file()
    remove_stop_request()
    # Keep the relay pins driven inactive so the motor cannot float back on.
    sys.exit(0)

cycle=0.1 #seconds
ENGINE_HEIGHT = 50.0  # cm — difference between the baseline and the bottom
TOP_OFFSET = -17.0  # cm — top of engine is 17cm above baseline
DEPTH_WINDOW = 33.0       # cm — allowed deviation from target depth
REQUIRED_CONSECUTIVE = 7  # consecutive 5s readings needed within window
DATA_FILE = "collect_data.txt"
SAMPLE_FILE = "sample_data.txt"
PID_FILE = "main.pid"
STOP_FILE = "stop_dive.request"

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
    calibrate_baseline()

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
        with open(DATA_FILE, "a") as f:
            f.write(msg + "\n")

        if consecutive_in_window >= REQUIRED_CONSECUTIVE:
            mission_complete.set()

def dive():
    global consecutive_in_window, current_depth, target_depth, leg

    remove_stop_request()
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    try:
        initialize_dive()
        open(DATA_FILE, "w").close()  # erase on startup
        mission_complete.clear()
        consecutive_in_window = 0
        previous_depth = 0

        logger_thread = threading.Thread(target=data_logger, daemon=True)
        logger_thread.start()

        while True:
            if stop_requested():
                msg = "Stop request found. Ending dive loop."
                print(msg)
                logging.info(msg)
                break

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
    finally:
        pump_stop()
        remove_pid_file()
        remove_stop_request()


def sample():
    startup()
    calibrate_baseline()
    depth_baseline = get_depth_reading()
    depth_top = depth_baseline + TOP_OFFSET
    depth_bottom = depth_baseline + ENGINE_HEIGHT
    in_window = f"SAMPLE"
    row = f"0371A : NA : {depth_baseline:.2f} : {depth_top:.2f} : {depth_bottom:.2f} : {in_window}"

    with open(SAMPLE_FILE, "w") as f:
        f.write(row + "\n")

    msg = "Sample row added."
    print(msg)
    logging.info(msg)


def battery_level():
    try:
        import board
        import adafruit_ina228

        i2c = board.I2C()
        ina = adafruit_ina228.INA228(i2c)
        voltage = ina.bus_voltage
    except Exception as e:
        msg = f"Battery check failed: {e}"
        print(msg)
        logging.exception(msg)
        return

    is_low = voltage < LOW_BATTERY_THRESHOLD
    GPIO.output(LOW_BATTERY_LED_GPIO, LOW_BATTERY_LED_ON if is_low else LOW_BATTERY_LED_OFF)

    msg = f"Battery level: {voltage:.3f} volts. Low battery LED {'ON' if is_low else 'OFF'}."
    print(msg)
    logging.info(msg)

def command_is_dive(args):
    parts = args.split()
    main_filename = os.path.basename(__file__)
    has_main = any(os.path.basename(part) == main_filename for part in parts)
    return has_main and "dive" in parts

def start_new_process_group():
    try:
        os.setsid()
    except OSError:
        pass

def signal_dive_process(pid, sig):
    try:
        pgid = os.getpgid(pid)
        if pgid == pid:
            os.killpg(pgid, sig)
            return "process group"
    except OSError:
        pass

    os.kill(pid, sig)
    return "process"

def find_dive_pids():
    pids = set()
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                pids.add(int(f.read().strip()))
        except (OSError, ValueError):
            pass

    try:
        result = subprocess.run(
            ["ps", "-eo", "pid=,args="],
            capture_output=True,
            text=True,
            check=False,
        )
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue

            try:
                pid_text, args = line.split(None, 1)
                pid = int(pid_text)
            except ValueError:
                continue

            if command_is_dive(args):
                pids.add(pid)
    except OSError:
        pass

    pids.discard(os.getpid())
    return pids

def is_process_running(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False

def stop_dive():
    create_stop_request()
    print("Stop request created.")
    pump_stop()

    pids = find_dive_pids()
    if not pids:
        print("No dive process found. Stop request left in place.")
        remove_pid_file()
        return

    for pid in pids:
        try:
            target = signal_dive_process(pid, signal.SIGINT)
            print(f"Ctrl+C signal sent to dive {target} {pid}.")
        except OSError as e:
            print(f"Dive process {pid} was not running: {e}")

    deadline = time.time() + 5
    while time.time() < deadline:
        try:
            set_pump_pins_inactive(repeats=1, delay=0)
        except Exception as e:
            print(f"Could not hold pump pins inactive while stopping: {e}")
            logging.exception("Could not hold pump pins inactive while stopping")
        remaining = [pid for pid in pids if is_process_running(pid)]
        if not remaining:
            break
        time.sleep(0.1)

    for pid in pids:
        if is_process_running(pid):
            try:
                target = signal_dive_process(pid, signal.SIGTERM)
                print(f"Terminate signal sent to dive {target} {pid}.")
            except OSError as e:
                print(f"Dive process {pid} could not be terminated: {e}")

    deadline = time.time() + 3
    while time.time() < deadline:
        try:
            set_pump_pins_inactive(repeats=1, delay=0)
        except Exception as e:
            print(f"Could not hold pump pins inactive while terminating: {e}")
            logging.exception("Could not hold pump pins inactive while terminating")
        remaining = [pid for pid in pids if is_process_running(pid)]
        if not remaining:
            break
        time.sleep(0.1)

    for pid in pids:
        if is_process_running(pid):
            try:
                target = signal_dive_process(pid, signal.SIGKILL)
                print(f"Force killed dive {target} {pid}.")
            except OSError as e:
                print(f"Dive process {pid} could not be force killed: {e}")

    pump_stop()
    remove_pid_file()
    remaining = [pid for pid in pids if is_process_running(pid)]
    if remaining:
        print(f"Dive process still running: {remaining}. Stop request left in place.")
    else:
        remove_stop_request()


def run_button_action():
    if len(sys.argv) > 1:
        action = sys.argv[1]
    else:
        action = None

    setup_logging(rotate=action == "dive")

    if action == "dive":
        start_new_process_group()
        signal.signal(signal.SIGTERM, shutdown_handler)
        signal.signal(signal.SIGINT, shutdown_handler)
        dive()
    elif action == "sample":
        sample()
    elif action == "battery":
        battery_level()
    elif action == "stop":
        stop_dive()
    else:
        print("No recognized button was pressed.")


if __name__ == "__main__":
    try:
        run_button_action()
    except KeyboardInterrupt:
        pump_stop()
        remove_pid_file()
    except Exception as e:
        msg = f"main.py failed: {e}"
        print(msg)
        logging.exception(msg)
        pump_stop()
        remove_pid_file()
