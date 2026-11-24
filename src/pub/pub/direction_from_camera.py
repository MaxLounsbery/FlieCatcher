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
        # angle (degrees) off of the center point that relative angles are measured from
        # 0 is straight right of center, increasing counterclockwise (90 is straight up)
        baseAngle=0,
    ):
        self.targetR = targetR / 255
        self.targetG = targetG / 255
        self.targetB = targetB / 255

        self.imageX = imageX
        self.imageY = imageY

        self.centerX = centerX
        self.centerY = centerY

        self.baseAngle = baseAngle

    def highlighted(self, image, blur=False):
        """
        given a RGB888 image of dimensions (imageX, imageY, 3) in BGR order 
        
        returns a 'highlighted' int16_t version that prioritizes targetted colors
        and disincentivizes untargeted colors

        if blur, the result is gaussian blurred so single noisy pixels are smoothed out
        """
        b, g, r = np.split(image, 3, axis=2)

        # gets their distance from 255/2, represents how strongly we want each color
        # white light will be discounted twice if the color we want is pure
        r = (2 * self.targetR - 1) * r.astype(np.int16)
        g = (2 * self.targetG - 1) * g.astype(np.int16)
        b = (2 * self.targetB - 1) * b.astype(np.int16)

        highlight = r + g + b

        # GaussianBlur drops the single channel axis, so add it back to keep the shape the same
        if blur:
            highlight = cv2.GaussianBlur(highlight, (15, 15), 0)[:, :, np.newaxis]

        return highlight

    def targetPoint(self, image):
        """
        given a RGB888 image of dimensions (imageX, imageY, 3) in BGR order

        returns the (x, y) of the most 'targeted' point in the image,
        or None if nothing in the image is targeted
        """
        highlight = self.highlighted(image, blur=True)[:, :, 0]

        # flat index of the strongest point, converted back to (row, col)
        y, x = np.unravel_index(np.argmax(highlight), highlight.shape)

        # nothing leans towards the target color, so there is no target
        if highlight[y, x] <= 0:
            return None

        return int(x), int(y)

    def angleToTarget(self, image):
        """
        given a RGB888 image of dimensions (imageX, imageY, 3) in BGR order

        returns the angle (degrees) from the center point to the target point,
        0 is straight right of center, increasing counterclockwise, in the range (-180, 180]
        returns None if there is no target
        """
        target = self.targetPoint(image)
        if target is None:
            return None

        x, y = target
        dx = x - self.centerX
        # image y grows downwards, flip it so up is positive
        dy = self.centerY - y

        return float(np.degrees(np.arctan2(dy, dx)))

    def relativeAngle(self, image):
        """
        given a RGB888 image of dimensions (imageX, imageY, 3) in BGR order

        returns the angle (degrees) of the target point relative to baseAngle,
        positive is counterclockwise of baseAngle, in the range (-180, 180]
        returns None if there is no target
        """
        angle = self.angleToTarget(image)
        if angle is None:
            return None

        # wrap the difference back into (-180, 180]
        relative = (angle - self.baseAngle) % 360
        if relative > 180:
            relative -= 360

        return relative

    def relativeVector(self, image):
        """
        given a RGB888 image of dimensions (imageX, imageY, 3) in BGR order

        returns (angle, distance) of the target point, where angle (degrees) is relative to
        baseAngle in the range (-180, 180] and distance is pixels from the center point
        returns None if there is no target
        """
        target = self.targetPoint(image)
        if target is None:
            return None

        x, y = target
        dx = x - self.centerX
        # image y grows downwards, flip it so up is positive
        dy = self.centerY - y

        # wrap the difference back into (-180, 180]
        relative = (float(np.degrees(np.arctan2(dy, dx))) - self.baseAngle) % 360
        if relative > 180:
            relative -= 360

        return relative, float(np.hypot(dx, dy))
