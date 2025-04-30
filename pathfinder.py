import picobot_api
import math
import time
import cv2 as cv
import numpy as np
import threading
import sys

class VideoCaptureAsync:
    def __init__(self, src=0, width=640, height=480):
        self.src = src
        self.cap = cv.VideoCapture(self.src)
        self.cap.set(cv.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv.CAP_PROP_FRAME_HEIGHT, height)
        self.grabbed, self.frame = self.cap.read()
        self.started = False
        self.read_lock = threading.Lock()

    def set(self, var1, var2):
        self.cap.set(var1, var2)

    def start(self):
        if self.started:
            print('[!] Asynchroneous video capturing has already been started.')
            return None
        self.started = True
        self.thread = threading.Thread(target=self.update, args=())
        self.thread.start()
        return self

    def update(self):
        while self.started:
            grabbed, frame = self.cap.read()
            with self.read_lock:
                self.grabbed = grabbed
                self.frame = frame

    def read(self):
        with self.read_lock:
            frame = self.frame.copy()
            grabbed = self.grabbed
        return grabbed, frame

    def stop(self):
        self.started = False
        self.thread.join()

    def __exit__(self, exec_type, exc_value, traceback):
        self.cap.release()

class PygameVideoStream:
    def __init__(self, path, width, height):
        import pygame.camera
        
        self.width = width
        self.height = height
        pygame.camera.init()
        self.cam = pygame.camera.Camera(path, (width, height), "RGB")
        self.cam.start()
        self.cam.set_controls(True, True, 50)
    
    def read(self):
        out = np.zeros((self.height, self.width, 3), np.uint8)
        img = self.cam.get_image()
        for iy in range(self.height):
            for ix in range(self.width):
                pix = img.get_at((ix, iy))
                out[iy, ix, 0] = int(pix.b)
                out[iy, ix, 1] = int(pix.g)
                out[iy, ix, 2] = int(pix.r)
        return out
        

class GroundPoint:
    def __init__(self, position = [0, 0]):
        self.position = position
        #self.spawn_time = time.time()
        self.traversed = False
        self.explored = False
        
    def __str__(self):
        return f"{self.position}"
    
    def __repr__(self):
        return self.__str__()

class VehiclePoint:
    def __init__(self, position = [0, 0], angle = 0):
        global axel_to_camera_distance
        self.position = position
        self.angle = angle
        self.spawn_time = time.time()
        
        self.camera_position = [0.0, 0.0]
        self.camera_position[0] = position[0] + axel_to_camera_distance * math.cos(angle)
        self.camera_position[1] = position[1] + axel_to_camera_distance * math.sin(angle)
    
    def age(self):
        return time.time() - self.spawn_time
        
    def __str__(self):
        return f"{self.position} *{self.angle} age: {self.age()}"
    
    def __repr__(self):
        return self.__str__()

# All measurements are in cm
camera_height_from_ground = 4.2
wheel_diameter = 8.7
axel_distance = 10.7
tape_radius = 2.4
axel_to_camera_distance = 15.1
encoder_counts_per_revolution = 96 # From Docs
vertical_fov = math.radians(25.0) # Messy Measurement, prolly wrong but close enough
search_radius = 2.0
search_count = 30
path_node_acceptance_radius = 1.0
camera_latency = 0.5
camera_polling_distance = 10 # Distance between pixels polled when taking photo

wheel_circumference = wheel_diameter * math.pi
encoder_tick_distance = wheel_circumference / encoder_counts_per_revolution

# Arrays of 2-lists
ground_points = [] 
current_path = []

vehicle_history = [VehiclePoint([0, 0], 0.0)]

current_target = None

camera_width = 800
camera_height = 600

camera = VideoCaptureAsync("/dev/video0", camera_width, camera_height)
camera.start()

vertical_fov_tan = math.tan(vertical_fov)
min_camera_gx = camera_height_from_ground / vertical_fov_tan
max_camera_gx = 40.0
horizontal_fov = (camera_width / camera_height) * vertical_fov

running = True
thread_errored = False

def rectify_camera():
    """ Uses pygame to flip cameras x and y (Cant be done in opencv as far as i know) """
    import pygame.camera
    pygame.camera.init()
    cam = pygame.camera.Camera("/dev/video0", (800, 600), "RGB")
    cam.start()
    cam.set_controls(True, True, 50)
    cam.stop()

