#!/usr/bin/env python3
"""Command-line battery tester for the INA228 power monitor.

Reads voltage, current, power, and temperature from the INA228 over I2C.
Run a single reading, or monitor continuously at a fixed interval.

Examples:
    python3 battery_test.py                 # one reading and exit
    python3 battery_test.py -c               # monitor until Ctrl+C
    python3 battery_test.py -c -i 0.5        # monitor every 0.5 s
    python3 battery_test.py -c --low 11.1    # warn below 11.1 V
"""

import argparse
import sys
import time


def connect():
    """Open the I2C bus and return an INA228 instance."""
    import board
    import adafruit_ina228

    i2c = board.I2C()
    return adafruit_ina228.INA228(i2c)


def read(ina):
    """Return a dict of the current sensor readings.

    Missing attributes (depending on library version / wiring) are
    reported as None rather than raising.
    """
    def safe(name):
        try:
            return getattr(ina, name)
        except Exception:
            return None

    return {
        "voltage": safe("bus_voltage"),   # volts
        "current": safe("current"),       # milliamps
        "power": safe("power"),           # milliwatts
        "temperature": safe("temperature"),  # degrees C
    }


def format_reading(r, low=None):
    """Format a reading dict into a one-line status string."""
    parts = []

    v = r["voltage"]
    if v is not None:
        flag = ""
        if low is not None and v < low:
            flag = "  *** LOW ***"
        parts.append(f"{v:6.3f} V{flag}")
    else:
        parts.append("   -- V")

    i = r["current"]
    if i is not None:
        # current is reported in mA; show A for readability
        parts.append(f"{i / 1000.0:7.3f} A")

    p = r["power"]
    if p is not None:
        parts.append(f"{p / 1000.0:7.3f} W")

    t = r["temperature"]
    if t is not None:
        parts.append(f"{t:5.1f} C")

    return "  ".join(parts)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="INA228 battery tester (voltage / current / power / temp)."
    )
    parser.add_argument(
        "-c", "--continuous", action="store_true",
        help="keep reading until interrupted (Ctrl+C)",
    )
    parser.add_argument(
        "-i", "--interval", type=float, default=1.0,
        help="seconds between readings in continuous mode (default: 1.0)",
    )
    parser.add_argument(
        "-n", "--count", type=int, default=None,
        help="stop after N readings (continuous mode only)",
    )
    parser.add_argument(
        "--low", type=float, default=None,
        help="flag readings below this voltage threshold",
    )
    args = parser.parse_args(argv)

    try:
        ina = connect()
    except Exception as e:
        print(f"Could not connect to INA228: {e}", file=sys.stderr)
        print(
            "Check wiring and that the sensor shows up: i2cdetect -y 1",
            file=sys.stderr,
        )
        return 1

    if not args.continuous:
        try:
            print(format_reading(read(ina), low=args.low))
        except Exception as e:
            print(f"Read failed: {e}", file=sys.stderr)
            return 1
        return 0

    readings = 0
    try:
        while True:
            try:
                line = format_reading(read(ina), low=args.low)
            except Exception as e:
                line = f"read error: {e}"
            print(line)
            sys.stdout.flush()

            readings += 1
            if args.count is not None and readings >= args.count:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
