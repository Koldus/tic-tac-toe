import numpy as np
import cv2 as cv
from nao_vision import NaoVision
import logging
import time

logging.basicConfig(format = '%(asctime)s;%(levelname)s;%(filename)s;%(message)s', level = logging.DEBUG)

i = 1
while True:
    im = cv.imread("unit_tests/snapshot_sm_" + str(i) + ".jpg")
    vision = NaoVision((im.shape[0], im.shape[1]), logging)

    start = time.time()
    board_found, result, blob_size = vision.find_board(im)
    end = time.time()
    print ('Find board function: ' + str( end - start ) )

    if board_found:
        print('BOARD FOUND')
        result = vision.fix_board_position(result)
    else:
        print('ERROR')

    width = int(result.shape[1] * 30 / 100)
    height = int(result.shape[0] * 30 / 100)
    dim = (width, height)
    # resize image
    resized = cv.resize(result, dim, interpolation = cv.INTER_AREA)

    cv.imshow("cropped", resized)
    cv.waitKey(0)

    i = i + 1
    if i > 1:
        break

print('Analysis ended')