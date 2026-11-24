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
        self.publisher = self.create_publisher(Twist, '/rogue/cmd_vel', 10)
        self.camera = CameraWorker()
        # TODO: tune angle offset
        self.image_processor = ImageProcessor(baseAngle=90)

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
        control.angular.z = float(offset)
        self.publisher.publish(control)

    def set_speed(self, speed):
        control = Twist()
        control.linear.x = float(speed)
        self.publisher.publish(control)

    def set_twist(self, speed, offset):
        control = Twist()
        control.linear.x = float(speed)
        control.angular.z = float(offset)
        self.publisher.publish(control)

    def timer_callback(self):
        ANGLE_TOLERANCE = 10
        DIST_TOLERANCE = 30
        MIN_ANGLE = -45
        MAX_ANGLE = 45

        frame = self.camera.getImage()
        vector = self.image_processor.relativeVector(frame)

        if vector is None:
            self.relative_angle = 0
            self.distance = 0
        else:
            self.relative_angle = vector[0]
            self.distance = vector[1]
            print(f"Drone detected at distance: {self.distance} and relative angle: {self.relative_angle}")
        # self.relative_angle, distance = vector if vector is not None else (self.relative_angle, float("infinity"))

        
        speed, heading = 0,0
        # Set heading tests
        # control = relative_angle / 180
        # catcher_pub.set_heading(control)
        if abs(self.relative_angle) <= ANGLE_TOLERANCE:
            # do nothing, heading stays 0
            pass
        elif self.relative_angle > 0:
            # NOTE: might need to flip these back?
            #       if camera is on floor looking up, heading might be reversed
            heading = -1
        elif self.relative_angle < 0:
            heading = 1

        # Set accel tests (assumes the center of the frame is safe)
        if self.distance > DIST_TOLERANCE and MIN_ANGLE < self.relative_angle < MAX_ANGLE:
            speed = 1

        self.set_twist(speed, heading)

def main():
    rclpy.init()
    catcher_pub = CatcherPub()
    rclpy.spin(catcher_pub)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
