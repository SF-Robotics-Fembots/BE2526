#!/usr/bin/env python3
import time
import board
import adafruit_ina228

i2c = board.I2C()
ina = adafruit_ina228.INA228(i2c)

print("INA228 voltage test — Ctrl+C to stop")
print("-" * 40)

try:
    while True:
        print(f"Bus Voltage:   {ina.bus_voltage:.3f} V")
        print(f"Shunt Voltage: {ina.shunt_voltage * 1000:.3f} mV")
        print(f"Current:       {ina.current:.2f} mA")
        print(f"Power:         {ina.power:.2f} mW")
        print(f"Temperature:   {ina.die_temperature:.2f} C")
        print("-" * 40)
        time.sleep(1)
except KeyboardInterrupt:
    print("Done.")
