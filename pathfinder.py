import picobot_api
import math
import time

# All measurements are in cm and where measure using a ruler
camera_height_from_ground = 4.2
wheel_diameter = 8.2
axel_distance = 10.7
tape_radius = 2.4
axel_to_camera_distance = 15.1
encoder_counts_per_revolution = 96 # From Docs
vertical_fov = math.pi / 6 # Messy Measurement, prolly wrong
horizontal_fov = math.pi / 6 # Messy Measurement, prolly wrong

vehicle_position = [0.0, 0.0]
vehicle_angle = 0.0

ground_points = [] # Array of 2-lists (lists are mutable)

camera_width = 800
camera_height = 600


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


def add_ground_point(x, y):
    global vertical_fov, horizontal_fov, camera_width, camera_height, camera_height_from_ground, vehicle_angle, vehicle_position, ground_points, axel_to_camera_distance

    center_x = camera_width / 2
    center_y = camera_height / 2

    xO = horizontal_fov * (x - center_x) / center_x
    yO = vertical_fov  * (y - center_y) / center_y

    if xO >= 0 :
        return None
    
    M = axel_to_camera_distance + camera_height / math.tan(xO)
    O = vehicle_angle + yO


    ground_points.append(AgedPoint([M * math.cos(O), M * math.sin(O)]))