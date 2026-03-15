import csv
import matplotlib.pyplot as plt

# Read mission log
times = []
target_depths = []
current_depths = []
errors = []

with open("mission_log.csv", newline="") as logfile:
    reader = csv.DictReader(logfile)
    for row in reader:
        times.append(float(row["time"]))
        target_depths.append(float(row["target_depth"]))
        current_depths.append(float(row["current_depth"]))
        errors.append(float(row["error"]))

# Normalize time to start at zero
t0 = times[0]
times = [t - t0 for t in times]

#  1: Depth vs. Time 
plt.figure(figsize=(10, 6))
plt.plot(times, current_depths, label="Current Depth", color="blue")
plt.plot(times, target_depths, label="Target Depth", color="red", linestyle="--")
plt.xlabel("Time (s)")
plt.ylabel("Depth (m)")
plt.title("Depth vs. Time")
plt.legend()
plt.grid(True)
plt.savefig("depth_vs_time.png")

#  2: Error vs. Time 
plt.figure(figsize=(10, 6))
plt.plot(times, errors, label="Error", color="green")
plt.xlabel("Time (s)")
plt.ylabel("Error (m)")
plt.title("Error vs. Time")
plt.legend()
plt.grid(True)
plt.savefig("error_vs_time.png")

print("Plots saved as depth_vs_time.png and error_vs_time.png")