# # I have commented out stuff that has to do with syringe stuff and that's where I need to change to make it a pump
# # I commented out this whole section because I made a whole new file that has this code adjusted
# #collec!/usr/bin/python
# import sys
# import signal
# import RPi.GPIO as GPIO
# import time
# from simple_pid import PID
# import ms5837
# import smbus
# import datetime
# import threading
# import os

# global target_position
# global position

# IN1 = 17
# IN2 = 18
# EN = 28
# TOP_SWITCH = 22

# SEC_PER_UNIT = 0.5

# #position tracking
# position = 0


# # TOP_SWITCH = 21
# # ROTATE_SWITCH = 6
# # SERVO_OFF = 150
# # SERVO_UP = 200
# # SERVO_DOWN = 100

# # SYRINGE_NEUTRAL = 14	 #was 25 #was 16	
# # SYRINGE_MAX = 37 #was 44 #was 30

# # SEC_PER_CLICK = 2.384615

# # SERVO_CHANNEL = 0

# start_depth = 0

# p = -0.001 #was -0.02
# i = 0 #was -0.00015
# d = 0

# GPIO.setmode(GPIO.BCM)
# GPIO.setup(IN1, GPIO.OUT)
# GPIO.setup(IN2, GPIO.OUT)
# GPIO.setup(EN, GPIO.OUT)
# #GPIO.setup(12, GPIO.OUT)
# #GPIO.setup(ROTATE_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# GPIO.setup(TOP_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# #p = GPIO.PWM(12, 50) # channel 12, 50Hz
# #p.start(SERVO_OFF) #motor_off

# sensor = ms5837.MS5837_02BA(1)

# # Stop Servo
# #p.start(SERVO_OFF)
# time.sleep(1)
# file2 = open("Depth.txt", "w")
# #k = open("collect_data.txt", "w")

# pwm = GPIO.PWM(EN, 1000)
# pwm.start(0)

# # def handle_signal(signum, frame):
# #     Set_Servo(SERVO_CHANNEL, SERVO_OFF)
# #     file2.close()
# #     k.close()
# #     print("bye")
# #     sys.exit(0)

# # Register the handler for common termination signals
# signal.signal(signal.SIGTERM, handle_signal)  # kill
# signal.signal(signal.SIGINT, handle_signal)   # Ctrl+C


# # # Turn on servo with servoblaster
# # def Set_Servo(channel, pulse_width):
# #     with open('/dev/servoblaster', 'w') as f:
# #         f.write(f"{channel}={pulse_width}\n")

# def startup():
# 	# Set_Servo(SERVO_CHANNEL, SERVO_OFF) 
# 	sensor.init()
# 	time.sleep(1)
# 	sensor.read(ms5837.OSR_256)
# 	sensor.setFluidDensity(ms5837.DENSITY_FRESHWATER)


# # def Go_To_Top():
# # #code to turn on servo and fill syringe w water and stop it when switch (pin 20) is activated
# #         global position
# #         print("GoToTop")
# #         count=0
# #         if (GPIO.input(TOP_SWITCH) == 0):
# #                 Set_Servo(SERVO_CHANNEL, SERVO_OFF)
# #                 position=0
# #                 return

# #         while (GPIO.input(TOP_SWITCH) == 1):
# # #               print("rotate switch: ", GPIO.input(21))
# #                 Set_Servo(SERVO_CHANNEL, SERVO_UP) 
# # #p.ChangeDutyCycle(SERVO_UP) #syringe up
# #                 if (GPIO.input(ROTATE_SWITCH) == 0):
# #                         count+=1
# #                         print("Count = ", count)
# #                         while(GPIO.input(ROTATE_SWITCH) == 0):
# #                                 if (GPIO.input(TOP_SWITCH) == 0):
# #                                         break
# #                 time.sleep(0.5)
# #         Set_Servo(SERVO_CHANNEL, SERVO_OFF) 
# # #       p.ChangeDutyCycle(SERVO_OFF)
# #         position = 0
# #         print("top reached")

# # def Go_To_Pos(target_position):
# # #code to turn on servo and fill syringe w water and stop it when switch (pin 20) is activated
# #         global position
# #         print("starting position = ", position)
# #         print("going to ", target_position)
# # 	#@pos_part = target_position - int(target_position)

