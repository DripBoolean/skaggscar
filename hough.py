import picobot_api
import cv2 as cv
import numpy as np
picobot_api.init()
def displayLines(image, lines):
 if lines is not None:
  for line in lines:
   msg(line)
   x1, y1, x2, y2 = line.reshape(4)
   cv.line(image, (x1, y1), (x2, y2), (255, 0, 0), 10)
 return image
capture = cv.VideoCapture(0)
capture.set(cv.CAP_PROP_FRAME_WIDTH, 320)
capture.set(cv.CAP_PROP_FRAME_HEIGHT, 240)
ret, cap = capture.read()
if ret:
    cap.resize(240, 320, 3)
    cap = np.flip(cap, 0)
    cap = np.flip(cap, 1)
    cap = cap.astype(np.uint8).copy() 
hsv = cv.cvtColor(cap,cv.COLOR_BGR2HSV)
lower_green = np.array([50,100,100])
upper_green = np.array([90,255,255])
mask = cv.inRange(hsv,lower_green,upper_green)
edge = cv.Canny(mask, 50, 100)
lines = cv.HoughLinesP(edge, 4, np.pi/180, 100, maxLineGap=40)
msg(lines)
msg(f"{len(lines)} lines")
wlines=displayLines(cap, lines)
img(wlines)