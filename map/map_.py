"""
Updates virtual map of the environment
Input:
- velocity controls of the drone
- distance from detected objects
Output:
- grid based map marking drone's position
- updated map with obstacles
"""

import cv2
import numpy as np
import math
import collections
import time
from path import main as path
from scipy.interpolate import BPoly
import itertools


def read_path(path):
	"""
	reads nodes of RRT algorithm from path.txt file
	"""
	path_list = []
	f = open(path, "r")
	contents = f.readlines()
	for x in contents:
		i = x.split(",")
		i = [int(i[0]), int(i[1][:-1])]
		path_list.append(i)   

	return path_list



class Map():
	def __init__(self, dims, screen, area):
		self.dims = dims
		self.screen = screen
		self.area = area

		self.path = read_path("path/path.txt") #queue holding nodes of the path
		self.curve = [] #queue holding nodes of the curve

		#set initial position as the position in the first node
		self.x = self.path[0][0]
		self.y = self.path[0][1]
		self.pos = self.get_pos(self.x, self.y)


		#create the map (initially just 0s)
		self.map = np.zeros((dims[0], dims[1]))

		#np array to represent map on the screen
		self.img = np.zeros((self.screen[0], self.screen[1], 3), np.uint8)
		self.obs = [] #holds all the obstacle's positions

		self.speed = 0 #speed of drone in the map
		self.angle = 0 #angle the drone is following in the map




	def update_path(self):
		"""
		Reads new path to follow and stores
		it in the queue self.path
		"""
		self.path = read_path("path/path.txt")

		return self.path



	def get_pos(self, x, y):
		"""
		Input: (x, y) position in screen     
		Output: (x', y') position in map (self.dims)
		"""
		x = math.floor((x/self.screen[0])*self.dims[0])
		y = math.floor((y/self.screen[1])*self.dims[1])

		return [x, y]




	def bezier_curve(self, degree):
		"""
		Smooths out the path found by applying a bezier curve to
		the nodes, making the drone's trajectory more natural to follow

		Input:
		degree --> the rate at which the bezier curve meets a node
		"""
		#split the path into subarrays of length <int>degree (input)

		chunks = [self.path[x:x+degree] for x in range(0, len(self.path), degree)]
		num_points = 4#number of points between <int>degree nodes

		for count, i in enumerate(chunks):
			if count != 0:
				cmn = chunks[count-1][-1]
				chunks[count].insert(0, cmn)

		for c in chunks:
			cp = np.array(c)
			curve = BPoly(cp[:, None, :], [0, 1])

			x = np.linspace(0, 1, num_points)
			points = curve(x)


			for p in points:
				pos = self.get_pos(p[0], p[1])
				self.curve.append((pos[0], pos[1]))
				#self.draw_map(pos, (255, 255, 255))

		for i in self.path:
			self.draw_map(self.get_pos(i[0], i[1]), (255, 0, 255))

		self.curve = list(collections.OrderedDict.fromkeys(self.curve))
		self.curve.insert(0, (self.pos[0], self.pos[1]))

		return points




	def get_bezier_curve(self, degree):
		"""
		Smooths out the path found by applying a bezier curve to
		the nodes, making the drone's trajectory more natural to follow

		Input: degree --> the rate at which the bezier curve meets a node
		Output: connected bézier curves forming a spline of the entire path
		"""

		#separate path's nodes into chunks of length equal to the degree
		chunks = [self.path[x:x+degree] for x in range(0, len(self.path), degree)]


		#create a common node for every chunk so that the bézier curves connect
		#more smoothly, creating a spline
		"""
		for count, i in enumerate(chunks):
			if count != 0:
				cmn = chunks[count-1][-1] #get last element from previous chunk
				chunks[count].insert(0, cmn) #insert last element into current chunk at index 0
		"""


		for c in chunks:
			#create bézier curve for each chunk and join them
			self.bezier_curve_2( [[[i[0]], [i[1]]] for i in c], 2)

		#remove duplicate points in the curve by converting it into a dictionary
		#(dictionaries can't have duplicate keys) and convert back to a list
		self.curve = list(dict.fromkeys(self.curve))

		return self.curve




	def bezier_curve_2(self, points, num_points):
		"""
		Creates bézier curve of the given points
		Creates num_points of points forming the curve
		Uses De Casteljau's algorithm to do so
		"""

		#base case of recursive algorithm:
		#if there is only one set of points,
		#the points represent the curve
		if len(points) == 1:

			#convert points into positions in the map
			for count, p in enumerate(points[0][0]):
				pos = self.get_pos(p, points[0][1][count])
				self.curve.append((pos[0], pos[1]))
				self.draw_map(pos, (255, 255, 255)) #draw curve on map

			for i in self.path:
				#draw original path
				self.draw_map(self.get_pos(i[0], i[1]), (255, 0, 255))

			return self.curve

		else:
			temp = [] #temporary list holding the points in each iteration

			for count, p in enumerate(points):

				if count != len(points)-1:
					#temporary lists holding x and y values for each lerp
					x = []
					y = []

					for i in range(0, num_points+1):
						#calculates lerp value for num_points
						t = i/num_points #scalar multiplier in lerp

						for (x1, x2, y1, y2) in zip(p[0], points[count+1][0], p[1], points[count+1][1]):
							#calculate lerp for each point and the next one
							#so the length of lerps to do each iteration
							#decreases by one
							x.append( self.lerp(x1, x2, t) ) #interpolates x values
							y.append( self.lerp(y1, y2, t) ) #interpolates y values

					temp.append([x, y]) #append x and y values for next iteration

			self.bezier_curve_2(temp, num_points) #recursive step




	def lerp(self, p0, p1, t):
		"""
		Returns the value of the linear interpolation at t
		between p0 and p1 using interpolation formula
		"""
		return ((1-t)*p0) + (t*p1)




	def offset(self, pos, distance):
		"""
		Gets the indices of the neighbouring elements
		of an element at position pos that are at the
		required distance

		Used for uncertainties in obstacle mapping,
		threat mapping and collision avoidance
		"""
		row = pos[0]
		col = pos[1]

		indices = []
		for r in range(row-distance, row+distance+1):
			for c in range(col-distance, col+distance+1):
				# Skip the element itself
				if r == row and c == col:
					continue
				# Check if the element is within the bounds of the array
				if r >= 0 and r < self.map.shape[0] and c >= 0 and c < self.map.shape[1]:
					# Calculate the distance from the element
					d = abs(row - r) + abs(col - c)
					# Check if the distance is equal to the desired distance
					if d == distance:
						indices.append((r, c))

		return indices




	def add_obs(self, distance, angle, error):
		"""
		Calculates position of a detected obstacle at a
		given distance and angle and adds it to the map

		Error accounts for the uncertainty of the measurement
		and drone's position during the flight by setting the
		neighbouring elements as obstacles too
		"""

		#turn distance in cm into distance in relation to the screen's dimensions
		distance = distance * (self.screen[0] / self.area[0])

		#Calculate position of obstacle by using trigonometry
		obs = [int(self.x + (distance*math.cos(self.angle + angle))), int(self.y + (distance*math.sin(self.angle + angle)))]
		obs_pos = self.get_pos(obs[0], obs[1]) #turns position into a position in the map (instead of screen)

		print("Obs pos: ", obs)

		#set neighbour elements at distance of the value error as obstacles
		for d in range(1, error):
			for i in self.offset(obs_pos, d):
				self.map[i[1]][i[0]] = 2 #add obstacle to the map
				self.obs.append(i)
				self.draw_map(i, (0, 255, 0)) #draw obstacle on the screen

		#save map as a text file, with each element separated by a comma ','
		#to be opened by path plannning module to create new path
		np.savetxt("map/map.txt", self.map, delimiter = ",", fmt = "%i")


		return self.obs
	



	def map_drone(self, n1, n2, at_node, time, speed_cmd):
		"""
		Maps the drone's position in the map while it flies

		Input: 
		n1 - last node visited, n2 - next node in queue,
		at_node - boolean value to check if the drone has reached n2
		time - the time it is going to take to get to n2
		speed_cmd - velocity command sent to the drone while flying

		Output:
		Drone's position in the map (updated every iteration)
		"""

		#checks that the drone is moving (not at a node)
		if speed_cmd == 0:
			#if it is rotating, set self.speed to 0 (so self.pos doesn't change)
			self.speed = 0
		else:
			#calculate the distance between the nodes
			#get distance in terms of the size of the screen & map, not area
			distance = math.dist(n1, n2) * (self.dims[0]/self.area[0]) * (self.screen[0]/self.area[0]) * (117/150) * 1.07

			#calculate the speed for which the drone travels that distance
			#in the time required by using formula v = d/t
			self.speed = (distance/time)


		if not at_node:
			#calculate the angle between the nodes by using trigonometry
			self.angle = math.atan2(n2[1]-n1[1], n2[0]-n1[0])

			#get x and y components of self.speed by using trigonometry
			#add the value to the current position in the screen
			self.x += math.cos(self.angle)*self.speed
			self.y += math.sin(self.angle)*self.speed

			#convert (self.x, self.y) position into a position in the map (dims)
			self.pos = self.get_pos(self.x, self.y)

		#set the drone's position in the map as a 1
		self.map[self.pos[1]][self.pos[0]] = 1


		return self.pos

		


	def start_end(self, pos):
		"""
		Gets the start and end positions in the
		screen of a square in the map
		"""

		#use self.dims : self.screen ratio to find positions
		start = (round(self.screen[0]*(pos[0]/self.dims[0])), round(self.screen[1]*(pos[1]/self.dims[1])))
		end = (round(start[0] + (self.screen[0]/self.dims[0])), round(start[1] + (self.screen[1]/self.dims[1])))

		return start, end



	def draw_map(self, point, colour):
		"""
		Represents a point in the map in the screen
		to give a visual representation of the flight
		"""

		#get top left and bottom right positions of rect at
		#position point
		point = self.start_end(point)

		#draw rectangle on self.img of colour --> (b, g, r)
		cv2.rectangle(self.img, point[0], point[1], colour, -1)

		#cv2.imshow("map", self.img)
		#cv2.waitKey(1)



