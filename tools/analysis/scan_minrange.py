"""Republish /scan_raw as /scan with every range below MINR (m, env var, default 0.6) set to inf.
Stand-in for a laser_filters range filter in the OI-8 offline replay (laser_filters is not installed)."""
import os, rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
MINR = float(os.environ.get('MINR', '0.6'))
def clip(m):
    m.ranges = [float('inf') if r < MINR else r for r in m.ranges]
    return m
class F(Node):
    def __init__(self):
        super().__init__('minrange')
        self.p = self.create_publisher(LaserScan, '/scan', qos_profile_sensor_data)
        self.create_subscription(LaserScan, '/scan_raw', lambda m: self.p.publish(clip(m)), qos_profile_sensor_data)
if __name__ == '__main__':
    rclpy.init(); rclpy.spin(F())
