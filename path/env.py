import pygame, sys, math, time #import modules

class Environment(): #create an environment to represent the nodes and edges of the path found by the RRT class
	def __init__(self, dims, screen, map_location): #initialize variables
		pygame.init()
		pygame.display.set_caption("path")
		self.dims = dims
		self.screen = screen
		self.map_location = map_location #directory of map
		self.map = pygame.display.set_mode((self.screen[0], self.screen[1])) #create window/screen
		#self.map_img = pygame.image.load(f"maps/{map_location}").convert()
		#self.map_img = pygame.transform.scale(self.map_img, (dims[0], dims[1]))
		#self.map.blit(self.map_img, (0, 0))nea
		self.map.fill((255, 255, 255))
		self.pos = []

	def load_map(self, directory):
		"""
		Input: directory of the current map
		Output: a two-dimensional array of the map
		"""
		f = open(directory + ".txt", "r") #open map's directory
		data = f.read() #read contents of map
		f.close()
		data = data.split("\n")
		curr_map = []
		for row in data:
			data_split = row.split(",") #get individual element from the map
			curr_map.append(data_split) #append each element into array as a string
		curr_map = curr_map[:-1] #last line is empty
		
		for row in range(len(curr_map)):
			for i in range(len(curr_map[row])):
				curr_map[row][i] = str((int(curr_map[row][i]))) #nested for loop turns map into a 2d array

		return curr_map


	def update_map(self):
		#map_ = self.load_map(f"map/path/maps/{self.map_location}") #load map
		map_ = self.load_map(f"map/{self.map_location}") 

		#calculate the width and height of one square in the grid map (converted to the screen's size)
		w = self.screen[0]/self.dims[0]
		h = self.screen[1]/self.dims[1]

		for y, row in enumerate(map_):
			for x, tile in enumerate(row):
				if tile == "2": #checks if there are any obstacles in the map (obstacle is represented as a 2)
					#draws a rectangle representing the obstacle, and adding it to the virtual map (self.map)
					pygame.draw.rect(self.map, (0, 0, 0), pygame.Rect(x*w, y*h, w, h))


	def draw_node(self, pos, colour):
		"""
		Input: position and colour of a node
		Output: node is represented in the virtual environment as a circle
		"""
		if pos != None:
			pygame.draw.circle(self.map, colour, pos, 5, 3)


	def draw_edge(self, pos, colour, width):
		"""
		Input: position ((node1.x, node1.y), (node2.x, node2.y)), colour and width of an edge
		Output: edge is represented in the virtual environment as a line connecting two nodes
		"""
		if pos[0] != None and pos[1] != None:
			pygame.draw.line(self.map, colour, pos[0], pos[1], width)


	def def_path(self):
		"""
		Method used for testing algorithm (easier to check different path possibilities)
		Gets mouse position to create a start and end point in the environment
		self.pos --> (start, end)
		"""
		if len(self.pos) != 2: #checks that the path wasn't predefined
			time.sleep(0.1) 
			mx, my = pygame.mouse.get_pos() #x, y mouse position
			state = pygame.mouse.get_pressed()

			if state[0]: #left click (adds a point)
				self.pos.append((mx, my))
				self.draw_node((mx, my), (165, 42, 42))
			if state[2] and len(self.pos) > 0: #right click (deletes a point)
				self.pos.pop()
		else:

			return self.pos

	def exit(self):
		"""
		Quits if pygame's window cross is pressed
		"""
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()



if __name__ == "__main__":
	e = Environment("map_3")

	print(e.w, e.h)