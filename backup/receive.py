import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation

#  Configure serial port 
# Need to adjust to match the system
ser = serial.Serial(port="/dev/ttyUSB0", baudrate=9600, timeout=1)

#  Data storage 
times = []
depths = []
targets = []

#  Live plot setup 
fig, ax = plt.subplots()
line_depth, = ax.plot([], [], label="Current Depth", color="blue")
line_target, = ax.plot([], [], label="Target Depth", color="red", linestyle="--")

ax.set_xlabel("Packet #")
ax.set_ylabel("Depth (m)")
ax.set_title("Live Buoyancy Engine Depth Tracking")
ax.legend()
ax.grid(True)

def update(frame):
    global times, depths, targets

    try:
        line = ser.readline().decode("utf-8").strip()
        if line:
            # Expected format: packet_id,target_depth,current_depth,pressure_pa,error,pump_action
            parts = line.split(",")
            if len(parts) >= 3:
                packet_id = int(parts[0])
                target_depth = float(parts[1])
                current_depth = float(parts[2])

                times.append(packet_id)
                targets.append(target_depth)
                depths.append(current_depth)

                # Update plot data
                line_depth.set_data(times, depths)
                line_target.set_data(times, targets)

                ax.relim()
                ax.autoscale_view()
    except Exception as e:
        print(f"Parse error: {e}")

    return line_depth, line_target

ani = animation.FuncAnimation(fig, update, interval=500, blit=False)
plt.show()