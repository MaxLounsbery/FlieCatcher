import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from rcl_interfaces.srv import SetParameters
from rcl_interfaces.msg import Parameter, ParameterType

#cam imports
from picamera2 import Picamera2, Preview
import numpy as np
import cv2
import time

class CatcherPub(Node):
    def __init__(self):
        super().__init__('pub')

        cam = CameraWorker()
        cam.getImage()
        self.get_logger().info("done!")
        # param = Parameter()
        # param.name = "safety_override"
        # param.value.type = ParameterType.PARAMETER_STRING
        # param.value.string_value = "full"

        # self.set_param('/rogue/motion_control/set_parameters', param)

        # self.publisher = self.create_publisher(Twist, '/rogue/cmd_vel', 10)
        # self.publisher.publish(self.set_speed(1.0))

    def set_param(self, param_path, param):
        client = self.create_client(SetParameters, param_path)
        while not client.wait_for_service(timeout_sec = 1.0):
            self.get_logger().info("Waiting")
        self.get_logger().info("Found: %s" % param_path)

        param_req = SetParameters.Request()
        param_req.parameters.append(param)

        future = client.call_async(param_req)
        rclpy.spin_until_future_complete(self, future)
        self.get_logger().info("Response: %s" % future.result())

    def set_heading(self, offset):
        control = Twist()
        control.angular.z = offset
        return control

    def set_speed(self, speed):
        control = Twist()
        control.linear.x = speed
        return control

def main():
    # angle_tolerance = 10
    # dist_tolerance = 10

    rclpy.init()
    # camera = CameraWorker()
    # image_processor = ImageProcessor()
    catcher_pub = CatcherPub()
    rclpy.spin(catcher_pub)

    # center = 320, 240

    # while (True):
    #     frame = camera.getImage()
    #     relative_angle = image_processor.relativeAngle(frame)
    #     target = image_processor.targetPoint(frame)
    #     # Set heading tests
    #     # control = relative_angle / 180
    #     # catcher_pub.set_heading(control)
    #     if abs(relative_angle) <= angle_tolerance:
    #         # do nothing
    #         pass
    #     elif relative_angle > 0:
    #         catcher_pub.set_heading(1)
    #     elif relative_angle < 0:
    #         catcher_pub.set_heading(-1)

    #     # Set accel tests (assumes the center of the frame is safe)
    #     distance = (target[0] - center[0]), (target[1] - center[1])
    #     if abs(distance) <= dist_tolerance:
    #         # do nothing
    #         pass
    #     elif distance > 0:
    #         catcher_pub.set_speed(1)

    rclpy.shutdown()

if __name__ == "__main__":
    main()

# cam code
class CameraWorker:
    def __init__(self):
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"size": (640, 480), "format": "RGB888"}, queue=False
        )
        self.picam2.configure(config)
        self.picam2.start()

    def getImage(self):
        self.picam2.capture_file("test_photo.jpg")
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
