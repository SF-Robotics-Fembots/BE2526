import time
import board
import digitalio
import adafruit_mprls  # Replace with your actual sensor library
import busio
import csv
import serial  # PySerial for UART/USB output

#  Setup I2C for pressure sensor 
i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_mprls.MPRLS(i2c, psi_min=0, psi_max=25)  # adjust for your sensor

#  Setup H-bridge pins for pump 
in1 = digitalio.DigitalInOut(board.D17)
in1.direction = digitalio.Direction.OUTPUT

in2 = digitalio.DigitalInOut(board.D27)
in2.direction = digitalio.Direction.OUTPUT

#  Setup Serial (adjust port to your system, e.g. '/dev/ttyUSB0' or 'COM3') 
ser = serial.Serial(port="/dev/ttyUSB0", baudrate=9600, timeout=1)

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
        return depth_m, pressure_pa
    except Exception as e:
        print(f"Sensor error: {e}")
        return None, None

def send_packet(packet_id, target_depth, depth, pressure, error, action):
    """Send packet over serial in CSV format."""
    packet = f"{packet_id},{target_depth:.2f},{depth:.2f},{pressure:.1f},{error:.2f},{action}\n"
    ser.write(packet.encode("utf-8"))

def go_to_depth(target_depth, hold_time=0, min_depth=0.1, tolerance=0.05, timeout=60, log_writer=None):
    print(f"Target depth: {target_depth} m")
    start_time = time.monotonic()
    packet_id = 1

    while True:
        depth, pressure = read_depth()
        if depth is None:
            print("Abort: Sensor failure.")
            pump_stop()
            return

        error = target_depth - depth

        # Safety: never break surface
        if depth < min_depth:
            print(f"Abort: Depth {depth:.2f} m < {min_depth} m (surface breach).")
            pump_stop()
            return

        # Timeout fail-safe
        if (time.monotonic() - start_time) > timeout:
            print("Abort: Timeout exceeded.")
            pump_stop()
            return

        action = "fill" if error > 0 else "empty" if error < 0 else "stop"

        # Logging
        if log_writer:
            log_writer.writerow({
                "time": time.time(),
                "target_depth": target_depth,
                "current_depth": depth,
                "pressure_pa": pressure,
                "error": error,
                "pump_action": action
            })

        # Serial packet
        send_packet(packet_id, target_depth, depth, pressure, error, action)
        packet_id += 1

        if abs(error) <= tolerance:
            pump_stop()
            print(f"Holding at {depth:.2f} m")
            break

        if error > 0:
            pump_fill()
        else:
            pump_empty()

        time.sleep(0.5)

    # Hold at depth
    if hold_time > 0:
        print(f"Holding for {hold_time} seconds...")
        pump_stop()
        time.sleep(hold_time)

#  Mission sequence 
def mission():
    print("Starting mission...")

    with open("mission_log.csv", mode="w", newline="") as logfile:
        fieldnames = ["time", "target_depth", "current_depth", "pressure_pa", "error", "pump_action"]
        log_writer = csv.DictWriter(logfile, fieldnames=fieldnames)
        log_writer.writeheader()

        # Descend to 2.5m and hold 30s
        go_to_depth(2.5, hold_time=30, log_writer=log_writer)

        # Ascend to 0.4m and hold 30s
        go_to_depth(0.4, hold_time=30, log_writer=log_writer)

    print("Mission complete. Log saved to mission_log.csv.")

if __name__ == "__main__":
    mission()