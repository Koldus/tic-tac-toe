import numpy as np
from naoqi import ALProxy
import cv2 as cv
from PIL import Image
import os

# callibration config
nao_ip = "marvin.local"
nao_port = 9559
nao_camera_id = 1

# Take a snapshot from NAO camera
cam_proxy = ALProxy("ALVideoDevice", nao_ip, nao_port)
cam_proxy.setActiveCamera(1)

video_client = cam_proxy.subscribe("python_client", 3, 11, 5)
nao_image = cam_proxy.getImageRemote(video_client)
cam_proxy.unsubscribe(video_client)

# Get the image size and pixel array.
im_width = nao_image[0]
im_height = nao_image[1]
im_array = nao_image[6]

# Create a PIL Image from our pixel array.
im = Image.frombytes("RGB", (im_width, im_height), im_array)

# Save the image.
im.save(os.path.join("helpers", "snapshot.jpg"), "JPEG")

im.show()