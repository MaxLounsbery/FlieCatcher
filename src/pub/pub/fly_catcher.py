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

from direction_from_camera import ImageProcessor, CameraWorker 

class CatcherPub(Node):
    def __init__(self):
        super().__init__('pub')

        param = Parameter()
        param.name = "safety_override"
        param.value.type = ParameterType.PARAMETER_STRING
        param.value.string_value = "full"

        self.set_param('/rogue/motion_control/set_parameters', param)

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
    camera = CameraWorker()
    image_processor = ImageProcessor(imageX = 1920, imageY = 1080, centerX = 960, centerY = 540)
    frame = camera.getImage()
    cv2.imwrite("original.jpg", frame)
    cv2.imwrite("highlighted.jpg", image_processor.highlighted(frame))
    catcher_pub = CatcherPub()
    catcher_pub.get_logger().info("targetPoint: ")
    catcher_pub.get_logger().info(image_processor.targetPoint(frame))
    catcher_pub.get_logger().info("angleTarget: ")
    catcher_pub.get_logger().info(image_processor.angleToTarget(frame))
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
