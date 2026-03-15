import time
import board
import busio
import RPi.GPIO as GPIO
import ms5837

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Define GPIO pins for pump control
PUMP_INFLATE_PIN = 17  # GPIO pin to fill chamber (descend)
PUMP_DEFLATE_PIN = 27  # GPIO pin to empty chamber (ascend)

GPIO.setup(PUMP_INFLATE_PIN, GPIO.OUT)
GPIO.setup(PUMP_DEFLATE_PIN, GPIO.OUT)

# Initialize I2C and pressure sensor
i2c = busio.I2C(board.SCL, board.SDA)
sensor = ms5837.MS5837_30BA(i2c)

def startup():
    if not sensor.init():
        print("Sensor initialization failed!")
        exit(1)
    sensor.setFluidDensity(ms5837.DENSITY_FRESHWATER)
    print("Sensor initialized.")

def pump_inflate():
    GPIO.output(PUMP_INFLATE_PIN, GPIO.HIGH)
    GPIO.output(PUMP_DEFLATE_PIN, GPIO.LOW)

def pump_deflate():
    GPIO.output(PUMP_INFLATE_PIN, GPIO.LOW)
    GPIO.output(PUMP_DEFLATE_PIN, GPIO.HIGH)

def pump_stop():
    GPIO.output(PUMP_INFLATE_PIN, GPIO.LOW)
    GPIO.output(PUMP_DEFLATE_PIN, GPIO.LOW)

def go_to_depth(target_depth_m):
    tolerance = 0.05  # meters
    max_duration = 60  # seconds
    start_time = time.time()

    while True:
        sensor.read(ms5837.OSR_256)
        current_depth = sensor.depth()
        error = target_depth_m - current_depth

        print(f"Current depth: {current_depth:.2f} m | Target: {target_depth_m:.2f} m")

        if abs(error) < tolerance:
            pump_stop()
            print("Target depth reached.")
            break
        elif error > 0:
            pump_inflate()
        else:
            pump_deflate()

        if time.time() - start_time > max_duration:
            print("Timeout: Could not reach target depth.")
            pump_stop()
            break

        time.sleep(0.2)

if __name__ == "__main__":
    try:
        startup()

        print("\nDescending to 40 cm...")
        go_to_depth(0.4)
        print("Holding at 40 cm for 45 seconds...")
        time.sleep(45)

        print("\nDescending to 2.5 meters...")
        go_to_depth(2.5)
        print("Holding at 2.5 meters for 30 seconds...")
        time.sleep(30)

        print("\nAscending to 0.05 meters (just below surface)...")
        go_to_depth(0.05)
        print("Holding at surface depth. Mission complete.")

        print("\nMission complete. Stopping pump.")
        pump_stop()
        GPIO.cleanup()

    except KeyboardInterrupt:
        print("\nInterrupted. Stopping pump and cleaning up GPIO.")
        pump_stop()
        GPIO.cleanup()