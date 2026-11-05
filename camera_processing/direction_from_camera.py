# import needs fixing maybe?
from picamera2 import Picamera2, Preview
import numpy as np
import cv2
import time


class CameraWorker:
    def __init__(self):
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"size": (640, 480), "format": "RGB888"}, queue=False
        )
        self.picam2.configure(config)
        self.picam2.start()

    def getImage(self):
        return self.picam2.capture_array()  # of shape (480, 640, 3), in BGR order


class ImageProcessor:
    def __init__(
        self,
        targetR=255,
        targetG=0,
        targetB=0,
        # size of given images
        imageX=640,
        imageY=480,
        # what x, y on the image represents a centered point
        centerX=320,
        centerY=240,
    ):
        self.targetR = targetR / 255
        self.targetG = targetG / 255
        self.targetB = targetB / 255

        self.imageX = imageX
        self.imageY = imageY

        self.centerX = centerX
        self.centerY = centerY

    def highlited(self, image):
        """
        given a RGB888 image of dimensions (imageX, imageY, 3) in BGR order 
        
        returns a 'highlighted' int16_t version that prioritizes targetted colors 
        and disincentivizes untargeted colors
        """
        b, g, r = np.split(image, 3, axis=2)

        # gets their distance from 255/2, represents how strongly we want each color
        # white light will be discounted twice if the color we want is pure
        r = (2 * self.targetR - 1) * r.astype(np.int16)
        g = (2 * self.targetG - 1) * g.astype(np.int16)
        b = (2 * self.targetB - 1) * b.astype(np.int16)

        return r + g + b
