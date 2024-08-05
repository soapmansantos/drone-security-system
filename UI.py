import pygame, sys
import numpy as np
import random
import cv2
import time
import os
import drone as d

pygame.init()
dims = (600, 400)
screen = pygame.display.set_mode((dims[0], dims[1]))
pygame.display.set_caption('UI')
clock = pygame.time.Clock() #set framerate


class Button():

	def __init__(self, screen, pos, colour, dims, tag):
		self.screen = screen #screen button is going to be displayed in
		#position of the button in the screen
		self.x = pos[0]
		self.y = pos[1]
		self.colour = colour #rgb values for colour
		#dimensions of the button
		self.w = dims[0]
		self.h = dims[1]
		#create button's rect
		self.rect = pygame.Rect(self.x, self.y, self.w, self.h)

		#font to display the button's tag (the text on the button)
		self.font = pygame.font.Font('freesansbold.ttf', 16)
		self.tag = tag #text on the button
		self.text = self.font.render(tag, True, (0, 0, 0)) #render tag's text
		self.text_rect = self.text.get_rect() #create rect for the text
		self.text_rect.center = (self.x + (self.w // 2), self.y + (self.h // 2))

		self.click = False
		self.show = False

	def display(self):
		"""
		Display the button with it's tag inside it
		"""
		pygame.draw.rect(self.screen, self.colour, self.rect)
		self.screen.blit(self.text, self.text_rect)


	def clicked(self, mpos):
		"""
		Checks if button was clicked
		Input: mouse's position when method is called
		"""
		#check if mpos is inside the position of the rect created by the button
		if (mpos[0] > self.x and mpos[0] <
				(self.x + self.w)) and (mpos[1] > self.y and mpos[1] <
																(self.y + self.h)):
			self.click = True
		else:
			self.click = False

		return self.click



class TextInput(Button):
	"""
	Inherits the button class
	Used as a button for user to enter text
	"""

	def __init__(self, screen, pos, colour, dims, tag):
		Button.__init__(self, screen, pos, colour, dims, tag) #initialize parent class
		self.inp_rect = pygame.Rect(self.x, self.y, self.w, self.h) #rect for text input
		self.font = pygame.font.Font('freesansbold.ttf', 32) #set font to a bigger size
		self.txt = "" #text entered by user
		self.active = self.click #whether or not keyboard inputs are added to self.txt string


	def display_text(self):
		"""
		Displays the text being entered by the user
		so they can keep track of what they are writing
		"""
		self.text = self.font.render(self.txt, True, (0, 0, 0))
		pygame.draw.rect(self.screen, self.colour, self.rect)
		self.screen.blit(self.text, self.text_rect)


	def display_textbox(self):
		#displays the textbox indicating where they should click
		#to enter the input
		#Represented by the border of a rectangle
		pygame.draw.rect(self.screen, (0, 0, 0), self.inp_rect, 2)


#create buttons for main menu
fly_b = Button(screen, (dims[0] * (1 / 4), dims[1] * (1 / 4)), (255, 255, 255), (dims[0] / 2, dims[1] / 2), "Fly")
map_ = Button(screen, (dims[0] * (1 / 5), dims[1] * (1 / 5)), (255, 255, 255), (dims[0] / 5, dims[1] / 5), "Map")
exit = Button(screen, (0, 0), (255, 0, 0), (dims[0] / 10, dims[1] / 10), "Exit")
stream = Button(screen, (dims[0] * (3 / 5), dims[1] * (1 / 5)), (255, 255, 255), (dims[0] / 5, dims[1] / 5), "Stream")
land = Button(screen, (dims[0] * (1 / 5), dims[1] * (3 / 5)), (255, 255, 255), (dims[0] / 5, dims[1] / 5), "Land")
mcontrol = Button(screen, (dims[0]*(3/5), dims[1]*(3/5)), (255, 255, 255), (dims[0]/5, dims[1]/5), "Manual Control")

#create buttons for user to input the dimensions of the area
#the drone has to cover, and for user to access videos and images
text_dims = (dims[0] / 4, dims[1] / 8)
recordings = Button(screen, ((dims[0] - text_dims[0])/2 - 40, ((dims[1] - text_dims[1])/2) + 60), (255, 255, 255), (dims[0] / 6, dims[1] / 6), "Threat recordings")
images = Button(screen, ((dims[0] - text_dims[0])/2 + 90, ((dims[1] - text_dims[1])/2) + 60), (255, 255, 255), (dims[0] / 6, dims[1] / 6), "Images")
area_input = TextInput(screen, ((dims[0] - text_dims[0])/2, (dims[1] - text_dims[1])/2), (255, 255, 255), text_dims, "ddd")
enter = Button(screen, ((dims[0] - text_dims[0])/2 + 25, ((dims[1] - text_dims[1])/2) - 70), (255, 255, 255), (dims[0] / 6, dims[1] / 6), "Enter area (m²)")

#add all objects of the Buttons class that are part of the main menu to a list
buttons = []
buttons.append(map_)
buttons.append(exit)
buttons.append(stream)
buttons.append(land)
buttons.append(mcontrol)

#variables for handling user input in the interface
click = False
delete = False
fly = False
area_inp_state = False
char = ""


#main loop
while True:
	screen.fill((255, 255, 255)) #fill background with white

	#get the position of the mouse in the screen
	mpos = pygame.mouse.get_pos()

	#if area has not yet been specified by the user, let them enter the area
	if area_inp_state is False:

		if click:

			#if recordings button is clicked
			if recordings.clicked(mpos):
				#open recordings folder so that user can access all past recordings
				os.system('xdg-open "%s"' % "threats/recordings")


			if images.clicked(mpos):
				#open images folder (pictures taken by user are shown)
				os.system('xdg-open "%s"' % "manual_control/images")


			if enter.clicked(mpos) and not area_input.active:
				#try entering the user's input as the area
				try:
					if int(area_input.txt) >= 5:

						drone = d.Drone([int(area_input.txt)*100, int(area_input.txt)*100])
						#create drone object
						#area input is done *100 since program uses area in centimetres

						area_inp_state = True #area input has been entered succesfully
					else:
						#can't be guaranteed that drone will work correctly in an area smaller
						#than 5x5 metres, so asks user to try again
						print("Area must be greater than 5 x 5 metres")
						area_input.txt = "" #clears current input
						char = ""

				except ValueError:
					#if area_input.txt tries to be passed to int type, but it
					#isn't an integer, then the ValueError is raised
					print("Invalid area, must be an integer") #error message
					area_input.txt = "" #clears current input
					char = ""

			if area_input.clicked(mpos):
				#set area_input button to active so that user can write their input
				area_input.active = True

			else:
				area_input.active = False

		if area_input.active:

			if delete:
				#remove last character in the string
				area_input.txt = area_input.txt[:-1]
				delete = False

			if char != "":
				#add character typed with keyboard 
				#at the end of the area_input.txt string
				area_input.txt += char
				char = ""


		click = False

		#display all buttons and the textbox
		recordings.display()
		images.display()
		area_input.display_text()
		area_input.display_textbox()
		enter.display()



	if not fly and area_inp_state:
		#once user has correctly entered the area,
		#the fly button is displayed for the security
		#system to be active, and the drone to take off

		fly_b.display() #display button
		if fly_b.clicked(mpos):
			#change button's colour if it is hovered with the mouse
			fly_b.colour = (237, 237, 237)
			if click:
				fly = True
				time.sleep(0.25)
		else:
			fly_b.colour = (255, 255, 255)


	elif area_inp_state:
			d.main(drone) #call the main function from main drone module
			drone.ui_screen = screen
			
			#iterate through all the buttons in the main menu
			for button in buttons:
				button.display()

				if button.show:
					#set colour to green if button is pressed 
					button.colour = (0, 128, 0)
					
					if button.tag == "Map":
							#show the map's representation
							cv2.imshow("map", drone.map.img)
							cv2.waitKey(1)

					if button.tag == "Manual Control":
						#activate manual control
						drone.ui_screen = button.screen
						drone.key_control = True

					if button.tag == "Stream":
						#show the drone's camera stream
						drone.show_frame()

					if button.tag == "Exit":
						cv2.destroyAllWindows()
						pygame.quit()
						sys.exit()
						break

				else:

					if button.tag == "Manual Control":
						#set manual control to False
						drone.key_control = False

				#change colour of buttons as user hovers over them
				#set the exit button's colour as red
				if button.clicked(mpos) and not button.show and button.tag != "Exit":
					button.colour = (237, 237, 237)
				else:
					if button.tag != "Exit":
						button.colour = (255, 255, 255)


				#handle the buttons.show attribute for the buttons
				if click:
					if button.clicked(mpos):
						if button.show:
							button.show = False
						else:
							button.show = True

						#if user clicks on the Land button, the drone lands and the
						#user interface goes out of the main menu, since fly is False
						if button.tag == "Land":
							drone.land()
							fly = False

			#set click to False every iteration
			click = False

	#handle key inputs from the user
	for event in pygame.event.get():
		#terminate the program if the cross button is pressed
		if event.type == pygame.QUIT:
			pygame.quit()
			sys.exit()

		#get the keys being pressed
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_BACKSPACE:
				delete = True
			else:
				#the current character is set to the value typed in the keyboard
				char = event.unicode
		#if mouse is left clicked, then click is set to True
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
			click = True

	pygame.display.flip()
	clock.tick(120) #set frames per second to 120FPS

	pygame.display.update() #update all the actions handled by pygame
