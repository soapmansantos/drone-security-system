from djitellopy import tello
import os, sys
import cv2
import torch
import urllib.request
import time
import random
import keyboard
import numpy as np
import math

from drone.drone_control import key_press_module as kp
#import object_detection as od
import matplotlib.pyplot as plt


#connect to drone's wifi

#os.system('cmd /c "netsh wlan show networks"')
#drone_network = "TELLO-FE53F5"
#os.system(f'''cmd /c "netsh wlan connect name={drone_network}"''')



#Connect to drone
def connect_drone():
    global drone
    connect = False
    if kp.key_press("t") and not connect:
        drone = tello.Tello()
        drone.connect()
        print(drone.get_battery())
        drone.streamon()

        time.sleep(2)
        connect = True

        return drone
    else:
        return None


#functions to get depth

def load_model():
    global midas, device, transform
    model_type = "MiDaS_small"

    midas = torch.hub.load("intel-isl/MiDaS", model_type)
    #midas = torch.load("/home/santos/.cache/torch/hub/intel-isl_MiDaS_master")

    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
    midas.to(device)
    midas.eval()

    midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")

    if model_type == "DPT_Large" or model_type == "DPT_Hybrid":
        transform = midas_transforms.dpt_transform
    else:
        transform = midas_transforms.small_transform


def detect_face(image):
    
    face_width = 0
    center = (0, 0)
 
    face_cascade = cv2.CascadeClassifier("resources/face_tracking_file.xml")
    img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(img_gray, 1.2, 8)
 
    for (x, y, h, w) in faces:
        #cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
        center = ((x+w)/2, (y+h)/2)
 
    return center



def depth_to_distance(depth):
    #distance = depth / 28.5
    #distance = (-0.59993*depth) + 26.0409
    #distance = (-8.35697*depth) + 139.045
    distance = (4.26694*depth) - 3.32428
    distance = (-10.3188*depth) + 207.131
    
    return distance
    


def get_depth(depth_map, point):
    depth_object = depth_to_distance(depth_map[int(point[0]), int(point[1])])
    #print("Depth to object: ", (depth_map[int(point[0]), int(point[1])]))

    
    return depth_object, (depth_map[int(point[0]), int(point[1])])


def closest_obs(depth_map):
    return np.unravel_index(np.argmax(depth_map), depth_map.shape)




start = False
count = 0

def depth_map(img):
    global count
    kp.init()
    pic = True
    count += 1
    #point = detect_face(img)
    
    if kp.key_press("p") and not pic:
        pic = True
        count += 1
    if pic:    
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        input_batch = transform(img).to(device)

        with torch.no_grad():
            prediction = midas(input_batch)

            prediction = torch.nn.functional.interpolate(
                prediction.unsqueeze(1),
                size=img.shape[:2],
                mode="bicubic",
                align_corners=False,
            ).squeeze()

        output = prediction.cpu().numpy()


        shape = output.shape

        #print("Closest px idx: ", closest_obs(output))
        #point = detect_face(img)
        #point = closest_obs(output)
        point = (shape[0]//2, shape[1]//2)

        distance, depth = get_depth(output, point)
        #print("Distance: ", distance)
        print("Depth: ", round(depth, 2))

        #od.main(img)
        cv2.imwrite(f"resources/save{count}.jpg", output)

        if cv2.waitKey(1) == ord("q"):
            pass

        pic = False

        return distance, point, shape
    else:
        return None, None, None


def obstacle_offset(distance, pos, dims):
    """
    Use depth_map methods to get the distance to the detected contours,
    check if it is close enough to be able to map, and then return the 
    distance and angle from center (to map later in 'map' module)
    """
    if pos is None:
        return None, None
    else:

        offset = pos[0] - (dims[0]/2)
        angle = math.atan2(offset, distance)

        return distance, angle




load_nn = start = False



def main(img):
    distance, point, shape = depth_map(img)

    return obstacle_offset(distance, point, shape)





if __name__ == "__main__":
    load_model()
    kp.init()
    while True:
        if kp.key_press("t") and not start:
            start = True
            connect_drone()
            time.sleep(2)

        if start:
            img = drone.get_frame_read().frame
            depth_map(img)
