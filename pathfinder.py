import picobot_api
import math
import time
import cv2 as cv
import numpy as np
import threading
import sys

picobot_api.init()

# All measurements are in cm and where measure using a ruler
camera_height_from_ground = 4.2
wheel_diameter = 8.2
axel_distance = 10.7
tape_radius = 2.4
axel_to_camera_distance = 15.1
encoder_counts_per_revolution = 96 # From Docs
vertical_fov = math.radians(25.0) # Messy Measurement, prolly wrong but close enough
#horizontal_fov = math.radians(35.362) # Messy Measurement, prolly wrong but hopefully good enough
search_radius = 4.0
search_count = 30
path_node_acceptance_radius = 1.0

wheel_circumference = wheel_diameter * math.pi
encoder_tick_distance = wheel_circumference / encoder_counts_per_revolution

vehicle_position = [0.0, 0.0]
vehicle_angle = 0.0

# Array of 2-lists
ground_points = [] 
current_path = []

camera_width = 800
camera_height = 600

running = True
thread_errored = False

class AgedPoint:
    def __init__(self, position = [0, 0]):
        self.position = position
        self.spawn_time = time.time()
        self.traversed = False
        self.explored = False
        
    def __str__(self):
        return f"{self.position} @ {time.time() - self.spawn_time}"
    
    def __repr__(self):
        return self.__str__()
    
def photo():
    capture = cv.VideoCapture(0)
    capture.set(cv.CAP_PROP_FRAME_WIDTH, camera_width)
    capture.set(cv.CAP_PROP_FRAME_HEIGHT, camera_height)

    ret, cap = capture.read()
    
    cap.resize(camera_height, camera_width, 3)
    cap = np.flip(cap, 0)
    cap = np.flip(cap, 1)
    
    return cap

def add_ground_point(x, y):
    global vertical_fov, camera_width, camera_height, camera_height_from_ground, vehicle_angle, vehicle_position, ground_points, axel_to_camera_distance

    center_x = camera_width / 2
    center_y = camera_height / 2
    
    x -= center_x
    y -= center_y
    
    if y <= 0:
        return
        
    x /=  center_x
    y /= center_y
    
    t = math.tan(vertical_fov)
    
    x *= t
    y *= t
    
    s = camera_height_from_ground / y
    
    gy = -x * s
    gx = s
    
    M = math.sqrt(gy ** 2 + gx ** 2)
    O = math.atan2(gy, gx) + vehicle_angle

    cM = axel_to_camera_distance
    cO = vehicle_angle

    ground_points.append(
        AgedPoint(
            [M * math.cos(O) + cM * math.cos(cO) + vehicle_position[0],
             M * math.sin(O) + cM * math.sin(cO) + vehicle_position[1]]
            )
        )

def take_capture(show = False):
    global camera_width, camera_height
    capture = cv.VideoCapture(0)
    capture.set(cv.CAP_PROP_FRAME_WIDTH, camera_width)
    capture.set(cv.CAP_PROP_FRAME_HEIGHT, camera_height)

    ret, cap = capture.read()

    if ret:
        cap.resize(camera_height, camera_width, 3)
        cap = np.flip(cap, 0)
        cap = np.flip(cap, 1)
        
        mask = cap.copy()
        threshold = 30

        print(mask.shape)
        print(mask[0, 0])
        # Detect the color green (DAS)
        hsv = cv.cvtColor(cap,cv.COLOR_BGR2HSV)
        
        
        lower_green = np.array([40,100,100]) # this is in HSV
        upper_green = np.array([70,255,255])
        # mask for threshold on green (ask Hannah for threshold deets)
        mask = cv.inRange(hsv,lower_green,upper_green)

        for x in range(0, camera_width, 5):
            for y in range(0, camera_height, 5):
                if mask[y, x] == 255:
                    cap[y, x] = [0, 0, 255]
                    add_ground_point(x, y)
        if show:
            cv.imshow("cap", cap)
            #cv.imshow("mask", mask)
            #cv.imshow("??", hsv)
        
    else:
        print("Error capuuring image")

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
    global encoder_tick_distance, axel_distance, vehicle_position, vehicle_angle
    e1 = picobot_api.readEncoder1()
    e2 = picobot_api.readEncoder2()
    
    e1r = e1 * encoder_tick_distance
    e2r = e2 * encoder_tick_distance
    
    mag, b = wheel_movement(e1r, e2r, axel_distance)
    ang = b / 2
    
    vehicle_position[0] += mag * math.cos(ang + vehicle_angle)
    vehicle_position[1] += mag * math.sin(ang + vehicle_angle)
    vehicle_angle += b
    
    reset_encoders()



def reset_encoders():
    picobot_api.resetEncoder1()
    picobot_api.resetEncoder2()
    
