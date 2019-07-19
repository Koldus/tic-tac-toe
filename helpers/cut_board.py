import numpy as np
import cv2 as cv
from nao_vision import NaoVision
import logging

logging.basicConfig(format = '%(asctime)s;%(levelname)s;%(filename)s;%(message)s', level = logging.DEBUG)

im = cv.imread("helpers/snapshot_7.jpg")
vision = NaoVision((im.shape[0], im.shape[1]), logging)

board = vision.get_current_state(im)
print(board)

width = int(im.shape[1] * 30 / 100)
height = int(im.shape[0] * 30 / 100)
dim = (width, height)
# resize image
resized = cv.resize(im, dim, interpolation = cv.INTER_AREA)

cv.imshow("cropped", resized)
cv.waitKey(0)