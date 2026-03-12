import threading
import time
from datetime import datetime

logging_enabled = False
exit_flag = False

def logger_thread():
    while not exit_flag:
        if logging_enabled:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[LOG] {timestamp}")
            with open("Thread-log.txt", "a") as f:
                f.write(timestamp + "\n")
        time.sleep(3)

t = threading.Thread(target=logger_thread, daemon=True)
t.start()

while True:
    user_input = input("Enter 1 (start logging), 0 (stop logging), or 2 (exit): ").strip()
    if user_input == "1":
        logging_enabled = True
        print("Logging started.")
    elif user_input == "0":
        logging_enabled = False
        print("Logging stopped.")
    elif user_input == "2":
        exit_flag = True
        print("Exiting...")
        t.join(timeout=4)
        break
    else:
        print("Invalid input. Enter 1, 0, or 2.")
