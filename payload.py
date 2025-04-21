import picobot_api
import cv2 as cv

picobot_api.init()

capture = cv.VideoCapture(0)
capture.set(cv.CAP_PROP_FRAME_WIDTH, 320)
capture.set(cv.CAP_PROP_FRAME_WIDTH, 240)

ret, cap = capture.read()

if ret:
    msg(cap.shape)
    msg(cap)

    img(cap)

i = 0
while True:
    picobot_api.setLedColor(0, 0, 0, i % 255)
    msg(i)
    if i > 1000:
        i / 0
    i += 1