# #         #if (GPIO.input(TOP_SWITCH) == 0):
# #         #        Set_Servo(SERVO_CHANNEL, SERVO_OFF)
# #         #        position=0
# #         #        return
# #         if target_position < 0:
# #                target_position = 0
# #         if target_position > SYRINGE_MAX:
# #                 target_position = SYRINGE_MAX
# #         move_amount = target_position - position
# #         if target_position == 0:
# #                 Go_To_Top()
# #                 return
# #         if move_amount > 0:
# #                 #target_position = int(target_position)
# #                 Set_Servo(SERVO_CHANNEL, SERVO_DOWN) 
# # #                time.sleep(0.25)
# # #                p.ChangeDutyCycle(SERVO_DOWN)
# #                 while (move_amount >= 1):
# #                         position=int(position)
# #                         if (GPIO.input(ROTATE_SWITCH) == 0):  #wait for click
# #                                 move_amount-=1 #reduce remaining amount to move by 1 rotation
# #                                 position+=1
# #                                 print("New Position = ", position, "Move Amount = ", move_amount)
# #                                 while(GPIO.input(ROTATE_SWITCH) == 0): #wait for unclick
# #                                        time.sleep(0.2)
# #                         time.sleep(0.3)
# #                 Set_Servo(SERVO_CHANNEL, SERVO_OFF)  
# #                 #Accounting for pid decimal

# #                 pos_part=(target_position - position)
# #                 if (pos_part != 0):
# #                      print("pos_part, = ", pos_part)
# #                      time_part = pos_part * SEC_PER_CLICK
# #                      Set_Servo(SERVO_CHANNEL, SERVO_DOWN)
# #                      time.sleep(time_part)
# #                      Set_Servo(SERVO_CHANNEL, SERVO_OFF)
# #                      position+=pos_part
# # #               p.ChangeDutyCycle(SERVO_OFF)

# #         if move_amount < 0:
# #                 if (GPIO.input(TOP_SWITCH) == 0):
# #                    Set_Servo(SERVO_CHANNEL, SERVO_OFF)
# #                    return

# #                 print("Move Amount less than 0: ", move_amount)
# #                 #target_position = int(target_position)
# #                 Set_Servo(SERVO_CHANNEL, SERVO_UP) 
# #                 time.sleep(0.25)
# # #               p.ChangeDutyCycle(SERVO_UP)
# #                 while (move_amount <= -1):
# #                         position=int(position)
# #                         if (GPIO.input(ROTATE_SWITCH) == 0):
# #                                 move_amount += 1
# #                                 position-=1
# #                                 print("New Position = ", position, "Move Amount = ", move_amount)
# #                                 while(GPIO.input(ROTATE_SWITCH) == 0):
# #                                         time.sleep(0.2)
# #                         time.sleep(0.3)
# #                 Set_Servo(SERVO_CHANNEL, SERVO_OFF) 

# #                 if (GPIO.input(TOP_SWITCH) == 0):
# #                     Set_Servo(SERVO_CHANNEL, SERVO_OFF) 
# #                     return

# # # how much micro movement
# #                 pos_part=(position - target_position)
# #                 if (pos_part != 0):
# #                    #pos_part = 1-pos_part
# #                    print("pos_part, = ", pos_part)
# #                    Set_Servo(SERVO_CHANNEL, SERVO_UP)
# #                    time.sleep(abs(pos_part * SEC_PER_CLICK))
# #                    Set_Servo(SERVO_CHANNEL, SERVO_OFF)
# #                    position-=pos_part
# # #                p.ChangeDutyCycle(SERVO_OFF)
# #         print("position reached: ", position)
# #         return

# def Output_Info(depth, dive_time, on_target, s5_periods):
# 	print("On-target? ", on_target)
# 	with open("/home/robotics/BE2425/collect_mg.txt","w") as k:
# 		print("RN08" + " : " + (str(depth)) + ":" + dive_time + " : " + on_target + " : " + s5_periods + "\n", file=k)
# 		print("RN08" + " : " + (str(depth)) + ":" + dive_time + " : " + on_target + " : " + s5_periods + "\n")
# 		k.flush()
# 	os.fsync(k.fileno())


# def Go_To_Depth(target_depth):
# 	global file2
# 	global position
# 	global target_position
# 	global SYRINGE_NEUTRAL
# 	start_time = datetime.datetime.now()
	
# 	#sensor.read(ms5837.OSR_256)
# 	#depth = sensor.depth()


# 	sensor.read(ms5837.OSR_256)
# 	depth = sensor.depth()
# 	start_depth = depth
# 	count_start=0
# 	s5_periods=1
# 	on_target=0

