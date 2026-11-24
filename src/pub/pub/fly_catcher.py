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

from .direction_from_camera import ImageProcessor, CameraWorker 

class CatcherPub(Node):
    def __init__(self):
        super().__init__('pub')

        self.relative_angle = 0

        param = Parameter()
        param.name = "safety_override"
        param.value.type = ParameterType.PARAMETER_STRING
        param.value.string_value = "full"

        self.set_param('/rogue/motion_control/set_parameters', param)
        self.publisher = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.camera = CameraWorker()
        self.image_processor = ImageProcessor()

        self.create_timer(0.1, self.timer_callback)

    def set_param(self, param_path, param):
        client = self.create_client(SetParameters, param_path)
        while not client.wait_for_service(timeout_sec = 1.0):
            self.get_logger().info("Waiting")
        self.get_logger().info("Found: %s" % param_path)

        param_req = SetParameters.Request()
        param_req.parameters.append(param)

        future = client.call_async(param_req)
        rclpy.spin_until_future_complete(self, future, timeout_sec = 1.0)
        self.get_logger().info("Response: %s" % future.result())

    def set_heading(self, offset):
        control = Twist()
        control.angular.z = offset
        self.publisher.publish(control)

    def set_speed(self, speed):
        control = Twist()
        control.linear.x = speed
        self.publisher.publish(control)

    def timer_callback(self):
        angle_tolerance = 10
        dist_tolerance = 10
        center = 320, 240

        frame = self.camera.getImage()
        vector = self.image_processor.relativeVector(frame)
        self.relative_angle, distance = vector if vector is not None else (self.relative_angle, float("infinity"))

        # Set heading tests
        # control = relative_angle / 180
        # catcher_pub.set_heading(control)
        if abs(self.relative_angle) <= angle_tolerance:
            # do nothing
            pass
        elif self.relative_angle > 0:
            self.set_heading(1.0)
        elif self.relative_angle < 0:
            self.set_heading(-1.0)

        # Set accel tests (assumes the center of the frame is safe)
        if abs(distance) <= dist_tolerance:
            # do nothing
            pass
        elif distance > 0:
            self.set_speed(1.0)

def main():
    rclpy.init()
    catcher_pub = CatcherPub()
    rclpy.spin(catcher_pub)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
