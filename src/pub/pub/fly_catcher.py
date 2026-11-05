import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from rcl_interfaces.srv import SetParameters
from rcl_interfaces.msg import Parameter, ParameterType

class CatcherPub(Node):
    def __init__(self):
        super().__init__('pub')

        self.publisher = self.create_publisher(Twist, '/rogue/cmd_vel', 10)

        for i in range(5):
            self.set_speed(3.0)


    def set_heading(self, offset):
        control = Twist()
        control.angular.z = offset
        return control

    def set_speed(self, speed):
        control = Twist()
        control.linear.x = speed
        return control

def main():
    rclpy.init()
    catcher_pub = CatcherPub()
    rclpy.spin(catcher_pub)
    rclpy.shutdown()

if __name__ == "__main__":
    main()