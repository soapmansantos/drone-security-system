"""
Controls drone's directions using velocity commands
Input:
- all velocity commands for the drone
- manual keyboard input
Output:
- moves the drone correspondingly
- provides interface for user to manually control drone
"""

#drone = tello.Tello()
"""
drone.connect()
print(drone.get_battery())
drone.streamon()
kp.init()
"""

#parameters for mapping-------------
fvel = 12
avel = 360/10
interval = 0.25
d_interval = fvel*interval
a_interval = avel*interval
#------------------------

import math, random
from manual_control import key_press_module as kp
from datetime import datetime
import sys, time, cv2
import numpy as np



class ManualControl():
    def __init__(self, controls, vel, drone):
        self.controls = controls #keys to be used to control the drone
        self.vel = vel #velocity at which drone moves (in all directions)
        self.drone = drone #drone object (from tello.Tello())
        self.key_presses = [] #holds keys being pressed (only ones that matter)
        self.velocity = [0]*4 #holds velocity commands for drone: [0, 0, 0, 0]
        self.pos = [400]*2 #drone's position (initial pos is at centre of screen)
        self.screen = [800, 800] #specify screen dimensions
        self.dir = [[False, False]*4]


        self.x = self.screen[0]//2
        self.y = self.screen[1]//2
        self.points = [(0, 0), (0, 0)] #stores all x,y points to map them
        self.a = 0
        self.yaw = 0
        self.speed = 15
        self.aspeed = 50


    def get_vel(self, optn_controls=[]):
        """
        Turns key presses into velocity commands for
        the drone to follow
        """
        #velocity commands updated (if no key presses, drone is stationary)
        self.velocity = [0]*4

        #iterate through 2d array self.key_presses
        for count, i in enumerate(self.key_presses):
            #first value in subarray means positive value for velocity
            #e.g. forward
            if i[0]:
                self.velocity[count] = self.vel
            #second value in subarray means negative value for velocity
            #e.g. backward
            if i[1]:
                self.velocity[count] = -self.vel

        return self.velocity


    def get_key_presses(self):
        """"
        Gets the key presses using the key_press_module
        self.key_presses in the form: [[], [], [], []]
        """

        self.key_presses = kp.main(self.controls)
        return self.key_presses


    def vel_converter(self, vel):
        """
        Converts the velocity commands into boolean values
        Used to map drone's position
        """
        #set all directions given to drone as False
        dirs = [[False, False], [False, False], [False, False], [False, False]]

        #if a velocity command is being sent, set that direction to True
        for count, i in enumerate(vel):
            if i > 0:
                dirs[count][0] = True
            elif i < 0:
                dirs[count][1] = True
            else:
                dirs[count][0] = False
                dirs[count][1] = False

        return dirs




    def get_img(self):
        """
        User takes picture by pressing 'p'
        The picture is stored in the 'images' folder
        """

        #get frame captured by drone
        img = self.drone.get_frame_read().frame
        img = cv2.resize(img, (360, 240))

        #if 'p' is pressed, store image
        if kp.key_press("p"):
            now = datetime.now()
            # dd/mm/YY H:M:S
            dt_string = now.strftime("%d/%m/%Y,%H:%M:%S")
            print("PIC")
            cv2.imwrite(f"images/img_{dt_string}.jpg", img)
            time.sleep(0.3)



    def update_pos(self, dir, fvel, avel, interval):
        """"
        Updates drone's position in the screen
        Takes directions (dir --> 2d array w/ booleans, form:
        [[right, left], [forward, backward], [up, down], [turn right, turn left]])
        fvel: forward/backward velocity
        avel: angular velocity
        interval: rate at which position changes
        """
        #initialize variables and set intervals for accurate mapping
        lr, fb, ud, yv = 0, 0, 0, 0
        d = 0
        yaw = 0
        d_interval = fvel * interval
        a_interval = avel * interval

        #updates d and self.a values as the directions given to the drone change
        #self.a and d used to map the drone
        if dir[0][0]:
            lr = self.speed
            d = -d_interval
            self.a = 180
        if dir[0][1]:
            lr = -self.speed
            d = d_interval
            self.a = -180
        if dir[1][0]:
            fb = self.speed
            d = d_interval
            self.a = -90
        if dir[1][1]:
            fb = -self.speed
            d = d_interval
            self.a = 90
        if dir[3][0]:
            yv = self.aspeed
            self.yaw += a_interval
        if dir[3][1]:
            yv = -self.aspeed
            self.yaw -= a_interval

        #update the x and y position of the drone in the screen by using trigonometry
        self.a += self.yaw
        self.x += int(d*math.cos(math.radians(self.a)))
        self.y += int(d*math.sin(math.radians(self.a)))

        #append points that the drone is covering to self.points
        #used to draw the path followed by user on the screen
        if self.points[-1][0] != self.x or self.points[-1][1] != self.y:
            self.points.append((self.x, self.y))

        #sleep for self.interval
        #used for accurate mapping
        time.sleep(self.interval) 

        return self.x, self.y




    def draw_points(self):
        """
        Draws the drone's position on the screen
        """
        #set screen to a numpy array of 0s with dimensions of self.screen
        screen = np.zeros((self.screen[0], self.screen[1], 3), np.uint8)

        #draw the points that the drone has been in
        for point in self.points:
            cv2.circle(screen, point, 5, (0, 0, 255), cv2.FILLED)
        #draw the point (with a different colour) of the drone's current position
        cv2.circle(screen, (self.x, self.y), 8, (217, 82, 24), cv2.FILLED)
        #show the distance travelled relative to the start
        cv2.putText(screen, f"({(self.points[-1][0] - self.screen[0]//2)/100}, {(self.points[-1][1] - self.screen[1]//2)/100})m",
                    (self.x + 10, self.y + 30), cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 255), 1)
        #show screen
        cv2.imshow("Ouput", screen)
        cv2.waitKey(1)





def main():
    kp.init()
    dc.get_key_presses()
    dc.get_vel()
    dc.update_pos(dc.vel_converter(dc.velocity), fvel, avel, interval)

    return dc.velocity



if __name__ == "__main__":
    drone = tello.Tello()
    dc = DroneControls([["d", "a"], ["w", "s"], ["UP", "DOWN"], ["RIGHT", "LEFT"]], 50, drone)
    while True:
        kp.init()
        dc.get_key_presses()
        #dc.get_img()

        dc.get_vel()
        dc.update_pos(dc.vel_converter(dc.velocity), fvel, avel, interval)
        #print(dc.vel_converter(dc.velocity))
        dc.draw_points()


        if kp.key_press("t"):
            drone.takeoff()

        dc.drone_key_control()
        dc.get_key_presses()

        if kp.key_press("l"):
            drone.land()
