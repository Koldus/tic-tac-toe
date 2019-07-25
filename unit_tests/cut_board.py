import numpy as np
import cv2 as cv
from nao_vision import NaoVision
import logging

logging.basicConfig(format = '%(asctime)s;%(levelname)s;%(filename)s;%(message)s', level = logging.DEBUG)

def shrink_image(image):
    width = int(image.shape[1] * 30 / 100)
    height = int(image.shape[0] * 30 / 100)
    dim = (width, height)
    resized = cv.resize(image, dim, interpolation = cv.INTER_AREA)
    return resized

i = 2
while True:
    im = cv.imread("unit_tests/snapshot_" + str(i) + ".jpg")
    vision = NaoVision((im.shape[0], im.shape[1]), logging)
    
    board_found, result, blob_size = vision.find_board(im)

    if board_found:
        vision.fix_board_position(result)
        board = vision.get_current_state(im)
    else:
        logging.error('Board not found!')

    cv.imshow("cropped", shrink_image(im))
    cv.waitKey(0)

    i = i + 1

    if i > 2:
        break