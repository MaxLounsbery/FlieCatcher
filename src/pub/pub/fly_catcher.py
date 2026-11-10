import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from rcl_interfaces.srv import SetParameters
from rcl_interfaces.msg import Parameter, ParameterType

class CatcherPub(Node):
    def __init__(self):
        super().__init__('pub')
        param = Parameter()
        param.name = "safety_override"
        param.value.type = ParameterType.PARAMETER_STRING
        param.value.string_value = "full"

        self.set_param('/rogue/motion_control/set_parameters', param)

        self.publisher = self.create_publisher(Twist, '/rogue/cmd_vel', 10)

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
    rclpy.init()
    catcher_pub = CatcherPub()
    rclpy.spin(catcher_pub)
    rclpy.shutdown()

if __name__ == "__main__":
    main()