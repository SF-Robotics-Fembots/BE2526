import time
import board
import digitalio
import busio
import csv

#  Setup I2C for pressure sensor 
i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_mprls.MPRLS(i2c, psi_min=0, psi_max=25)  # type: ignore #need to adjust

#  Setup H-bridge pins 
in1 = digitalio.DigitalInOut(board.D17)
in1.direction = digitalio.Direction.OUTPUT

in2 = digitalio.DigitalInOut(board.D27)
in2.direction = digitalio.Direction.OUTPUT

def pump_fill():
    in1.value = True
    in2.value = False

def pump_empty():
    in1.value = False
    in2.value = True

def pump_stop():
    in1.value = False
    in2.value = False

def read_depth():
    """Convert pressure sensor reading to depth (m)."""
    try:
        pressure_pa = sensor.pressure
        depth_m = pressure_pa / (1000 * 9.81)
        return depth_m
    except Exception as e:
        print(f"Sensor error: {e}")
        return None

#  PID controller 
class PIDController:
    def __init__(self, Kp=1.2, Ki=0.1, Kd=0.05, tolerance=0.05, min_depth=0.1):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.tolerance = tolerance
        self.integral = 0
        self.last_error = 0
        self.last_time = time.monotonic()
        self.min_depth = min_depth

    def compute(self, target, current):
        error = target - current
        now = time.monotonic()
        dt = now - self.last_time if self.last_time else 0.1

        self.integral += error * dt
        derivative = (error - self.last_error) / dt if dt > 0 else 0

        output = (self.Kp * error) + (self.Ki * self.integral) + (self.Kd * derivative)

        self.last_error = error
        self.last_time = now

        return output, error

def go_to_depth(target_depth, pid: PIDController, hold_time=0, log_writer=None, timeout=60, max_error=1.0):
    """PID loop with fail-safe abort conditions."""
    print(f"Target depth: {target_depth} m")
    start_time = time.monotonic()

    while True:
        depth = read_depth()
        if depth is None:
            print("Abort: Sensor failure.")
            pump_stop()
            return

        output, error = pid.compute(target_depth, depth)

        # Safety: don't break surface
        if depth < pid.min_depth:
            print(f"Abort: Depth {depth:.2f} m < {pid.min_depth} m (surface breach).")
            pump_stop()
            return

        # Fail-safe: timeout
        if (time.monotonic() - start_time) > timeout:
            print("Abort: Timeout exceeded.")
            pump_stop()
            return

        # Fail-safe: error too large
        if abs(error) > max_error:
            print(f"Abort: Error {error:.2f} m too large.")
            pump_stop()
            return

        # Logging
        if log_writer:
            log_writer.writerow({
                "time": time.time(),
                "target_depth": target_depth,
                "current_depth": depth,
                "error": error,
                "pid_output": output,
                "pump_action": "fill" if output > 0 else "empty" if output < 0 else "stop"
            })

        if abs(error) <= pid.tolerance:
            pump_stop()
            print(f"Holding at {depth:.2f} m")
            break

        if output > 0:
            pump_fill()
        else:
            pump_empty()

        time.sleep(0.5)

    # hold at depth
    if hold_time > 0:
        print(f"Holding for {hold_time} seconds...")
        pump_stop()
        time.sleep(hold_time)

#  Mission sequence 
def mission():
    print("Starting mission...")

    pid = PIDController(Kp=1.2, Ki=0.1, Kd=0.05, tolerance=0.05, min_depth=0.1)

    with open("mission_log.csv", mode="w", newline="") as logfile:
        fieldnames = ["time", "target_depth", "current_depth", "error", "pid_output", "pump_action"]
        log_writer = csv.DictWriter(logfile, fieldnames=fieldnames)
        log_writer.writeheader()

        # go down to 2.5m and hold 30s
        go_to_depth(2.5, pid, hold_time=30, log_writer=log_writer)

        # go up to 0.4m and hold 30s
        go_to_depth(0.4, pid, hold_time=30, log_writer=log_writer)

    print("Mission complete. Log saved to mission_log.csv.")

if __name__ == "__main__":
    mission()