import numpy as np
from naoqi import ALProxy
import cv2 as cv
from PIL import Image

# callibration config
board_dims = (7,7)
nao_ip = "172.16.200.19"
nao_port = 9559
nao_camera_id = 1

# termination criteria
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((7*7,3), np.float32)
objp[:,:2] = np.mgrid[0:7,0:7].T.reshape(-1,2)

# Arrays to store object points and image points from all the images.
objpoints = [] # 3d point in real world space
imgpoints = [] # 2d points in image plane.

# Take a snapshot from NAO camera
cam_proxy = ALProxy("ALVideoDevice", nao_ip, nao_port)
cam_proxy.setActiveCamera(nao_camera_id)
video_client = cam_proxy.subscribe("python_client", 3, 11, 5)
nao_image = cam_proxy.getImageRemote(video_client)
cam_proxy.unsubscribe(video_client)

# Get the image size and pixel array.
im_width = nao_image[0]
im_height = nao_image[1]
im_array = nao_image[6]

# Create an image object and save locally 
im = Image.frombytes("RGB", (im_width, im_height), im_array)
im = np.array(im)
im_gray = cv.cvtColor(im, cv.COLOR_BGR2GRAY)

# Find the chess board corners
ret, corners = cv.findChessboardCorners(im_gray, board_dims, None)

# If found, add object points, image points (after refining them)
if ret == True:
    objpoints.append(objp)
    corners2 = cv.cornerSubPix(im_gray, corners, (11,11), (-1,-1), criteria)
    imgpoints.append(corners)

    # Draw and display the corners
    cv.drawChessboardCorners(im, (7,6), corners2, ret)
    cv.imshow('img', im)
    cv.waitKey(5000)

    ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(objpoints, imgpoints, im_gray.shape[::-1], None, None)
    print(mtx)

else:
    print('Chessboard not found')

cv.destroyAllWindows()
