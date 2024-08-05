import sys, os
import numpy as np
import serial
#srl = serial.Serial("/dev/ttyACM0", 9600)
import serial


def get_sensor_data(sr):
	"""
	sr is the object of the Serial class, used to 
	read the sensor values of the proximity sensor
	from the serial monitor
	"""
	data = sr.readline() #read sensor data
	data.decode() #converts value from byte to string
	data = float(data[0:4]) #convert to float

	return data



if __name__ == "__main__":
	while True:
		print(get_sensor_data(srl))