# 	while (depth - start_depth < 0.05):
# 		dive_time = (datetime.datetime.now() - start_time).total_seconds()
# 		if int(dive_time) == 5 * s5_periods:
# 			s5_periods+=1
# 			Output_Info(depth, dive_time, on_target, s5_periods)
# 		# Go_To_Pos(SYRINGE_NEUTRAL - 0.25)
# 		count_start+=1
# 		sensor.read(ms5837.OSR_256)
# 		depth = sensor.depth()
# 		print("sd - current depth: ", start_depth)
# 		print("sd - start depth: ", depth)
# 		print("sd - start depth: ", start_depth, file=file2)
# 		# print("sd - current depth: ", depth, file=file2)
# 		# if TOP_SWITCH == 0:
# 		# 	# syr_position = 0
# 		# 	print("Cannot move past 0")
# 		# if count_start > 5:
# 		# 	# SYRINGE_NEUTRAL = SYRINGE_NEUTRAL - 0.25
# 		# 	count_start = 0
# 		# time.sleep(2)

# 	stable_count = 0

# 	while (stable_count <= 10):
# 		sensor.read(ms5837.OSR_256)
# 		pressure = sensor.pressure(ms5837.UNITS_kPa)
# 		pressure = round(pressure, 2)
# 		depth = sensor.depth()
# 		# output depth
# 		depth_diff = depth - target_depth
# 		dive_time = (datetime.datetime.now() - start_time).total_seconds()
# 		if int(dive_time) == 5 * s5_periods:
# 			s5_periods+=1
# 			on_target=0
# 			if -0.5 < depth_diff < 0.5:
# 				on_target = 1
# 				stable_count+=1
# 			Output_Info(depth, dive_time, on_target, s5_periods)
# 		print("current depth: ", depth)
# 		print("target depth: ", target_depth)
# 		print("target depth: ", target_depth, file=file2)
# 		print("current depth: ", depth, file=file2)
# 		if TOP_SWITCH == 0:
# 			syr_position = 0
# 			print("Cannot move past 0")
# 	#if lower than target depth
# 		if (0.05 > (depth_diff) > 0):
# 			print("depth diff: ", depth_diff)
# 			print("depth diff: ", depth_diff, file=file2)
# 			# Go_To_Pos(SYRINGE_NEUTRAL + 0.5)
# 			# print("going to downwards position: ", SYRINGE_NEUTRAL + 0.5)
# 			# print("going to downwards position: ", SYRINGE_NEUTRAL + 0.5, file=file2)
# 		if (0.15 > (depth_diff) > 0.05):
# 			print("depth diff: ", depth_diff)
# 			print("depth diff: ", depth_diff, file=file2)
# 			# Go_To_Pos(SYRINGE_NEUTRAL + 0.8)
# 			# print("going to downwards position: ", SYRINGE_NEUTRAL + 0.8)
# 			# print("going to downwards position: ", SYRINGE_NEUTRAL + 0.8, file=file2)
# 		if (0.5 > (depth_diff) > 0.15):
# 			print("depth diff: ", depth_diff)
# 			print("depth diff: ", depth_diff, file=file2)
# 			# Go_To_Pos(SYRINGE_NEUTRAL + 1.2)
# 			# print("going to downwards position: ", SYRINGE_NEUTRAL + 1.2)
# 			# print("going to downwards position: ", SYRINGE_NEUTRAL + 1.2, file=file2)
# 		if (0.75 > (depth_diff) > 0.5):
# 			print("depth diff: ", depth_diff)
# 			print("depth diff: ", depth_diff, file=file2)
# 			# Go_To_Pos(SYRINGE_NEUTRAL + 1.75)
# 			# print("going to downwards position: ", SYRINGE_NEUTRAL + 1.75)
# 			# print("going to downwards position: ", SYRINGE_NEUTRAL + 1.75, file=file2)				
# 		if ((depth_diff) > 0.75):
# 			print("depth diff: ", depth_diff)
# 			print("depth diff: ", depth_diff, file=file2)
# 			# Go_To_Pos(SYRINGE_NEUTRAL + 2.75)
# 			# print("going to downwards position: ", SYRINGE_NEUTRAL + 3.5)
# 			# print("going to downwards position: ", SYRINGE_NEUTRAL + 21.75, file=file2)				
# 	#if reached target
# 		if (depth_diff == 0) or (-0.10 < depth_diff < 0.10):
# 			print("depth diff: ", depth_diff)
# 			print("depth diff: ", depth_diff, file=file2)
# 			print("maintaining depth: ", depth)
# 			#print("maintaining depth: ", current_depth, file2)
# 	#if higher than target depth
# 		if (-0.3 <= (depth_diff) < 0):
# 			print("depth diff: ", depth_diff)
# 			print("depth diff: ", depth_diff, file=file2)
# 			# Go_To_Pos(SYRINGE_NEUTRAL - 0.35)
# 			# print("going to upwards position: ", SYRINGE_NEUTRAL - 0.35)
# 			# print("going to upwards position: ", SYRINGE_NEUTRAL - 0.35, file=file2)
# 		if (-0.5 <= (depth_diff) < -0.3):
# 			print("depth diff: ", depth_diff)
# 			print("depth diff: ", depth_diff, file=file2)
# 			# Go_To_Pos(SYRINGE_NEUTRAL - 0.6)
# 			# print("going to upwards position: ", SYRINGE_NEUTRAL - 0.6)
# 			# print("going to upwards position: ", SYRINGE_NEUTRAL - 0.6, file=file2)
# 		if ((depth_diff) <= -0.5):
# 			print("depth diff: ", depth_diff)
# 			print("depth diff: ", depth_diff, file=file2)
# 			# Go_To_Pos(SYRINGE_NEUTRAL - 0.95)
# 			# print("going to upwards position: ", SYRINGE_NEUTRAL - 0.95)
# 			# print("going to upwards position: ", SYRINGE_NEUTRAL - 0.95, file=file2)
# 		file2.write("flushing ...")
# 		file2.flush()
# 		os.fsync(file2.fileno())
# 	# Go_To_Pos(SYRINGE_MAX - 5)


