import ms5837
import smbus
import time
import datetime
import threading

sensor = ms5837.MS5837_02BA()
DEBUG = 1

time.sleep(2)

def startup():
#	print("prep to init")
	sensor.init()
	time.sleep(1)
#	print("prep to read")
	sensor.read(ms5837.OSR_256)
#	print("prep to set density")
	sensor.setFluidDensity(ms5837.DENSITY_FRESHWATER)


# main
startup_success = 0
while startup_success == 0:
	try:
		startup()
	except:
		print("                 ***FAILED STARTUP***")
		pass
	else:
		startup_success = 1
		time.sleep(0.5)

f = open("pressure_test.txt", 'w')

while True:
#	if DEBUG: print("prep to read")
	try:
		sensor.read(ms5837.OSR_256)
	except:
		print("                 ***FAILED READING***")
		continue
#	if DEBUG: print("prep to pressure")
	readings = sensor.pressure(ms5837.UNITS_kPa)
	now = datetime.datetime.now()
#	print(str(readings) + " ,  " + now.strftime("%H:%M:%S"))
#	f = open("pressure_test.txt", 'w') #w is write
#	print(str(readings) + ' , ' + now.strftime("%H:%M:%S"), file=f)
	print(str(now.strftime("%H:%M:%S") + " : " + str(readings) + " kPa"))
	print(str(now.strftime("%H:%M:%S") + " : " + (str(readings)) + " kPa"), file=f)
	time.sleep(5) #was 5

def main():
	startup_success = 0
	while startup_success == 0:
		try:
			startup()
		except:
			print("                 ***FAILED STARTUP***")
			pass
		else:
			startup_success = 1
			time.sleep(0.5)

	f = open("pressure_test.txt", 'w')

	while True:
#	if DEBUG: print("prep to read")
		try:
			sensor.read(ms5837.OSR_256)

		except:
			print("                 ***FAILED READING***")
			continue
#	if DEBUG: print("prep to pressure")
		readings = sensor.pressure(ms5837.UNITS_kPa)
		now = datetime.datetime.now()
#	print(str(readings) + " ,  " + now.strftime("%H:%M:%S"))
#	f = open("pressure_test.txt", 'w') #w is write
#	print(str(readings) + ' , ' + now.strftime("%H:%M:%S"), file=f)
		print(str(now.strftime("%H:%M:%S") + " : " + str(readings) + " kPa"))
		print(str(now.strftime("%H:%M:%S") + " : " + (str(readings)) + " kPa"), file=f)
		time.sleep(5)

main()