import picobot_api
import math
import time
import cv2 as cv
import numpy as np
import threading
import sys
import pygame
import waveplayer

pygame.init()

camera_width = 160
camera_height = 120

input_delay = 0.5
input_history = []

def green_mask(img):
    print(img)
    hsv = cv.cvtColor(img,cv.COLOR_BGR2HSV)
    
    lower_green = np.array([40,60,80]) # this is in HSV
    upper_green = np.array([70,255,255])
    # mask for threshold on green (ask Hannah for threshold deets)
    mask = cv.inRange(hsv,lower_green,upper_green)
    return mask
    

def photo(capture):
    global camera_width, camera_height

    ret, cap = capture.read()
    
    if ret:
        #cap.resize(camera_height, camera_width, 3)
        return (True, cap)
    
    return (False, None)

def set_wheels(left, right):
    picobot_api.setMotorPower1(left)
    picobot_api.setMotorPower2(right)

def rectify_camera():
    """ Uses pygame to flip cameras x and y (Cant be done in opencv as far as i know) """
    import pygame.camera
    pygame.camera.init()
    cam = pygame.camera.Camera("/dev/video0", (800, 600), "RGB")
    cam.start()
    cam.set_controls(True, True, 50)
    cam.stop()
    
def await_button():
    while picobot_api.readButtons() != 0:
        pass
    while picobot_api.readButtons() == 0:
        pass
    
def distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    
def mag(x, y):
    return math.sqrt(x ** 2 + y ** 2)

def ball_expansion(img, x, y, saturation_value, step=5):
    current_size = 0
    print(x, y)
    while True:
        current_size += step
        count = 0
        for iy, row in enumerate(img):
            for ix, pixel in enumerate(row):
                dx = ix - x
                dy = iy - y
                
                dist = math.sqrt(dx ** 2 + dy ** 2)
                
                if dist > current_size:
                    continue
                
                if pixel == 255:
                    count += 1
        if count > saturation_value:
            return current_size
        if current_size > camera_height:
            return camera_height
                
                    
    
def four_ball(img):
    global camera_width, camera_height
    
    distances = [[] for _ in range(4)]  
    
    for iy, row in enumerate(img):
        for ix, pixel in enumerate(row):
            from_bottom = camera_height - iy
            from_right = camera_width - ix
            
            if pixel == 255:
                #index = iy * camera_width + ix
                distances[0].append(mag(ix, iy))
                distances[1].append(mag(from_right, iy))
                distances[2].append(mag(ix, from_bottom))
                distances[3].append(mag(from_right, from_bottom))
    
    if len(distances[0]) <= 5:
        return [None] * 4
    
    output = [0] * 4
    for i in range(4):
        distances[i].sort()
        
        output[i] = distances[i][5]
        
    return output
           
def is_green(color):
    return color.g > color.r + 20 and color.g > color.b + 20

def four_value(img, pixels = 5):
    global camera_width, camera_height
    g_search = 150
    
    res = [0] * 4
    count = 0
    for i in range(camera_width):
        count += is_green(img.get_at((i, 0)))
        if count > pixels:
            res[0] = i
            break
        
    count = 0
    for i in range(camera_width):
        count += is_green(img.get_at((camera_width - i - 1, 0)))
        if count > pixels:
            res[1] = i
            break
            
    count = 0
    for i in range(camera_width):
        count += is_green(img.get_at((i, camera_height - 1)))
        if count > pixels:
            res[2] = i
            break
        
    count = 0
    for i in range(camera_width):
        count += is_green(img.get_at((camera_width - i -1, camera_height - 1)))
        if count > pixels:
            res[3] = i
            break
    return res
        
def button_pressed():
    return picobot_api.readButtons() != 0

def pixel_count(mask):
    count = 0
    for iy, row in enumerate(mask):
        for ix, pixel in enumerate(row):
            count += pixel == 255
    return count
    
#rectify_camera()
import pygame.camera
pygame.camera.init()
cam = pygame.camera.Camera("/dev/video0", (camera_width, camera_height), "RGB")
cam.start()
cam.set_controls(True, True, 50)
picobot_api.init()
# start = time.time()
# cam.get_image()
# print(f"Elapsed: {time.time() - start}")
# sys.exit()
# 
await_button()
print(cam.get_image().get_at((100, 100)).g)


time.sleep(0.2)

ds=pygame.display.set_mode((camera_width, camera_height))
# music_thread = threading.Thread(target = waveplayer.play, kwargs = {"filename": "music/ft2.wav"})
# music_thread.daemon = True
# music_thread.start()
was_left = False
is_lost = False
while not button_pressed():
    pygame.event.pump()
    keys=pygame.key.get_pressed()
    if keys[pygame.K_ESCAPE]:
        break
    #ret, img = photo(capture)
    #if not ret:
    #    print("error")
    #mask = green_mask(img)
#     if pixel_count(mask) > 10:
#         set_wheels(30, 70)
#     else:
#         set_wheels(70, 30)
    
    image = cam.get_image()
    values = four_value(image)
        
    ds.fill((0,0,0))
     #read camera in as a surface
    ds.blit(image,(0,0))    #draw the image on the display window
    pixels=pygame.surfarray.pixels3d(image)
    pygame.display.update()
    
    print(values)

    left_total = values[0] + values[2]
    right_total = values[1] + values[3]
    
#     if right_total == 0 and left_total == 0:
#         if is_lost:
#             set_wheels(-100, 100)
#         elif was_left:
#             is_lost = True
#             set_wheels(80, 0)
#         else:
#             is_lost = True
#             set_wheels(0, 80)

#     if left_total == 0 and right_total == 0:
#         if was_left:
#             input_history.append((-80, 80, time.time()))
#         else:
#             input_history.append((80, -80, time.time()))
#             
#     elif left_total < right_total:
#         was_left = True
#         input_history.append((60, 80, time.time()))
#         #set_wheels(0, 80)
#     else:
#         was_left = False
#         input_history.append(80, 0, time.time()))
#         set_wheels(80, 0)
    if left_total == 0 and right_total == 0:   
        if was_left:
            set_wheels(-80, 80)
        else:
            set_wheels(80, -80)
    elif left_total < right_total:
        was_left = True
        set_wheels(60, 80)
    else:
        was_left = False
        set_wheels(80, 60)
        
set_wheels(0, 0)
sys.exit()
