import cv2 as cv
from nao_vision import NaoVision
import logging

logging.basicConfig(format = '%(asctime)s;%(levelname)s;%(filename)s;%(message)s', level = logging.DEBUG)

im = cv.imread("unit_tests/snapshot_sm_1.jpg")
vision = NaoVision((im.shape[0], im.shape[1]), logging)

current_state = [[0, -1, 0],
                 [0, 1, 0],
                 [0, 0, 0]]

vision.renderImage(current_state)