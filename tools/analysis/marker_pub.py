#!/usr/bin/env python3
"""Publish std_msgs/String markers on /marker from ONE publisher, like Foxglove's Publish panel.

    python3 tools/analysis/marker_pub.py "push start" 3 "push end"     text, wait seconds, text...

`ros2 topic pub --once` makes a fresh publisher per message, and the recorder may not have
matched it yet, so the first marker can be lost; a persistent publisher does not lose them.
"""
import sys
import time

import rclpy
from std_msgs.msg import String

rclpy.init()
node = rclpy.create_node('marker_pub')
pub = node.create_publisher(String, '/marker', 10)
time.sleep(2)   # let the recorder match this publisher
for arg in sys.argv[1:]:
    if arg.isdigit():
        time.sleep(int(arg))
    else:
        pub.publish(String(data=arg))
        time.sleep(0.5)
node.destroy_node()
rclpy.shutdown()
