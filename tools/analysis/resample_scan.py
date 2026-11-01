"""Republish /scan_raw as /scan on a 720-beam grid (nearest beam), as angle_compensate does roughly."""
import math, rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
N, AMIN, INC = 720, -3.124, 0.00871
class R(Node):
    def __init__(self):
        super().__init__('resample')
        self.p = self.create_publisher(LaserScan, '/scan', qos_profile_sensor_data)
        self.create_subscription(LaserScan, '/scan_raw', self.cb, qos_profile_sensor_data)
    def cb(self, m):
        o = LaserScan(); o.header = m.header
        o.angle_min, o.angle_increment = AMIN, INC
        o.angle_max = AMIN + (N - 1) * INC
        o.time_increment, o.scan_time = m.time_increment, m.scan_time
        o.range_min, o.range_max = m.range_min, m.range_max
        r, it = [], []
        for k in range(N):
            a = AMIN + k * INC
            i = round((a - m.angle_min) / m.angle_increment)
            ok = 0 <= i < len(m.ranges)
            r.append(m.ranges[i] if ok else float('inf'))
            it.append(m.intensities[i] if ok and m.intensities else 0.0)
        o.ranges, o.intensities = r, it
        self.p.publish(o)
rclpy.init(); rclpy.spin(R())
