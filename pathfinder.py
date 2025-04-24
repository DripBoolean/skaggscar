import picobot_api
import math
import time
import cv2 as cv
import numpy as np

# All measurements are in cm and where measure using a ruler
camera_height_from_ground = 4.2
wheel_diameter = 8.2
axel_distance = 10.7
tape_radius = 2.4
axel_to_camera_distance = 15.1
encoder_counts_per_revolution = 96 # From Docs
vertical_fov = math.radians(27.0) # Messy Measurement, prolly wrong
horizontal_fov = math.radians(38.362) # Messy Measurement, prolly wrong but hopefully good enough

vehicle_position = [0.0, 0.0]
vehicle_angle = 0.0

ground_points = [] # Array of 2-lists (lists are mutable)

camera_width = 800
camera_height = 600

def take_capture():
    global camera_width, camera_height
    capture = cv.VideoCapture(0)
    capture.set(cv.CAP_PROP_FRAME_WIDTH, camera_width)
    capture.set(cv.CAP_PROP_FRAME_HEIGHT, camera_height)

    ret, cap = capture.read()

    print(cap.shape)

    if ret:
        cap.resize(camera_height, camera_width, 3)
        cap = np.flip(cap, 0)
        cap = np.flip(cap, 1)

        
        # Detect the color green (DAS)
        hsv = cv.cvtColor(cap,cv.COLOR_BGR2HSV)
        lower_green = np.array([50,100,100]) # this is in HSV
        upper_green = np.array([90,255,255])
        # mask for threshold on green (ask Hannah for threshold deets)
        mask = cv.inRange(hsv,lower_green,upper_green)
        
        print(mask.shape)
        for x in range(0, camera_width, 10):
            for y in range(0, camera_height, 10):
                if mask[y, x] == 255:
                    cap[y, x] = [0, 0, 255]
                    add_ground_point(x, y)

        #cv.imshow("cap", cap)
        #cv.imshow("mash", mask)
        #cv.waitKey()


wheel_circumference = wheel_diameter * math.pi
encoder_tick_distance = wheel_circumference / encoder_counts_per_revolution

def wheel_movement(A, B, X):
    if A == B:
        return (A, 0)
    
    reversed = False
    if A == 0:
        temp = A
        A = B
        B = temp
        reversed = True
    
    ri = X / (B / A - 1)
    b = A / ri

    S = 2 * (ri + (X / 2)) * math.sin(b / 2)
    #dO = b / 2

    if reversed:
        return (S, -b)

    return (S, b)

def calculate_movement():
    global encoder_tick_distance, axel_distance
    e1 = picobot_api.readEncoder1()
    time.sleep(0.01)
    e2 = picobot_api.readEncoder2()
    
    e1r = e1 * encoder_tick_distance
    e2r = e2 * encoder_tick_distance

    print(e1r)
    print(e2r)

    return wheel_movement(e1r, e2r, axel_distance)

class Ray:
    def __init__(self, position = [0, 0], angle = 0.0):
        self.position = position
        self.angle = angle

class AgedPoint:
    def __init__(self, position = [0, 0]):
        self.position = position
        self.spawn_time = time.time()
        
    def __str__(self):
        return f"{self.position} @ {time.time() - self.spawn_time}"


def add_ground_point(x, y):
    
    global vertical_fov, horizontal_fov, camera_width, camera_height, camera_height_from_ground, vehicle_angle, vehicle_position, ground_points, axel_to_camera_distance

    center_x = camera_width / 2
    center_y = camera_height / 2

    xO = horizontal_fov * (x - center_x) / center_x
    yO = -vertical_fov  * (y - center_y) / center_y

    if yO >= 0 :
        return None
    
    M = camera_height_from_ground / math.tan(-yO)
    O = vehicle_angle + xO # Need to do more math
    cM = axel_to_camera_distance
    cO = vehicle_angle
    
    print(cM * math.cos(cO))
    ground_points.append(AgedPoint([M * math.cos(O) + cM * math.cos(cO), M * math.sin(O) + cM * math.sin(cO)]))
    
take_capture()
print([str(x) for x in ground_points][-1])