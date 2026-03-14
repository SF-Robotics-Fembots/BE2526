import time
import DepthCSV

target_depth = float(input("Enter target depth in cm: "))
previous_depth = current_depth

while True:
    current_depth = float(input("Enter current depth in cm: "))

    # first reading (no speed yet)
    if previous_depth is None:
        previous_depth = current_depth
        print("Initial depth set.")
        continue

    # calculate speed
    actual_speed = previous_depth - current_depth

    # calculate offset
    depth_offset = target_depth - current_depth

    # check DepthCSV logic
    action = DepthCSV.check_depth(actual_speed, depth_offset)

    print("Current Depth:", current_depth)
    print("Actual Speed:", actual_speed, "cm/s")
    print("Depth Offset:", depth_offset)
    print("Action:", action)

    previous_depth = current_depth

    time.sleep(.2)