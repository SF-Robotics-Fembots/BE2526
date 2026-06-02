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
    user_input = input("Enter target depth in cm (or 'q' to quit): ").strip()
    if user_input.lower() == "q":
        break
    try:
        target_depth = float(user_input)
        break
    except ValueError:
        print("  Invalid input. Enter a number.")

print(f"Target depth set to {target_depth} cm.")

while True:
    user_input = input("Enter actual depth in cm (or 'q' to quit): ").strip()
    if user_input.lower() == "q":
        break
    try:
        actual_depth = float(user_input)
        offset = actual_depth - target_depth
        speed = get_speed(table, offset)
        if offset < 0:
            depth_status = "Too High"
        elif offset > 0:
            depth_status = "Too Low"
        else:
            depth_status = "On Depth"
        print(f"  Actual: {actual_depth} cm | Target: {target_depth} cm | Offset: {offset} cm ({depth_status}) -> Target speed: {speed} cm/s")
        actual_speed_input = input("  Enter actual speed in cm/s: ").strip()
        actual_speed = float(actual_speed_input)
        speed_offset = actual_speed - speed
        if actual_speed == speed:
            speed_status = "On Speed"
            action = "On Target"
        elif speed > 0:  # target is sinking
            if actual_speed < speed:
                speed_status = "Too Slow"
                action = "Water In"
            else:
                speed_status = "Too Fast"
                action = "Water Out"
        else:  # target is rising
            if actual_speed > speed:
                speed_status = "Too Slow"
                action = "Water Out"
            else:
                speed_status = "Too Fast"
                action = "Water In"
        print(f"  Actual speed: {actual_speed} cm/s | Target speed: {speed} cm/s | Speed offset: {speed_offset} cm/s ({speed_status}) -> {action}")
    except ValueError:
        print("  Invalid input. Enter a number or 'q'.")
