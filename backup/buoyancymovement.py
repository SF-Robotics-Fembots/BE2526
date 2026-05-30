#!/usr/bin/env python3
print("Content-Type: text/html\n\n")
import signal
import sys
import RPi.GPIO as GPIO
import time
from simple_pid import PID
import ms5837
import smbus
import datetime
import threading
import cgi
import cgitb
import Adafruit_MCP3008
from gpiozero import MCP3008
global target_position
global position
import os
import fcntl
#import testReadings
k = open("collect_data.txt" , "w")
txt_file = "collect_data.txt"
TOP_SWITCH = 21
ROTATE_SWITCH = 6
SERVO_OFF = 150
SERVO_UP = 200
SERVO_DOWN = 100
global SYRINGE_MAX

SYRINGE_NEUTRAL = 14	 #was 25 #was 16 #was 14
SYRINGE_MAX = 37 #was 44 #was 30 #was 37

SEC_PER_CLICK = 2.384615

SERVO_CHANNEL = 0

start_depth = 0

p = -0.001 #was -0.02
i = 0 #was -0.00015
d = 0

GPIO.setmode(GPIO.BCM)
GPIO.setup(ROTATE_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(TOP_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_UP)

sensor = ms5837.MS5837_02BA(1)
global second_time
counter=0
second_time = 0
time.sleep(1)
file = open("pidDepth.txt", "w")
file2 = open("Depth.txt", "w")
#k = open("collect_data.txt", "w")
b = open("battery_check.txt", "w")

def handle_signal(signum, frame):
	Set_Servo(SERVO_CHANNEL, SERVO_OFF)
	file.close()
	print("bye")
	sys.exit(0)

# Register the handler for common termination signals
signal.signal(signal.SIGTERM, handle_signal)  # kill
signal.signal(signal.SIGINT, handle_signal)   # Ctrl+C


# Turn on servo with servoblaster
def Set_Servo(channel, pulse_width):
	with open('/dev/servoblaster', 'w') as f:
		f.write(f"{channel}={pulse_width}\n")

def startup():
	Set_Servo(SERVO_CHANNEL, SERVO_OFF) 
	sensor.init()
	time.sleep(1)
	sensor.read(ms5837.OSR_256)
	sensor.setFluidDensity(ms5837.DENSITY_FRESHWATER)


def Go_To_Top():
#code to turn on servo and fill syringe w water and stop it when switch (pin 20) is activated
	global position
	print("GoToTop\n")
	count=0
	if (GPIO.input(TOP_SWITCH) == 0):
		Set_Servo(SERVO_CHANNEL, SERVO_OFF)
		position=0
		return

	while (GPIO.input(TOP_SWITCH) == 1):
		Set_Servo(SERVO_CHANNEL, SERVO_UP)
		if (GPIO.input(ROTATE_SWITCH) == 0):
			count+=1
			print("Count = ", count)
			while(GPIO.input(ROTATE_SWITCH) == 0):
				if (GPIO.input(TOP_SWITCH) == 0):
					break
		time.sleep(0.5)
		Set_Servo(SERVO_CHANNEL, SERVO_OFF)
	position = 0
	print("top reached")

def Go_To_Pos(target_position):
#code to turn on servo and fill syringe w water and stop it when switch (pin 20) is activated
        global position
        print("starting position = ", position)
        print("going to ", target_position)

        if target_position < 0:
               target_position = 0
        if target_position > SYRINGE_MAX:
                target_position = SYRINGE_MAX
        move_amount = target_position - position
        if target_position == 0:
                Go_To_Top()
                return
        if move_amount > 0:
                Set_Servo(SERVO_CHANNEL, SERVO_DOWN) 
                while (move_amount >= 1):
                        position=int(position)
                        if (GPIO.input(ROTATE_SWITCH) == 0):  #wait for click
                                move_amount-=1 #reduce remaining amount to move by 1 rotation
                                position+=1
                                print("New Position = ", position, "Move Amount = ", move_amount)
                                while(GPIO.input(ROTATE_SWITCH) == 0): #wait for unclick
                                       time.sleep(0.2)
                        time.sleep(0.3)
                Set_Servo(SERVO_CHANNEL, SERVO_OFF)  
                #Accounting for pid decimal

                pos_part=(target_position - position)
                if (pos_part != 0):
                     print("pos_part, = ", pos_part)
                     time_part = pos_part * SEC_PER_CLICK
                     Set_Servo(SERVO_CHANNEL, SERVO_DOWN)
                     time.sleep(time_part)
                     Set_Servo(SERVO_CHANNEL, SERVO_OFF)
                     position+=pos_part
#               p.ChangeDutyCycle(SERVO_OFF)

        if move_amount < 0:
                if (GPIO.input(TOP_SWITCH) == 0):
                   Set_Servo(SERVO_CHANNEL, SERVO_OFF)
                   return

                print("Move Amount less than 0: ", move_amount)
                #target_position = int(target_position)
                Set_Servo(SERVO_CHANNEL, SERVO_UP) 
                time.sleep(0.25)
#               p.ChangeDutyCycle(SERVO_UP)
                while (move_amount <= -1):
                        position=int(position)
                        if (GPIO.input(ROTATE_SWITCH) == 0):
                                move_amount += 1
                                position-=1
                                print("New Position = ", position, "Move Amount = ", move_amount)
                                while(GPIO.input(ROTATE_SWITCH) == 0):
                                        time.sleep(0.2)
                        time.sleep(0.3)
                Set_Servo(SERVO_CHANNEL, SERVO_OFF) 

                if (GPIO.input(TOP_SWITCH) == 0):
                    Set_Servo(SERVO_CHANNEL, SERVO_OFF) 
                    return

# how much micro movement
                pos_part=(position - target_position)
                if (pos_part != 0):
                   #pos_part = 1-pos_part
                   print("pos_part, = ", pos_part)
                   Set_Servo(SERVO_CHANNEL, SERVO_UP)
                   time.sleep(abs(pos_part * SEC_PER_CLICK))
                   Set_Servo(SERVO_CHANNEL, SERVO_OFF)
                   position-=pos_part
#                p.ChangeDutyCycle(SERVO_OFF)
        print("position reached: ", position)
        return

def Output_Info(depth, dive_time, on_target, s5_periods):
	print("On-target? ", on_target)
	with open("/home/robotics/BE2425/collect_mg.txt","w") as k:
		print("RN08" + " : " + (str(depth)) + ":" + str(dive_time) + " : " + str(on_target) + " : " + str(s5_periods) + "\n", file=k)
		print("RN08" + " : " + (str(depth)) + ":" + str(dive_time) + " : " + str(on_target) + " : " + str(s5_periods) + "\n")


def Go_To_Depth(target_depth):
	global position
	global target_position
	
	global SYRINGE_NEUTRAL

	#set start depth
	sensor.read(ms5837.OSR_256)
	depth = sensor.depth()
	pressure = sensor.pressure(ms5837.UNITS_kPa)
	start_depth = depth
	
	count_start=0 #counts during neutral buoyancy micro adjustment 
	s5_periods=1 #5 second periods
	on_target=0 #are we on target depth
	dive_time=0 #how long have we been diving?

	start_time = datetime.datetime.now()
	print("start time = ", start_time)
	
	while ((depth - start_depth < 0.05) & (dive_time < 60)):
		now_time = datetime.datetime.now()
		dive_time = int((now_time - start_time).total_seconds())
		print("start time = ", start_time, "now time = ", now_time,  "dive_time = ", dive_time, file=file)	
		if dive_time >= (5 * s5_periods):
			s5_periods+=1
			readings(dive_time, pressure, depth)
		Go_To_Pos(SYRINGE_NEUTRAL - 0.25)
		count_start+=1
		sensor.read(ms5837.OSR_256)
		depth = sensor.depth()
		print("sd - current depth: ", start_depth)
		print("sd - start depth: ", depth)
#		print("sd - start depth: ", start_depth, file=file2)
#		print("sd - current depth: ", depth, file=file2)
		if GPIO.input(TOP_SWITCH) == 0:
			syr_position = 0
			print("Cannot move past 0")
		if count_start > 5:
			SYRINGE_NEUTRAL = SYRINGE_NEUTRAL - 0.25
			count_start = 0
		time.sleep(2)
	SYRINGE_NEUTRAL = SYRINGE_NEUTRAL + 0.1

	stable_count = 0 #number of measurements in window

	while ((stable_count <= 10) & (dive_time < 120)):
		time.sleep(0.4)
		sensor.read(ms5837.OSR_256)
		pressure = sensor.pressure(ms5837.UNITS_kPa)
		pressure = round(pressure, 2)
		depth = sensor.depth()
		# output depth
		depth_diff = depth - target_depth
		now_time = datetime.datetime.now()
		dive_time = int((now_time - start_time).total_seconds())
		print("start time = ", start_time, "now time = ", now_time,  "dive_time = ", dive_time, file=file)	
#		readings(dive_time, pressure, depth)
		if dive_time >= (5 * s5_periods):
			on_target=0
			if -0.5 < depth_diff < 0.5:
				on_target = 1
				stable_count+=1
			print("dive time 5s = ", dive_time, file=file)
			readings(dive_time, pressure, depth)
			s5_periods+=1
		print("current depth: ", depth)
		print("target depth: ", target_depth)
		if GPIO.input(TOP_SWITCH) == 0:
			syr_position = 0
			print("Cannot move past 0")
	#if lower than target depth
		if (0.05 > (depth_diff) > 0):
			print("depth diff: ", depth_diff)
			Go_To_Pos(SYRINGE_NEUTRAL + 01.5)
		if (0.15 > (depth_diff) > 0.05):
			print("depth diff: ", depth_diff)
			Go_To_Pos(SYRINGE_NEUTRAL + 02.2)
		if (0.5 > (depth_diff) > 0.15):
			print("depth diff: ", depth_diff)
			Go_To_Pos(SYRINGE_NEUTRAL + 3.2)
		if (0.75 > (depth_diff) > 0.5):
			print("depth diff: ", depth_diff)
			Go_To_Pos(SYRINGE_NEUTRAL + 4.75)
		if ((depth_diff) > 0.75):
			print("depth diff: ", depth_diff)
			Go_To_Pos(SYRINGE_NEUTRAL + 6.75)
	#if reached target
		if (depth_diff == 0) or (-0.10 < depth_diff < 0.10):
			print("depth diff: ", depth_diff)
			print("maintaining depth: ", depth)
	#if higher than target depth
		if (-0.3 <= (depth_diff) < 0):
			print("depth diff: ", depth_diff)
			Go_To_Pos(SYRINGE_NEUTRAL - 0.35)
		if (-0.5 <= (depth_diff) < -0.3):
			print("depth diff: ", depth_diff)
			Go_To_Pos(SYRINGE_NEUTRAL - 0.6)
		if ((depth_diff) <= -0.5):
			print("depth diff: ", depth_diff)
			Go_To_Pos(SYRINGE_NEUTRAL - 0.95)
	Go_To_Pos(SYRINGE_MAX-1)


def init_html():

        #ORIGINAL CODE FROM 2023-24 below
	print("Content-type:text/html\r\n\r\n")
	print("")
	print("Hello everyone")
	print("""<p><a href="http://192.168.42.10/index.php">Go_Back_to_Data</a></p>""")

def find_neutral():
	global syr_position
	global SYRINGE_NEUTRAL
	global position
	global start_depth

	sensor.read(ms5837.OSR_256)
	start_depth = sensor.depth() * 100

	depth = sensor.depth() * 100
	while((depth - start_depth) < 5): #was 2
		if (GPIO.input(TOP_SWITCH) == 0):
			Set_Servo(SERVO_CHANNEL, SERVO_OFF)
			return

		print("Finding neutral from ", position)
		Set_Servo(SERVO_CHANNEL, SERVO_UP) 
		time.sleep(.25 * SEC_PER_CLICK)
		position-=0.25
		Set_Servo(SERVO_CHANNEL, SERVO_OFF) 
		time.sleep(0.5)
		sensor.read(ms5837.OSR_256)
		depth = sensor.depth() * 100
		print("Finding Neutral - ", depth, "cm")
	SYRINGE_NEUTRAL = position - 0.15 #was -.45
	Go_To_Pos(SYRINGE_NEUTRAL)
	print("Neutal syringe is ", position)

	
def readings(num_secs, pressure, depth):
#	k = open("collect_data.txt" , 'w')
#	k = open("collect_all_data.txt" , 'w')
#	second_time = 0
#	counter = 0
	#print("RN08" + " : " + (str(num_secs)) + " : " + (str(pressure)) + " : " + (str(depth)), file=k)
	#print("RN08" + " : " + (str(num_secs)) + " : " + (str(pressure)) + " : " + (str(depth)))
	with open(txt_file, "w") as file:
		fd = file.fileno()
		fcntl.flock(fd, fcntl.LOCK_EX)
		file.write("RN08" + " : " + (str(num_secs)) + " : " + (str(pressure)) + " : " + (str(depth)))
		print("RN08" + " : " + (str(num_secs)) + " : " + (str(pressure)) + " : " + (str(depth)))
		fcntl.flock(fd,fcntl.LOCK_UN)

def sample_readings(counter):
#	k = open("collect_data.txt" , 'w')
#	k = open("collect_all_data.txt" , 'w')
	global second_time
	startup_success = 0
#	second_time = 0
#	counter = 0
	while startup_success == 0:
		try:
			startup()
		except:
			print("                 ***FAILED STARTUP***")
			pass
		else:
			startup_success = 1
			time.sleep(0.5)

	while (second_time/5) < counter or (second_time/5) == 0:
		try:
			sensor.read(ms5837.OSR_256)

		except:
			print("                 ***FAILED READING***")
			continue
		readings = sensor.pressure(ms5837.UNITS_kPa)
		readings = round(readings, 2)
	
		depth = sensor.depth()
		depth = round(depth + 0.43, 2)

		try:
			sensor.read(ms5837.OSR_256)

		except:
			print("                 ***FAILED READING***")
			continue
		depth2 = sensor.depth() + 0.43

		now = datetime.datetime.now()
		if abs(depth2 - depth) > 0.35:
			continue

		if depth >= 5 or depth <-0.35:
			continue
		depth =  depth * -1
		second_time = second_time + 5
#		print("second time: ", second_time)
#		print("second time / 5", second_time/5)
		print("RN08" + " : " + (str(second_time)) + " : " + (str(readings)) + " : " + (str(depth)), file=k)
		print("RN08" + " : " + (str(second_time)) + " : " + (str(readings)) + " : " + (str(depth)))
		time.sleep(5)


def get_battery():
	pot = MCP3008(0)
	new_val = pot.value*6.6
	print(new_val)
	#b = open("battery_check.txt", 'w')
	print((new_val), file=b)

def runbe():
	form = cgi.FieldStorage()
	if "dive" in form:
		global SYRINGE_MAX
		global position
		position = SYRINGE_MAX
		Go_To_Pos(SYRINGE_NEUTRAL+5)
		find_neutral()
		Go_To_Depth(2.5)
	if "battery" in form:
		get_battery()
	if "sample" in form:
		for i in range(3):
			sample_readings(3)
	if "calibrate" in form:
#		global SYRINGE_MAX
		Go_To_Top()
		Go_To_Pos(SYRINGE_MAX)

if __name__ == "__main__":
	try:
		init_html()
		startup()
		runbe()

	except Exception as e:
		crash=["Error on line {}".format(sys.exc_info()[-1].tb_lineno),"/n",e]
		print(crash)
		timeX=str(time.time())
		with open ("/home/robotics/BE2425/crash/"+timeX+".txt","w") as crashlog:
			for i in crash:
				i=str(i)
				crashlog.write(i)
			crashlog.write("flushing...")
			crashlog.flush()
			os.fsync(crashlog.fileno())
			crashlog.close()