# install opencv "pip install opencv-python"
import cv2, math
import numpy as np
import os
from djitellopy import tello
#import depth_map as dm
"""
drone = tello.Tello()
drone.connect()
print(drone.get_battery())

drone.streamon()
"""



import cv2, math
from datetime import datetime



class Threat:
	def __init__(self):
		self.threat_pos = (0, 0) #center value of threat's bounding rect
		self.focal_length = 0 #focal length of drone's camera
		self.threat_width = 0 #width of threat's bounding rect
		self.is_threat = False
		self.record = False
		self.dt_string = ""
		self.img_list = []




	def threat_data(self, img):
		"""
		Detects threats in img
		Creates a bounding rect to identify threat's position
		Output: the width and position of the bounding rect
		"""
		#pre-trained machine learning model to detect human faces
		cascade = cv2.CascadeClassifier("threats/resources/threat_tracking_file.xml")
		img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

		#creates bounding rect around detected threat
		threats = cascade.detectMultiScale(img_gray, 1.2, 8)
	 
		for (x, y, h, w) in threats:
			cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2) #draw a rectangle around threat
			#get the width and position of the threat in the camera
			self.threat_width = w
			self.threat_pos = ((x+x+w)//2, (y+y+h)//2)


		if threats == (): #means no threat is detected
			self.is_threat = False
			self.threat_width = 0
			self.threat_pos = (0, 0)
		else:
			self.is_threat = True
	 
		return self.threat_width, self.threat_pos




	def find_focal_length(self, measured_distance, real_width, width_in_rf_image):
		"""
		Input: measured/known values of face in the real world
		Output: focal length
		(Focal length is a property of the camera, it doesn't change)
		"""
		#calculate focal length using the lens equation
		self.focal_length = (width_in_rf_image * measured_distance) / real_width

		return self.focal_length




	def find_distance(self, real_width):
		"""
		Calculates the distance using the lens equation
		"""
		distance = (real_width * self.focal_length) / self.threat_width

		return distance




	def get_distance(self, img):
		"""
		Focal length and distance methods are called along
		with threat detection to get the distance to the threat
		"""
		#manually measured values to calculate the focal length
		#the average of repeated measurements (reduces uncertainty)
		known_distance = 38.6
		known_width = 14
		known_img_width = 129

		self.threat_data(img) #detects threat
		#calculate focal length
		self.focal_length = self.find_focal_length(known_distance, known_width, known_img_width)
	 
		if self.is_threat: #if False, it means no threat is detected
			distance = self.find_distance(known_width) #calculate distance
			#print("Distance: ", round(distance, 2))

			return distance
		else:
			return None




	def vector_to_command(self, distance, angle):
		"""
		Break down vector representing threat into
		its x and y components
		Turn each one into a yaw and up/down velocity command
		"""
		vx = distance*math.cos(angle) #get vectors in the x and y directions
		vy = distance*math.sin(angle) #by splitting vector into its components

		cmd_x = (75/480)*vx #multipliers calculated by setting max value
		cmd_y = (75/360)*vy #as the max velocity command required (50)

		return cmd_x, -cmd_y




	def vector(self, img):
		"""
		Creates vector for the x and y axis by calculating the
		magnitude (distance) and direction (angle) to the threat
		"""
		center = (img.shape[1]//2, img.shape[0]//2) #get center position of camera screen
		distance = angle = 0

		if self.is_threat:
			#calculate magnitude of vector
			distance = math.dist(center, self.threat_pos)

			#calculate direction of vector
			angle = math.atan2(self.threat_pos[1]-center[1], self.threat_pos[0]-center[0])

			#draw a line representing the vector
			cv2.line(img, center, self.threat_pos, (0, 255, 0), 2)

		return self.vector_to_command(distance, angle) #convert vector to commands




	def cmd_to_angle(self, cmd):
		#converts yaw command into an angle command
		return (15/36)*cmd





	def follow(self, img, min_distance, max_distance):
		"""
		Input: lower (min_distance) and upper (max_distance) bounds
		of accepted distance range to the threat

		Creates vector in the z axis (vz) to follow the threat
		by using it as a forward/backward velocity command

		Gets distance and angle to map the following and keep track
		of drone's position
		"""
		vz = 0 #z vector
		z_speed = 2 #multiplier to increase drone's following speed

		dist = self.get_distance(img) #distance to threat
		angle = self.cmd_to_angle(self.vector(img)[0]) #yaw command

		if self.is_threat:
			if dist < min_distance:
				#move away threat it gets closer
				vz = -(min_distance - dist)*z_speed
			elif dist > max_distance:
				#move towards threat as it moves away
				vz = (dist - max_distance)*z_speed


		return dist, angle, vz




	def record_video(self, record, img):
		"""
		Records threat if one is detected
		"""

		if record:

			if not self.record:
				#get the date and time when the threat is first detected
				now = datetime.now()
				#turn date and time into a string of the form:
				#dd-mm-YY,H:M:S
				self.dt_string = now.strftime("%d-%m-%Y,%H:%M:%S")

				self.record = True
			#add frame to img_list
			self.img_list.append(img)

		else:
			self.record = False




	def store_video(self, video_dims):
		"""
		Stores video of threat previously captured
		by the record_video method
		video_dims specifies the dimensions at which
		the video should be stored
		"""

		os.mkdir(f"threats/recordings/{self.dt_string}")

		#create video object
		video = cv2.VideoWriter(f"threats/recordings/{self.dt_string}.avi", 0, 1, video_dims) 

		#iterate through all the images captured and write them into the video object
		for count, img in enumerate(self.img_list):
			video.write(img)
			cv2.imwrite(f"threats/recordings/{self.dt_string}/{count}.jpg", img)

		video.release() #finish video
		self.img_list = [] #empty img_list










def contours(img, contour, area_threshold):
	contours, hierarchy = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

	for i in contours:
		area = cv2.contourArea(i)
		if area > area_threshold:
			cv2.drawContours(contour, i, -1, (255, 0, 255), 7)
			perimeter = cv2.arcLength(i, True)
			approx = cv2.approxPolyDP(i, 0.02 * perimeter, True)
			x, y, w, h  = cv2.boundingRect(approx)
			center = ((x+x+w)/2, (y + y + h)/2)
			cv2.rectangle(contour, (x, y), (x + w, y + h), (0, 255, 0), 5)

			return center
		else:
			return None




def contour_processing(frame, threshold1, threshold2, area_threshold):
	frame_contour = frame.copy()

	frame_blur = cv2.GaussianBlur(frame, (7, 7), 1)
	frame_gray = cv2.cvtColor(frame_blur, cv2.COLOR_BGR2GRAY)

	#threshold1 = 100
	#threshold2 = 100
	#area_threshold = 1000

	canny = cv2.Canny(frame_gray, threshold1, threshold2)
	kernel = np.ones((5, 5))
	dilation = cv2.dilate(canny, kernel, iterations=1)
	cv2.imshow("dilation", dilation)


	obs_pos = contours(dilation, frame_contour, area_threshold)

	if obs_pos != None:
		print("Center of contour: ", obs_pos)


	cv2.imshow("contours", frame_contour)

	if cv2.waitKey(1) == ord("q"):
		pass

	return obs_pos







if __name__ == "__main__":
	threat = Threat()
	record = False
	count = 0

	while True:

		img = drone.get_frame_read().frame
		distance, angle, fspeed = threat.follow(img, 0, 0)
		#distance, angle, self.fspeed = self.threat.follow(img, 0, 0)

		cv2.imshow("feed", img)

		if cv2.waitKey(1) == ord("q"):
			cv2.destroyAllWindows()
			drone.streamoff()
			break


		if distance != None:
			#self.yaw, self.ud_v = threat.vector(img)
			yaw, ud_v = threat.vector(img)

		if threat.is_threat:
			record = True
			count = 0


		threat.record_video(record, img)

		if record and not threat.is_threat:
			count += 1

		if count >= 50 and not threat.is_threat:
			record = False
			count = 0
			threat.store_video((img.shape[1], img.shape[0]))
			print("Stop recording")


	 
	cv2.destroyAllWindows()
	#drone.streamoff()

"""

TO-DO:
Use findContours and depth map to find obstacles
"""