def remote_control(use_camera=True):
    import pygame
    pygame.init()

    if use_camera:
        import pygame.camera
        pygame.camera.init()
        cam = pygame.camera.Camera("/dev/video0", (800, 600), "RGB")
        cam.start()
        cam.set_controls(True, True, 50) # Flips and sets brightness
        ds=pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Remote View")
    else:
        ds=pygame.display.set_mode((600, 600))
        pygame.display.set_caption("BrainDisplay")
        
    
    while True:
        ds.fill((0,0,0))
        if use_camera:
            image = cam.get_image() #read camera in as a surface
        else:
            array = np.flip(np.swapaxes(show_brain(False), 0, 1), 2)
            image = pygame.surfarray.make_surface(array)
        ds.blit(image,(0,0))
        pygame.display.update()
        
        pygame.event.pump()
        keys=pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            pygame.quit()
            return
        movement_vector = (keys[pygame.K_d] - keys[pygame.K_a], keys[pygame.K_w] - keys[pygame.K_s])
        
        wheel_values = (0, 0)
        if movement_vector[0] != 0:
            if movement_vector[1] != 0:
                wheel_values = (100, 0)
            else:
                wheel_values = (100, -100)
        elif movement_vector[1] != 0:
            wheel_values = (100, 100)
            
        if movement_vector[0] == -1:
            wheel_values = (wheel_values[1], wheel_values[0])
        if movement_vector[1] == -1:
            wheel_values = (-wheel_values[0], -wheel_values[1])
        
        picobot_api.setMotorPower1(wheel_values[0])
        picobot_api.setMotorPower2(wheel_values[1])

def show_brain(show=True):
    global ground_points, vehicle_history
    
    display = np.zeros((600, 600, 3))
    def to_coords(x, y):
        return (int(x + 300), int(-y + 300))
    
    points_are_ommited = False
    for point in ground_points:
        x, y = to_coords(*point.position)
        
        if x < 0 or x >= 600:
            points_are_ommited = True
            continue
        if y < 0 or y >= 600:
            points_are_ommited = True
            continue
        
        display[y, x] = (255, 255, 255)
    
    for point in vehicle_history:
        x, y = to_coords(*point.position)
        cx, cy = to_coords(*point.camera_position)
        
        brightness = 255 * (1 / (1 + 0.2 * point.age()))
        cv.line(display, (x, y), (cx, cy), (brightness, 0, 0), 1)
        display[y, x] = (0, 0, brightness)
    if show:
        if points_are_ommited:
            print("Points ommited in display")
        print(f"Vehicle Position: {vehicle_history[-1].position}")
        print(f"Vehicle Angle: {vehicle_history[-1].angle})")
        print(f"Number of points: {len(ground_points)}")
        print(f"Ground Points: {ground_points}")
        cv.imshow("PicoBrain", display)
    return display
    #cv.waitKey()


def get_dated_vehicle_point(age):
    global vehicle_history
    
    #def lerp(a, b, c):
    #    return (b - a) * c
    
    for point in reversed(vehicle_history):
        if point.age() < age:
            continue
        return point
    

def add_ground_point(x, y, vehicle_point):
    global vertical_fov_tan, camera_width, camera_height, camera_height_from_ground, camera_latency, ground_points, max_camera_gx

    center_x = camera_width / 2
    center_y = camera_height / 2
    
    x -= center_x
    y -= center_y
    
    if y <= 0:
        return
        
    x /= center_y
    y /= center_y
    
    x *= vertical_fov_tan
    y *= vertical_fov_tan
    
    s = camera_height_from_ground / y
    
    gy = -x * s
    gx = s
    
    if gx > max_camera_gx:
        return
    
    M = math.sqrt(gy ** 2 + gx ** 2)
    O = math.atan2(gy, gx) + vehicle_point.angle

    ground_points.append(
        GroundPoint(
            [M * math.cos(O) + vehicle_point.camera_position[0],
             M * math.sin(O) + vehicle_point.camera_position[1]]
            )
        )

def clear_points_in_camera(vehicle_point):
    global ground_points, horizontal_fov, min_camera_gx, vehicle_history, max_camera_gx, camera_polling_distance
    
    O = vehicle_point.angle
    x = vehicle_point.position[0]
    y = vehicle_point.position[1]
    removed = 0
    for i in reversed(range(len(ground_points))):
        point = ground_points[i]
        
        dx = point.position[0] - x
        dy = point.position[1] - y
        
        rO = math.fmod(math.atan2(dy, dx) - O, 180)
        M = math.sqrt(dx ** 2 + dy ** 2)
        
        rx = M * math.cos(rO)
        #ry = M * math.sin(rO)
        
        if rO > -horizontal_fov and rO < horizontal_fov and rx > min_camera_gx and rx < max_camera_gx:
            removed += 1
            ground_points.pop(i)
    print(f"Removed: {removed}")

def take_capture(show = False):
    global camera_width, camera_height, camera
