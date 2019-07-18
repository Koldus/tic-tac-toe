import numpy as np
import cv2 as cv
from nao_vision import NaoVision
import logging

logging.basicConfig(format = '%(asctime)s;%(levelname)s;%(filename)s;%(message)s', level = logging.DEBUG)

im = cv.imread("helpers/snapshot_2.jpg")
vision = NaoVision((im.shape[0], im.shape[1]), logging)

while not vision.find_board(im):
    pass

print('Board identified')