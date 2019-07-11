import cv2 as cv
from nao_vision import NaoVision
from PIL import Image

im = Image.open("helpers/snapshot.jpg")
im.show()

vision = NaoVision((im[0], im[1]), False)

