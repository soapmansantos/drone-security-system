import pygame, sys, math

class Environment():
	def __init__(self, map_dimensions):
		pygame.init()
		self.point_cloud = []
		self.map_img = pygame.image.load("maps/map_1.png")
		self.mapw, self.maph = map_dimensions
		self.map_window_name = "MAP"
		pygame.display.set_caption(self.map_window_name)
		self.map = pygame.display.set_mode((self.mapw, self.maph))
		self.map.blit(self.map_img, (0, 0))

	def ad2pos(self, distance, angle, robot_pos):
		x = distance * math.cos(angle) + robot_pos[0]
		y = -distance * math.sin(angle) + robot_pos[1]

		return int(x), int(y)

	def data_storage(self, data):
		print(len(self.point_cloud))

		for element in data:
			point = self.ad2pos(element[0], element[1], element[2])
			if point not in self.point_cloud:
				self.point_cloud.append(point)

	def show_sensor_data(self):
		self.infomap = self.map.copy()
		for point in self.point_cloud:
			self.infomap.set_at((int(point[0]), int(point[1])) , (255, 0, 0))
