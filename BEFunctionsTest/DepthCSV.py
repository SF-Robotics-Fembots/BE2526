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

def get_speed(table, offset):
    offsets = [row[0] for row in table]
    i = bisect.bisect_left(offsets, offset)
    # Clamp to valid range
    if i >= len(table):
        return table[-1][1]
    # Return the speed of the upper bound of the window
    return table[i][1]

table = load_speed_table("speeds.csv")
print(f"Loaded {len(table)} entries.")

while True:
    user_input = input("Enter offset (or 'q' to quit): ").strip()
    if user_input.lower() == "q":
        break
    try:
        offset = float(user_input)
        speed = get_speed(table, offset)
        print(f"  Offset {offset} -> Target speed: {speed} cm/s")
    except ValueError:
        print("  Invalid input. Enter a number or 'q'.")
