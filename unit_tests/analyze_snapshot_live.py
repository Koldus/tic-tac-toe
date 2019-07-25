import numpy as np
from naoqi import ALProxy
from nao_vision import NaoVision
import cv2 as cv
from PIL import Image
import logging
import traceback
import time

logging.basicConfig(format = '%(asctime)s;%(levelname)s;%(filename)s;%(message)s', level = logging.DEBUG)

# callibration config
nao_ip = "marvin.local"
nao_port = 9559
nao_camera_id = 1

# Take a snapshot from NAO camera
cam_proxy = ALProxy("ALVideoDevice", nao_ip, nao_port)
cam_proxy.setActiveCamera(1)

video_client = cam_proxy.subscribeCamera("python_client", 1, 2, 11, 5)
nao_image = cam_proxy.getImageRemote(video_client)

try:
    frame_tmp = np.asarray(bytearray(nao_image[6]), dtype=np.uint8)
    frame_tmp = frame_tmp.reshape((nao_image[1],nao_image[0],3))

    vision = NaoVision((frame_tmp.shape[0], frame_tmp.shape[1]), logging)

    while True:

        start = time.time()
        nao_image = cam_proxy.getImageRemote(video_client)
        end = time.time()
        print ('getImageRemote: ' + str( end - start ) )
        
        start = time.time()
        frame = np.asarray(bytearray(nao_image[6]), dtype=np.uint8)
        frame = frame.reshape((nao_image[1],nao_image[0],3))
        frame = frame[...,::-1]
        end = time.time()
        print ('frame shaping: ' + str( end - start ) )

        start = time.time()
        board_found, result, blob_size = vision.find_board(frame)
        end = time.time()
        print ('finding the board: ' + str( end - start ) )

        if board_found:
            print('Analysis ended, board found')
            break

except Exception, err:
    # Log the errors before game termination
    print(Exception)
    print(err)
    print('problem, test ended')

    traceback.print_exc()

finally:

    cam_proxy.unsubscribe(video_client)

