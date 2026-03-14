

target_depth = int(input("Enter target depth in cm: ").strip())

while True:
    current_depth = int(input("Enter actual depth in cm (or 'q' to quit): ").strip())
    if current_depth == "q":
        break
    offset = current_depth - target_depth
    if offset < 0:
        print(f"Too High by {-offset} cm")
    elif offset > 0:
        print(f"Too Low by {offset} cm")
    else:
        print("On Depth")

    actual_speed = current_depth - previous_depth
    target_speed = get_speed(table, offset)
    previous_depth = current_depth