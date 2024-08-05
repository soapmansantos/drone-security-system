import pygame, sys, math
import numpy as np


def uncertainty_add(distance, angle, sigma):
	mean = np.array([distance, angle])
	covariance = np.diag(sigma**2)
	distance, angle = np.random.multivariate_normal(mean, covariance)
	distance = max(distance, 0)
	angle = max(angle, 0)
	return [distance, angle]


class Sensor():
	def __init__(self, range_, map_, uncertainty):
		self.range = range_
		self.speed = 4
		self.sigma = np.array([uncertainty[0], uncertainty[1]])
		self.pos = (0, 0)
		self.map = map_
		self.w, self.h = pygame.display.get_surface().get_size()
		self.obstacles = []


	def distance(self, obs_pos):
		return math.sqrt(((obs_pos[0] - self.pos[0])**2) +  ((obs_pos[1] - self.pos[1])**2))

	def sense_obstacles(self):
		data = []
		x1, y1 = self.pos[0], self.pos[1]

		for angle in np.linspace(0, 2*math.pi, 60, False):
			x2, y2 = (x1 + self.range*math.cos(angle), y1 - self.range*math.sin(angle))
			for i in range(0, 100):
				u = i / 100
				x = int(x2*u + x1*(1 - u))
				y = int(y2*u + y1*(1 - u))

				if 0 < x < self.w and 0 < y < self.h:
					colour = self.map.get_at((x, y))
					if (colour[0], colour[1], colour[2]) == (0, 0, 0):
						distance = self.distance((x, y))
						output = uncertainty_add(distance, angle, self.sigma)
						output.append(self.pos)
						data.append(output)
						break

		if len(data) >= 0:
			return data
		else:
			return False 