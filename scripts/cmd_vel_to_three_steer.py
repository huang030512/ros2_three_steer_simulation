#!/usr/bin/env python3
"""Subscribe to geometry_msgs/Twist (cmd_vel), publish steer + wheel group commands."""
import math

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray

# 与 URDF 轮心一致（base_link 平面内，米）
RX = (0.32, -0.16, -0.16)
RY = (0.0, 0.277128, -0.277128)
R_WHEEL = 0.07
EPS = 1e-4


class CmdVelToThreeSteer(Node):
    def __init__(self):
        super().__init__('cmd_vel_to_three_steer')
        self.declare_parameter('invert_wheel_sign', -1.0)
        self._sign = float(self.get_parameter('invert_wheel_sign').value)

        self._pub_steer = self.create_publisher(Float64MultiArray, '/steer_group_controller/commands', 10)
        self._pub_wheel = self.create_publisher(Float64MultiArray, '/wheel_group_controller/commands', 10)
        self.create_subscription(Twist, 'cmd_vel', self._cb, 10)

    def _cb(self, msg: Twist):
        vx = msg.linear.x
        vy = msg.linear.y
        wz = msg.angular.z

        steer = [0.0] * 3
        wheel = [0.0] * 3
        for i in range(3):
            vxi = vx - wz * RY[i]
            vyi = vy + wz * RX[i]
            spd = math.hypot(vxi, vyi)
            if spd < EPS:
                steer[i] = 0.0
                wheel[i] = 0.0
                continue
            steer[i] = math.atan2(vyi, vxi)
            wheel[i] = self._sign * spd / R_WHEEL

        smsg = Float64MultiArray()
        smsg.data = steer
        self._pub_steer.publish(smsg)
        wmsg = Float64MultiArray()
        wmsg.data = wheel
        self._pub_wheel.publish(wmsg)


def main():
    rclpy.init()
    node = CmdVelToThreeSteer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
