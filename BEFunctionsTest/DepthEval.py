import csv
import bisect

def load_speed_table(filename):
    table = []
    with open(filename, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            offset = float(row["Offset"])
            speed = float(row["Speed"])
            table.append((offset, speed))
    table.sort(key=lambda x: x[0])
    return table

def get_speed(table, depth_offset):
    offsets = [row[0] for row in table]
    i = bisect.bisect_left(offsets, offset)
    # Clamp to valid range
    if i >= len(table):
        return table[-1][1]
    # Return the speed of the upper bound of the window
    return table[i][1]