#     capture = cv.VideoCapture(0)
#     capture.set(cv.CAP_PROP_FRAME_WIDTH, camera_width)
#     capture.set(cv.CAP_PROP_FRAME_HEIGHT, camera_height)

    ret, cap = camera.read()
    
    if ret:
        vehicle_point = get_dated_vehicle_point(camera_latency)
        clear_points_in_camera(vehicle_point)
        cap.resize(camera_height, camera_width, 3, refcheck=False)
        
        mask = cap.copy()
        # Detect the color green (DAS)
        hsv = cv.cvtColor(cap,cv.COLOR_BGR2HSV)
        
        lower_green = np.array([40,60,80]) # this is in HSV
        upper_green = np.array([70,255,255])
        # mask for threshold on green (ask Hannah for threshold deets)
        mask = cv.inRange(hsv,lower_green,upper_green)
        
        
        for x in range(0, camera_width, camera_polling_distance):
            for y in range(0, camera_height, camera_polling_distance):
                if mask[y, x] == 255:
                    cap[y, x] = [0, 0, 255]
                    add_ground_point(x, y, vehicle_point)
        if show:
            cv.imshow("cap", cap)
            #cv.imshow("mask", mask)
            #cv.imshow("??", hsv)
            #cv.waitKey()
        
    else:
        print("Error capturing image")

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
    global encoder_tick_distance, axel_distance, vehicle_history
    e1 = picobot_api.readEncoder1()
    e2 = picobot_api.readEncoder2()
    
    if e1 == None or e2 == None:
        raise RuntimeError("Error reading encoder")
    
    e1r = e1 * encoder_tick_distance
    e2r = e2 * encoder_tick_distance
    
    mag, b = wheel_movement(e1r, e2r, axel_distance)
    ang = b / 2
    
    previous_angle = vehicle_history[-1].angle
    previous_position = vehicle_history[-1].position.copy()
    previous_position[0] += mag * math.cos(ang + previous_angle)
    previous_position[1] += mag * math.sin(ang + previous_angle)
    vehicle_history.append(VehiclePoint(previous_position, previous_angle + b))
    
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
        if not math.sqrt(ground_points[i].position[0] ** 2 + ground_points[i].position[1] ** 2) < radius:
            continue
        
        if explored != None:
            ground_points[i].explored=explored
        if traversed != None:
            ground_points[i].traversed=traversed
        
def reset_evaluation():
    global ground_points
    
    for i in range(len(ground_points)):
        ground_points[i].evaluted = False
        
def generate_path():
    global search_radius, ground_points, search_count, current_path, current_target
    
    #reset_evaluation()
    current_search_count = search_count
    current_search_radius = search_radius
    search_point = current_path[-1] if len(current_path) > 0 else vehicle_position
    
    for _ in range(20):
        best = None
        best_value = 0
        
        for i in range(current_search_count):
            angle = 2 * math.pi * i / current_search_count
            
            x_pos = current_search_radius * math.cos(angle)
            y_pos = current_search_radius * math.sin(angle)
            
            x_pos += search_point[0]
            y_pos += search_point[1]
            
            value = evaluate_space(x_pos, y_pos)
            
            #print(x_pos, y_pos)
            if value > best_value:
                best = (x_pos, y_pos)
                
                value = best_value
                
        if best == None:
            current_search_radius += 3.0
            print(f"No Best, Expanding to radius: {current_search_radius}")
            current_search_count += 4
            continue
        
        set_area_state(*best, tape_radius, explored=True)
        current_path = [best]
        #current_target = best
        break

def update_wheel_power():
    global vehicle_history, current_target
    
    if len(current_path) == 0:
        #print("No Path")
        picobot_api.setMotorPower1(0)
        picobot_api.setMotorPower2(0)
        return
    
    target = current_target
    vehicle_position = vehicle_history[-1].position
    vehicle_angle = vehicle_history[-1].angle
    
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
        if angle_difference > 0:
            picobot_api.setMotorPower1(90)
            picobot_api.setMotorPower2(100)
        else:
            picobot_api.setMotorPower1(100)
            picobot_api.setMotorPower2(90)

def execute_task(function_s, pause, name = "Task"):
    global thread_errored, running
    while running:
        try:
            if isinstance(function_s, list):
                for function in function_s:
                    function()
            else:
                function_s()
            time.sleep(pause)
        except Exception as e:
            print(f"Error in {name}: {e}")
            thread_erroed = True

def start_async_task(function_s, pause, name = "Task"):
    thread = threading.Thread(
        target=execute_task,
        kwargs={
            "function_s": function_s,
            "pause": pause,
            "name": name
            }
        )
    thread.daemon = True
    thread.start()
    
    return thread

def await_button():
    while picobot_api.readButtons() != 0:
        pass
    while picobot_api.readButtons() == 0:
        pass
        
#await_button()
if not picobot_api.init():
    print("PICOBOT API FAILED TO INIT")
    sys.exit()
    
reset_encoders()
# rectify_camera()
start_async_task([calculate_movement, update_wheel_power], 0.05, "Movement Observation")
start_async_task([take_capture, generate_path], 0.05, "Observation")
# 
remote_control(False)
#show_brain()
#take_capture(True)

#running = False
#start_async_task([calculate_movement, update_wheel_power], 0.01, "Movement Execution")
#start_async_task([take_capture, generate_path], 0.1, "Observation")

#await_button()

print(vehicle_history)

running = False
# wait for threads to exit so wheels will stop
time.sleep(0.2)
picobot_api.setMotorPower1(0)
picobot_api.setMotorPower2(0)
try:
    cv.waitKey()
except:
    pass
sys.exit()