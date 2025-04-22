import picobot_api
import cv2 as cv
import numpy as np

picobot_api.init()

capture = cv.VideoCapture(0)
capture.set(cv.CAP_PROP_FRAME_WIDTH, 320)
capture.set(cv.CAP_PROP_FRAME_HEIGHT, 240)

ret, cap = capture.read()

if ret:
    cap.resize(240, 320, 3)
    cap = np.flip(cap, 0)
    cap = np.flip(cap, 1)

    #img(cap)

# Detect the color green (DAS)
hsv = cv.cvtColor(cap,cv.COLOR_BGR2HSV)
lower_green = np.array([50,100,100]) # this is in HSV
upper_green = np.array([90,255,255])
# mask for threshold on green (ask Hannah for threshold deets)
mask = cv.inRange(hsv,lower_green,upper_green)
street_vision = cv.bitwise_and(cap,cap,mask=mask) #what the car will see to drive
car_vision = cv2.GaussianBlur(street_vision,(5,5),cv2.BORDER_DEFAULT)
center_point = [160,150]
center = car_vision[center_point[0]][center_point[1]]
horizon_point = [160,170]
horizon = car_vision[horizon_point[0]][horizon_point[1]]
if sum(horizon) > 50:
    msg("Keep driving sis")
else:
    msg("Ain't no way :skull:. Stop driving lil bro.")
# TESTING STUFF
#cv.imshow("test", cap)
#cv.imshow("mask",mask)
#cv.imshow("car_vision",car_vision)
img(car_vision)
while True:
    pass
