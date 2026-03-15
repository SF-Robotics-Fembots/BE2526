import csv
import matplotlib.pyplot as plt

def load_log(filename):
    times, target_depths, current_depths, errors = [], [], [], []
    with open(filename, newline="") as logfile:
        reader = csv.DictReader(logfile)
        for row in reader:
            times.append(float(row["time"]))
            target_depths.append(float(row["target_depth"]))
            current_depths.append(float(row["current_depth"]))
            errors.append(float(row["error"]))
    # Normalize time to start at zero
    t0 = times[0]
    times = [t - t0 for t in times]
    return times, target_depths, current_depths, errors

#  List of logs to compare 
log_files = ["mission_log.csv", "mission_log_run2.csv", "mission_log_run3.csv"]

#  Plot Depth vs. Time 
plt.figure(figsize=(10, 6))
for fname in log_files:
    times, targets, currents, _ = load_log(fname)
    plt.plot(times, currents, label=f"{fname} Current Depth")
    plt.plot(times, targets, linestyle="--", label=f"{fname} Target Depth")

plt.xlabel("Time (s)")
plt.ylabel("Depth (m)")
plt.title("Depth vs. Time (Multiple Runs)")
plt.legend()
plt.grid(True)
plt.savefig("depth_vs_time_multi.png")

#  Plot Error vs. Time 
plt.figure(figsize=(10, 6))
for fname in log_files:
    times, _, _, errors = load_log(fname)
    plt.plot(times, errors, label=f"{fname} Error")

plt.xlabel("Time (s)")
plt.ylabel("Error (m)")
plt.title("Error vs. Time (Multiple Runs)")
plt.legend()
plt.grid(True)
plt.savefig("error_vs_time_multi.png")

print("Comparison plots saved as depth_vs_time_multi.png and error_vs_time_multi.png")