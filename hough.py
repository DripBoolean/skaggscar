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
hsv = cv.cvtColor(cap,cv.COLOR_BGR2HSV)
lower_green = np.array([50,100,100])
upper_green = np.array([90,255,255])
mask = cv.inRange(hsv,lower_green,upper_green)
car_vision = cv.bitwise_and(cap,cap,mask=mask)
msg(cv.HoughLines(car_vision, 1 ,))
img(car_vision)

while True:
    pass
