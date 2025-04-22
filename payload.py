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
    
    img(cap)
