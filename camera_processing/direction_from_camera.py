# import needs fixing maybe?
from picamera2 import Picamera2, Preview
import numpy as np
import cv2
import time


class cameraWorker:
    def __init__(self):
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"size": (640, 480), "format": "RGB888"}, queue=False
        )
        self.picam2.configure(config)
        self.picam2.start()

    def getImage(self):
        frame = self.picam2.capture_array()  # of shape (480, 640, 3), in BGR order
        return frame[:, :, ::-1]  # flip to RGB order


class imageProcessor:
    def __init__(
        self,
        targetR=255,
        targetG=0,
        targetB=0,
        imageX=640,
        imageY=480,
        centerX=320,
        centerY=240,
    ):
        pass

    def direction(self, image):
        pass
