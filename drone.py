import sys, pygame
import cv2
import numpy as np
import collections
import math, random
import time, datetime
import serial
from djitellopy import tello
from map import map_
from path import main as path
from obstacles import proximity_sensor as proximity
from threats import follow_threat as threat
from manual_control import key_press_module as kp
from manual_control import manual_control as mc
 



class Drone:
	def __init__(self, area):
		self.drone = tello.Tello() #drone object from tello api
		self.area = area #dimensions of the area the drone travels around
		self.screen = [500, 500] #dimensions of the screen to represent the map
		self.dims = [self.area[0]//10, self.area[1]//10] #dimensions of the map
		self.start = (5, 5) #start position of path
		self.end = (150, 200) #end position of path

		#create object of Map class (polymorphism)
		self.map = map_.Map(self.dims, self.screen, self.area)
		#create manual control object and set the keyboards to control drone
		self.mc = mc.ManualControl([["d", "a"], ["w", "s"], ["UP", "DOWN"], ["RIGHT", "LEFT"]], 50, self.drone)
		#create object of Threat class
		self.threat = threat.Threat()
		#use pyserial to connect to microcontroller
		#self.sr = serial.Serial("/dev/ttyACM0", 9600)

		np.savetxt("map/map.txt", self.map.map, delimiter = ",", fmt = "%i") #clear all obstacles
		path.main(self.start, self.end, self.dims, self.screen) #create initial path

		self.connected = False #connected to drone
		self.takeoff = False #drone has taken off
		self.key_control = False #drone is being controlled with keys

		self.speed = 100 #speed of drone
		self.angle = 0 #angle it is following

		#velocity commands to control drone
		#forward/backward speed
		self.fspeed = 0
		#left/right speed
		self.lr_speed = 0
		#yaw (angular speed)
		self.yaw = 0
		#up/down speed
		self.ud_speed = 0

		#time it will take to travel from one node to the next one
		self.time = 0
		#time when drone is at a new node
		self.start = 0
		#time when travelling between nodes
		self.curr = 0 

		self.node = [0, 0]
		self.new_node = [0, 0]
		#whether drone has reached the next node or not
		self.at_node = True


		#checks if a new obstacle has been detected
		self.new_obs = False

		self.is_threat = False #whether or not there is a threat
		self.threat_timer = 0

		self.ui_screen = pygame.display.set_mode((600, 400))
		self.map.get_bezier_curve(degree=3)

		#depth_map.load_model()


	def connect_drone(self):
		"""
		Connect to the drone usings the .connect()
		method from the DJI Tello API
		"""
		if not self.connected:		
			self.drone.connect() #connect drone
			time.sleep(0.1)

			#print battery to check if it needs charging
			print(self.drone.get_battery())

			#activate stream to be able to retrieve camera feed
			self.drone.streamon()

			#time.sleep(0.5)
			self.connected = True #set connected status to True

			return self.drone
		else:
			return None



	def get_frame(self):
		"""
		Gets the drone's camera feed using
		Tello class method from api
		"""
		return self.drone.get_frame_read().frame



	def take_off(self):
		"""
		Makes drone take off and stabilize
		automatically
		"""
		if not self.takeoff:
			self.drone.takeoff()
			self.takeoff = True

			#delay to stabilize drone
			time.sleep(5)

		return self.takeoff



	def land(self):
		"""
		Makes drone land safely using
		integrated sensor at the bottom
		"""
		if self.takeoff:
			self.drone.land()
			self.takeoff = False


	
	def manual_control(self):
		"""
		Allows user to control the drone with
		their keyboard using "WASD" and the
		arrows
		"""
		#If user has pressed the manual control button
		#on the user interface
		if self.key_control:
			#parameters for mapping the drone's position on
			#a separate screen
			fvel = 12 #forward velocity
			avel = 360/10 #angular velocity
			interval = 0.2
			#'interval' accounts for the slower speed in real life

			#initalise the key press module to be able to identify key presses
			kp.init(self.ui_screen)
			#get the key presses of the key controls
			self.mc.get_key_presses()
			self.mc.get_img()

			#get velocity commands according to the key presses
			dirs = self.mc.get_vel()
			self.lr_speed = dirs[0]
			self.fspeed = dirs[1]
			self.ud_speed = dirs[2]
			self.yaw = dirs[3]

			#update the drone's position in the screen by using the mapping constants
			self.mc.update_pos(self.mc.vel_converter(self.mc.velocity), fvel, avel, interval)
			#draw the calculated position
			self.mc.draw_points()

			return self.mc.velocity



	def select_waypoint(self):
		"""
		Selects a new point in the map for the drone to
		follow once the previous one has been reached

		Points around the drone's position at the same distance
		are calculated, forming a circle

		One of these points is chosen randomly as the next
		waypoint
		"""
		#radius is set as half the map's dimensions
		radius = self.dims[0]//2

		#points of circle are formed around the drone's position
		points = [(int(math.cos(i)*radius) + self.map.pos[0], int(math.sin(i)*radius) + self.map.pos[1]) for i in range(1, 360, 4)]

		#points of circle that are outside the map's dimensions and are at an obstacle
		points = [i for i in points if (i[0] < self.dims[0] and i[0] > 0 and i[1] < self.dims[1] and i[1] > 0 and self.map.map[i[1]][i[0]] != 2)]
		#select point in circle randomly
		self.end = random.choice(points)

		#turn map position into screen position to use in path planning
		self.end = (int((self.end[0]/self.dims[0])*self.screen[0]), int((self.end[1]/self.dims[1])*self.screen[1]))
		
		return self.end




	def redo_path(self):
		"""
		A new path is found from the drone's current position to
		the current end position by running the path planning
		algorithm and getting the bézier curve of the path
		"""
		#get new path (taking into account any obstacles)
		path.main((round(self.map.x), round(self.map.y)), self.end, self.dims, self.screen)
		#update path
		self.map.update_path()
		self.map.curve = []
		#get bézier curve of path
		self.map.get_bezier_curve(degree=3)




	def handle_threat(self):
		"""
		Checks if there are any threats detected by the drone's
		camera

		If there is a threat, passes velocity directions to the
		drone to follow the threat and records the threat and 
		stores the video

		While following, the drone's position is also updated
		in the map
		"""
		#get the frame captured by the drone
		img = self.get_frame()

		#get the distance and angle to threat
		#get the forwards/backward velocity command to follow the drone
		distance, angle, self.fspeed = self.threat.follow(img, 35, 40)

		#if there is a threat, record the video
		self.threat.record_video(self.is_threat, img)

		#the threat timer is the time after a threat has stopped being detected
		#used to avoid saving multiple videos and following the path too early and miss the threat
		if self.threat_timer >= 50:
			#cv2.destroyWindow("threat")
			#path has to be done again, since position has changed
			self.redo_path()
			#store the video that has been recorded
			self.threat.store_video((img.shape[1], img.shape[0]))
			self.is_threat = False


		if self.is_threat:
			#the camera's feed is shown with text indicating the user that a threat is being detected
			image = cv2.putText(img, "Threat detected!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)
			#cv2.imshow("threat", image)


		if self.threat.is_threat: #checks if a threat is detected
			self.is_threat = True

			#get velocity commands for the yaw (angle) and the up/down speed
			self.yaw, self.ud_speed = self.threat.vector(img)
			#update the angle of the drone in the map
			self.map.angle += angle

			self.threat_timer = 0

			#map drone's position as it follows the threat
			self.map_threat_following(self.fspeed, angle)
			#map the threat
			self.map_threat(distance, angle)

			return True

		else:

			if self.is_threat:
				#set all velocity commands to 0 if no threat is being detected
				self.yaw = self.ud_speed = self.fspeed = 0
				self.threat_timer += 1

			return False




	def map_threat(self, distance, angle):
		#map the threat at the distance and angle to the threat
		self.map.add_obs(distance, angle, error=4)



	def map_threat_following(self, speed_cmd, angle):
		"""
		Maps the drone's position while following a threat
		in the environment
		"""
		#convert speed command to speed in the map
		speed = speed_cmd * (39/50) * (self.dims[0]/self.area[0]) * (self.screen[0]/self.area[0]) * (117/150) * 1.07

		#update drone's position in the map
		self.map.x += math.cos(self.map.angle)*speed
		self.map.y += math.sin(self.map.angle)*speed

		#convert position from screen to map (dims)
		self.map.pos = self.map.get_pos(self.map.x, self.map.y)
		#self.map.points.append(self.map.pos)




	def map_obs(self):
		img = self.get_frame()
		dist, ang = depth_map.main(img)


		if (dist, ang) != (None, None):
			print("Add obstacle.")	
			self.map.add_obs(dist, ang, error=2)




	def proximity_obstacle(self, error):
		"""
		Gets the sensor values from the proximity sensor
		and converts them to their corresponding distance
		If value is less than a specific threshold, then
		it means the sensor detected an obstacle, and it 
		is avoided and mapped
		"""

		#get sensor data
		sensor_data = proximity.get_sensor_data(self.sr)

		#distance multiplier found by manually measuring real distance
		#and using linear regression to find the multiplier to convert
		#sensor values into a distance
		distance_multiplier = (16/235)*10
		threshold = 200


		if sensor_data < threshold:

			self.new_obs = True
			#calculate the distance
			distance = distance_multiplier*sensor_data
			#if sensor value is 0, minimum distance is set to 4cm
			if distance == 0:
				distance = 4

			#obs = map_.Obstacle(self.dims, self.screen, self.area, distance, 0)
			#obs.add_obs(error)

			#obstacle is mapped
			self.map.add_obs(distance, 0, error)
			#collision with obstacle is avoided
			self.avoid_obs(distance=2)


		elif self.new_obs and sensor_data >= 235:
			#if obstacle has been avoided a new path is
			#found that takes into account the obstacle
			self.yaw = 1
			print("Redo path")
			self.redo_path()
			self.new_obs = False






	def avoid_obs(self, distance):
		"""
		Collision with a detected obstacle is
		avoided by rotating the drone
		"""

		#constant to turn angular velocity command into actual angle
		angle_multiplier = (15/36)

		print("ROTATE")
		#rotate drone
		self.yaw = 0
		#update drone's angle in map
		self.angle += math.radians(self.yaw*angle_multiplier)
		self.map.angle += math.radians(self.yaw*angle_multiplier)



	
	def drone_dir(self):
		"""
		Gets the position in the area of the node and the next node
		Synchronises drone movement in real life and movement in the
		map to find the position of the drone in the map
		"""
		try:
			if not self.at_node:
				#if drone is not at a node of the curve
				#the position is of the drone in the
				#map is updated according to the velocity
				#commands (self.fspeed)
				self.map.map_drone(self.map.curve[0], self.map.curve[1], self.at_node, self.time, self.fspeed)
				self.map.draw_map(self.map.pos, (255, 0, 0))

			else:

				if self.at_node:
					#if drone is at a node, then that node
					#is visited, so it is dequeued from
					#the self.map.curve queue
					self.map.curve.pop(0) 

			#the position of the last visited node and the node
			#it is currently going to is turned into a position
			#in real life (in terms of self.area's dimensions)

			node = [(self.map.area[0]/self.map.screen[0]) * self.map.curve[0][0], (self.map.area[1]/self.map.screen[1]) * self.map.curve[0][1]]
			new_node = [(self.map.area[0]/self.map.screen[0]) * self.map.curve[1][0], (self.map.area[1]/self.map.screen[1]) * self.map.curve[1][1]]


			return node, new_node


		except IndexError:
			#if there is IndexError, there are no more nodes
			#to cover in the path, meaning the path is covered
			print("Path covered.")
			#new point to go to is selected
			self.select_waypoint()
			#path is found from drone's position to new waypoint
			self.redo_path()
			#time.sleep(1)

			return (0, 0), (0, 0)




	def show_frame(self):
		#shows the drone's video stream in real time
		image = self.get_frame()
		#resize image
		image = cv2.resize(img, (360, 240))
		#show image
		cv2.imshow("feed", image)
		



	def follow_path(self, n0, n1):
		self.lr_speed = 0
		#get distance in real life between nodes
		distance = math.dist(n0, n1)
		#get angle in real life between nodes
		angle = math.atan2(n1[1]-n0[1], n1[0]-n0[0])


		if self.at_node:
			#if drone is at node, rotate drone so it points towards the next node
			#angle-self.angle is the angle difference between nodes (degree of rotation)
			if (angle - self.angle) < 0:
				#if degree of rotation is negative rotate counter clockwise
				self.drone.rotate_counter_clockwise(int(abs(math.degrees(angle - self.angle))))
			else:
				#if degree of rotation is positive rotate clockwise
				self.drone.rotate_clockwise(int(math.degrees(angle - self.angle)))

			#wait to let rotation fully finish (so velocity
			#commands/processes don't interfere with each other)
			#time.sleep(0.15)

			#set current angle (self.angle) as angle drone is moving in
			self.angle = angle
			#calculate time by using speed = distance / time
			self.time = distance/self.speed
			#start the timer
			self.start = time.time()
			#set self.at_node to False so that drone starts moving towards next node
			self.at_node = False

		else:
			#set second time to calculate the time passed since leaving the node
			self.curr = time.time()

			#if time passed since leaving the node is less than the calculated time,
			#then velocity commands are sent to the drone to go forward at self.speed
			if (self.curr - self.start) <= self.time:
				self.fspeed = (150/117)*self.speed #constant found by manual testing

			else:
				#sets self.at_node to True once it has reached the next node
				#so that it can rotate again and repeat the process
				self.fspeed = 0
				self.at_node = True




	def move(self):
		#moves the drone at the specified velocity commands
		#uses tellopy's API to do so
		self.drone.send_rc_control(int(self.lr_speed), int(self.fspeed), int(self.ud_speed), int(self.yaw))







def main(drone):
	"""
	Input: object of the 'Drone' class

	Main function to run all features of
	the program
	"""

	#connects drone
	if not drone.connected:
		drone.connect_drone()

	if drone.connected:
		#drone takes off
		drone.take_off()

		if drone.takeoff:
			if drone.key_control:
				drone.manual_control()

			else:
				#handle threats
				drone.handle_threat()

				#follows the path
				if not drone.is_threat and not drone.new_obs:
					n0, n1 = drone.drone_dir()
					drone.follow_path(n0, n1)


				#maps and avoids obstacles
				drone.proximity_obstacle(error=2)

			#moves drone
			drone.move()


if __name__ == "__main__":
	#drone.map.bezier_curve_2(drone.map.path)
	#print(drone.map.curve)
	while True:
		break

"""
TO-DO:
Move drone by using send_rc_control command (to check video stream while flying) - use angular velocity knowledge
Get midpoint from node to node to create circle --> DONE
Represent drone's position in map while flying in real time
Add objects to the map while flying by using distance estimation module
Use rc speed control for forward/backward movement (allows using camera and mapping during flight)
Use map's module representation of path (rather than nodes from path planning module)

"""