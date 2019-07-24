import numpy as np
import cv2 as cv
from nao_vision import NaoVision
import logging

logging.basicConfig(format = '%(asctime)s;%(levelname)s;%(filename)s;%(message)s', level = logging.DEBUG)

i = 1
while True:
    im = cv.imread("unit_tests/snapshot_" + str(i) + ".jpg")
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

    i = i + 1

    if i > 18:
        break