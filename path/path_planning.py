import numpy, random, math, pygame
from path import env

class Node():
	def __init__(self, parent, data):
		self.data = data
		self.parent = parent
		self.child = None


class Tree():
	def __init__(self, root):
		self.root = Node(None, root)
		self.nodes = [self.root]

	def add_node(self, node):
		"""
		Input: new node object
		Output: nodes with new node added
		"""
		if len(self.nodes) > 0: 
			#set added node as the child of its parent
			self.nodes[-1].child = node
		
		self.nodes.append(node) #add node to tree

		return self.nodes


 

class RRT():
	def __init__(self, start, end, dims, grid, map_location):
		self.start = start
		self.end = end
		self.dims = dims
		self.max_distance = dims[0]/12 #maximum distance between nodes
		self.node = self.start #holds current node
		self.found = False
		self.trace = False
		#create environment and tree objects
		self.environment = env.Environment(grid, self.dims, map_location)
		self.tree = Tree(start)
		self.environment.update_map()
		self.trace_node = end
		self.path = [] #queue holding nodes of final path


	def distance(self, node, point):
		"""
		Returns the distance from the current node to a new node
		"""
		return round(math.sqrt((point[0]-node[0])**2 + (point[1]-node[1])**2))

	def new_node(self):
		"""
		Generates a new point randomly in the map
		"""
		x = random.randint(0, self.dims[0])
		y = random.randint(0, self.dims[1])

		return (x, y)

	def collide_obs(self, p1, p2):
		"""
		Checks if there is an obstacle between two nodes
		Done by checking any black in the edge created by two nodes
		"""
		collide = False
		num_subpoints = 200

		for i in range(0, num_subpoints+1):
			#use interpolation to check all points between two nodes
			u = i/num_subpoints
			x = round(p1[0]*u + p2[0]*(1-u)) #interpolation formula for x and y values in edge
			y = round(p1[1]*u + p2[1]*(1-u))

			if 0 < x < self.dims[0] and 0 < y < self.dims[1]:
				#checks if at the (x, y) pixel there is black
				#which means there is an obstacle, therefore a collision
				if self.environment.map.get_at((x, y)) == (0, 0, 0, 255):
					collide = True


		return collide


	def select_node(self, new_node):
		"""
		Input: Position of new node
		Finds closest node to the new node
		Puts it at a distance of self.max_distance away
		Output: adds new node to tree
		"""

		dists = [self.distance(i, new_node) for i in [x.data for x in self.tree.nodes]] #holds all distances from previous nodes to new node
		self.node = self.tree.nodes[dists.index(min(dists))].data #selects the closest node

		#checks if selected node has reached the final node, and path has been found
		if not self.collide_obs(self.node, self.end) and self.distance(self.node, self.end) <= self.max_distance*2:
			new_node = self.end
			self.end = new_node
			print("Found")
			self.found = True
		else:
			theta = math.atan2((new_node[1]-self.node[1]), (new_node[0]-self.node[0])) #calculates angle from closest node to new node
			#new node is moved at self.max_distance away, at the same angle
			new_node = (self.node[0] + round(self.max_distance*math.cos(theta)), self.node[1] + round(self.max_distance*math.sin(theta)))

		node = Node(self.node, new_node) #create new Node object
		self.tree.add_node(node) #add node to the tree

		return self.node, new_node



	def traverse_tree(self, trace_node):
		"""
		Traces path by finding each node's parent
		(starts from end node) until it reaches the
		start node
		self.path holds the actual positions of the
		nodes of the final path
		Input: current node

		"""
		#base case: if trace_node is the same as the initial node,
		#it means that the path has been traced
		if trace_node == self.tree.root.data:
			self.path.append(self.tree.root.data)
			self.trace = True

		else:
			for n in self.tree.nodes:
				if n.data == trace_node:
					self.path.append(n.data) #enqueue node's position
					trace_node = n.parent #set trace node as it's parent
					self.traverse_tree(trace_node)




if __name__ == "__main__":
	pass


#find angle from parent node to child, get every edge the same distance --> DONE
#retrace steps to find parent nodes and create path	