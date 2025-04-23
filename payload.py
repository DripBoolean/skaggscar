import picobot_api
import cv2 as cv
import numpy as np
import time
import math

wheel_diameter = 8.2
encoder_counts_per_revolution = 96 # From Docs
wheel_circumference = wheel_diameter * math.pi
encoder_tick_distance = wheel_circumference / encoder_counts_per_revolution
axel_distance = 10.7

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

    msg(e1)
    msg(e2)
    
    e1r = e1 * encoder_tick_distance
    e2r = e2 * encoder_tick_distance

    print(e1r)
    print(e2r)

    return wheel_movement(e1r, e2r, axel_distance)



if not picobot_api.init():
    msg("Failed to init")

picobot_api.resetEncoder1()
picobot_api.resetEncoder2()

msg("Setting power to max!")
picobot_api.setMotorPower1(100)
picobot_api.setMotorPower2(100)
time.sleep(0.5)
picobot_api.setMotorPower1(0)
picobot_api.setMotorPower2(0)

time.sleep(0.2)

msg(calculate_movement())

# msg(picobot_api.readEncoder1())
# time.sleep(0.01)
# msg(picobot_api.readEncoder2())

# HEIGHT = 600
# WIDTH = 800


# capture = cv.VideoCapture(0)
# capture.set(cv.CAP_PROP_FRAME_WIDTH, WIDTH)
# capture.set(cv.CAP_PROP_FRAME_HEIGHT, HEIGHT)

# ret, cap = capture.read()

# print(cap.shape)

# if ret:
#     cap.resize(HEIGHT, WIDTH, 3)
#     cap = np.flip(cap, 0)
#     cap = np.flip(cap, 1)

#     cv.imshow("cap", cap)
#     cv.waitKey()

# # Detect the color green (DAS)
# hsv = cv.cvtColor(cap,cv.COLOR_BGR2HSV)
# lower_green = np.array([50,100,100]) # this is in HSV
# upper_green = np.array([90,255,255])
# # mask for threshold on green (ask Hannah for threshold deets)
# mask = cv.inRange(hsv,lower_green,upper_green)
# street_vision = cv.bitwise_and(cap,cap,mask=mask) #what the car will see to drive
# car_vision = cv.GaussianBlur(street_vision,(5,5),cv.BORDER_DEFAULT)
# center_point = [160,150]
# center = car_vision[center_point[0]][center_point[1]]
# horizon_point = [160,170]
# horizon = car_vision[horizon_point[0]][horizon_point[1]]
# if sum(horizon) > 50:
#     msg("Keep driving sis")
# else:
#     msg("Ain't no way :skull:. Stop driving lil bro.")
# # TESTING STUFF
# #cv.imshow("test", cap)
# #cv.imshow("mask",mask)
# #cv.imshow("car_vision",car_vision)
# img(cap)
# while True:
#     pass