def evaluate_space(x, y):
    global ground_points, tape_radius
    
    points_in_range = 0
    for point in ground_points:
        if point.traversed or point.explored:
            continue
        
        ppos = point.position
        dx = ppos[0] - x
        dy = ppos[1] - y
        
        dist = math.sqrt(dx ** 2 + dy ** 2)
        
        if dist < tape_radius:
            points_in_range += 1
    
    return points_in_range

def set_area_state(x, y, radius, explored=None, traversed=None):
    global ground_points
    for i in range(len(ground_points)):
        if explored != None:
            ground_points[i].explored=explored
        if traversed != None:
            ground_points[i].traversed=traversed
        
def reset_evaluation():
    global ground_points
    
    for i in range(len(ground_points)):
        ground_points[i].evaluted = False
        
def generate_path():
    global search_radius, ground_points, search_count, current_path
    
    reset_evaluation()
    current_search_radius = search_radius
    while True:
        #print(current_search_radius)
        best = None
        best_value = 0
        
        for i in range(search_count):
            angle = 2 * math.pi * i / search_count
            
            x_pos = current_search_radius * math.cos(angle)
            y_pos = current_search_radius * math.sin(angle)
            
            value = evaluate_space(x_pos, y_pos)
            
            if value > best_value:
                best = (x_pos, y_pos)
                
                value = best_value
                
        if best == None:
            current_search_radius += 0.8
            search_count += 4
            continue
        
        set_area_state(*best, tape_radius, explored=True)
        current_path = [best]
        break

def update_wheel_power():
    global vehicle_position, vehicle_angle, current_path
    
    if len(current_path) == 0:
        print("No Path")
        picobot_api.setMotorPower1(0)
        picobot_api.setMotorPower2(0)
        return
    
    target = current_path[0]
    
    target_relative_position = [target[0] - vehicle_position[0], target[1] - vehicle_position[1]]
    
    if math.sqrt(target_relative_position[0] ** 2 + target_relative_position[1] ** 2) < path_node_acceptance_radius:
        print(f"Reached: {current_path.pop(0)}")
        
        return
    
    relative_angle = math.atan2(
        target_relative_position[1],
        target_relative_position[0]
    )
    
    angle_difference = relative_angle - vehicle_angle
    angle_difference = math.fmod(angle_difference, math.pi)
    
    if angle_difference > math.radians(5.0):
        if angle_difference > math.radians(20.0):
            picobot_api.setMotorPower1(-100)
            picobot_api.setMotorPower2(100)
        else:
            picobot_api.setMotorPower1(-70)
            picobot_api.setMotorPower2(70)
    elif angle_difference < math.radians(-5.0):
        if angle_difference < math.radians(-20.0):
            picobot_api.setMotorPower1(100)
            picobot_api.setMotorPower2(-100)
        else:
            picobot_api.setMotorPower1(70)
            picobot_api.setMotorPower2(-70)
    else:
        picobot_api.setMotorPower1(100)
        picobot_api.setMotorPower2(100)
        

def position_update_daemon():
    global thread_errored, running
    while running:
        try:
            #calculate_movement()
            time.sleep(0.02)
        except Exception as e:
            print(f"Error while calculating movement {e}")
            thread_errored = True

def movement_execution_daemon():
    global thread_errored, running
    while running:
        try:
            calculate_movement()
            update_wheel_power()
            time.sleep(0.01)
        except Exception as e:
            print(f"Error while executing movement {e}")
            thread_errored = True

def observation_daemon():
    #??? how do you 
    pass

def move():
    picobot_api.setMotorPower1(100)
    picobot_api.setMotorPower2(-100)
    time.sleep(0.3)
    picobot_api.setMotorPower1(0)
    picobot_api.setMotorPower2(0)
    
            
# Observer thread
# Movement Execution thread
# Position Update thread
# Path formation thread

reset_encoders()

#running = False

# print(math.degrees(vehicle_angle))
# take_capture()
# print(len(ground_points))
# print(ground_points[0].position)
# generate_path()
# print(current_path)

take_capture(True)
print(ground_points)
cv.waitKey()
generate_path()
print(current_path)

position_update_thread = threading.Thread(target=position_update_daemon)
position_update_thread.daemon = True
position_update_thread.start()

movement_execution_thread = threading.Thread(target=movement_execution_daemon)
movement_execution_thread.daemon = True
movement_execution_thread.start()

#vehicle_angle = math.radians(90)


#cv.waitKey()
#cv.imshow("window", photo())
#cv.waitKey()
#current_path = [(15, 15), (0, 0)]
time.sleep(5)
# time.sleep(5)
#print(vehicle_position)
#print(math.degrees(vehicle_angle))
#picobot_api.set_motor

# wait for threads to exit


running = False
time.sleep(0.1)
picobot_api.setMotorPower1(0)
picobot_api.setMotorPower2(0)
sys.exit()