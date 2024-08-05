import pygame, sys, math, time #import all libraries necessary
import numpy as np
#import other files from path planning module
from path import env
from path import path_planning
sys.setrecursionlimit(10000)


def check_path(nodes, dims, screen):
	"""
	Checks if the remaining path collides with any obstacles
	when a new obstacle is added to the map
	Used while flying
	"""
	#create objects for environment and path planning
	environment = env.Environment(dims, screen, "map")
	path = path_planning.RRT((900, 450), (1700, 800), environment.screen, environment.dims, environment.map_location)
	environment.update_map() #update map to take into account any new obstacles
	nodes = [[nodes[i], nodes[i+1]] for i in range(len(nodes)) if i+1 < len(nodes)] #puts nodes in the form [parent, child]
	for i in nodes:
		collision = path.collide_obs(i[0], i[1]) #Checks for collision between nodes

		return collision


def main(start, end, dims, screen):
	"""
	Input: start position (usually drone's current position), end (destination), 
	dims --> dimensions of the map, screen--> pygame's screen size
	Output: writes to path.txt file with nodes of path foun 
	"""
	#generate objects for the environment and RRT classes
	environment = env.Environment(dims, screen, "map")
	path = path_planning.RRT(start, end, environment.screen, environment.dims, environment.map_location)
	write = False

	while True:
		environment.update_map()
		environment.exit()

		for event in pygame.event.get():

			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()



		if not path.found:
			nodes = path.new_node() #generates a new node radomly
			select_nodes = path.select_node(nodes) #selects closest node to new node
			#checks if the edge between these two nodes collide with an obstacle
			collision = path.collide_obs(select_nodes[0], select_nodes[1])


			if not collision:
				#parent node, child node, and edge are drawn
				environment.draw_node(select_nodes[0], (255, 0, 0)) 
				environment.draw_node(select_nodes[1], (255, 0, 0))
				environment.draw_edge(select_nodes, (255, 0, 0), 1)

			else:
				#Remove node from tree
				path.tree.nodes.pop()


		else:
			if path.found:
				print("Found path.")

				if path.trace:
					#writes the traced path into a text file
					f = open("path/path.txt", "w+")

					for i in reversed(path.path):
						f.write(f"{i[0]},{i[1]}\n")
					f.close()

					#draws the traced path's nodes and edges to represent the path found
					for count, i in enumerate(path.path):
						environment.draw_node(i, (0, 0, 0))
						try:
							environment.draw_edge((i, path.path[count+1]), (0, 0, 0), 3)
						except IndexError:
							environment.draw_edge((i, path.path[-1]), (0, 0, 0), 3)

					break

				else:
					path.traverse_tree(end) #tree is traversed to trace path



		



		pygame.display.update()

if __name__ == "__main__":
	main((1, 1), (450, 450), (100, 100), (500, 500))