# def init_html():

#         #ORIGINAL CODE FROM 2023-24 below
#         print("Content-type:text/html\r\n\r\n")
#         print("")
#         print("Hello everyone")
#         print("""<p><a href="http://192.168.42.10/index.php">Go_Back_to_Data</a></p>""")

# def find_neutral():
# 	# global syr_position
# 	# global SYRINGE_NEUTRAL
# 	global position
# 	global start_depth

# 	sensor.read(ms5837.OSR_256)
# 	start_depth = sensor.depth() * 100

# 	# depth = sensor.depth() * 100
# 	# while((depth - start_depth) < 5): #was 2
# 	# 	if (GPIO.input(TOP_SWITCH) == 0):
# 	# 		Set_Servo(SERVO_CHANNEL, SERVO_OFF)
# 	# 		return

# 	# 	print("Finding neutral from ", position)
# 	# 	Set_Servo(SERVO_CHANNEL, SERVO_UP) 
# 	# 	time.sleep(.25 * SEC_PER_CLICK)
# 	# 	position-=0.25
# 	# 	Set_Servo(SERVO_CHANNEL, SERVO_OFF) 
# 	# 	time.sleep(0.5)
# 	# 	sensor.read(ms5837.OSR_256)
# 	# 	depth = sensor.depth() * 100
# 	# 	print("Finding Neutral - ", depth, "cm")
# 	# SYRINGE_NEUTRAL = position - 0.15 #was -.45
# 	# Go_To_Pos(SYRINGE_NEUTRAL)
# 	# print("Neutal syringe is ", position)
# 	# print("Neutral syringe is: ", position, file=file2)
# 	# #syr_position = SYRINGE_NEUTRAL



# if __name__ == "__main__":
# 	try:
# 		with open("/home/robotics/BE2425/collect_mg.txt","w") as k:
# 			print("STARTINGRN08")
# 			print("STARTING", file=k)
# 			k.flush()
# 		init_html()
# 		startup()
# #REMOVE THIS IF AND THE STUFF INSIDE FOR COMPETITION
# 		if (sys.argv[1]=="bottom"):
# 			# position = SYRINGE_MAX
# 			# Go_To_Pos(SYRINGE_NEUTRAL+5)
# 			find_neutral()
# 			Go_To_Depth(1.5)
# 		else:
# 			# Go_To_Top()
# 			# Go_To_Pos(SYRINGE_MAX)
# 			# inp = input("Press Enter to Continue")
# 			# Go_To_Pos(SYRINGE_NEUTRAL+5)
# 			find_neutral()
# 			inp = input("Press Enter to Continue")
# 			Go_To_Depth(1)
# 		file2.close()
# 		GPIO.cleanup()

# 	except Exception as e:
# 		crash=["Error on line {}".format(sys.exc_info()[-1].tb_lineno),"\n",e]
# 		print(crash)
# 		timeX=str(time.time())
# 		with open("/home/robotics/BE2425/crash/"+timeX+".txt","w") as crashlog:
# 			for i in crash:
# 				i=str(i)
# 				crashlog.write(i)
# 			crashlog.write("flushing ...")
# 			crashlog.flush()
# 			os.fsync(crashlog.fileno())
# 			crashlog.close()