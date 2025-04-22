import picobot_api
import cv2 as cv

picobot_api.init()

capture = cv.VideoCapture(0)
capture.set(cv.CAP_PROP_FRAME_WIDTH, 320)
capture.set(cv.CAP_PROP_FRAME_WIDTH, 240)

ret, cap = capture.read()

cap.resize(240, 320, 3)

if ret:
    msg(cap.shape)
    msg(cap)

    img(cap)