m = Map([100, 100], [500, 500], [1000, 1000])



class Obstacle(Map):

	def __init__(self, dims, screen, area, distance, angle_diff):
		Map.__init__(self, dims, screen, area)
		self.distance = distance
		self.angle_diff = angle_diff


	def add_obs(self, error):
		#self.distance = self.distance * (self.screen[0] / self.area[0])

		obs = [int(self.x + (self.distance*math.cos(self.angle + self.angle_diff))), int(self.y + (self.distance*math.sin(self.angle + self.angle_diff)))]
		obs_pos = self.get_pos(obs[0], obs[1])

		print("Obs pos: ", obs_pos)

		for d in range(1, error):
			for i in self.offset(obs_pos, d):
				self.map[i[1]][i[0]] = 2 
				self.obs.append(i)
				self.draw_map(i, (0, 255, 0))


		return self.obs
		



if __name__ == "__main__":

	while True:
		m.bezier_curve_2(degree=3)

		"""
		face_cascade = cv2.CascadeClassifier("obstacles/resources/face_tracking_file.xml")
		dist = de.main(face_cascade)
		m.add_obs(dist)
		print(dist)
		m.draw_map()
		"""
		






"""
TO-DO:
- Figure out how to read files in distance_estimation module
- Use OpenCV to  detect obstacles and calculate distance to them    
- Update the map using the distance from the drone to the obstacles
- Calculate velocity directions of drone from one node to the other for deployment
- Change path algorithm from RRT to A*?


DONE:
- Represent drone's motion as a square on a grid map
- Start developing the drone_control module for test flight with no obstacles inside room

"""