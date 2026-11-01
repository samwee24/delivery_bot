#!/usr/bin/env python3
"""Where do the lidar's missing (inf) ranges fall, by angle?

Reads a rosbag2 (mcap) with /scan and reports the overall fraction of non-finite
ranges and a per-30-degree-bin table in the `laser` frame (0 deg = the lidar's own
zero, counter-clockwise positive). Angles are computed per message because the
beam count varies from scan to scan (1132-1143 on the A1M8).

    source /opt/ros/jazzy/setup.bash
    python3 tools/analysis/inf_histogram.py ~/ros2_ws/bags/still_2026-10-30
"""
import math
import sys

import rosbag2_py
from rclpy.serialization import deserialize_message
from sensor_msgs.msg import LaserScan

BIN_DEG = 30
N_BINS = 360 // BIN_DEG

reader = rosbag2_py.SequentialReader()
reader.open(rosbag2_py.StorageOptions(uri=sys.argv[1], storage_id="mcap"),
            rosbag2_py.ConverterOptions("", ""))

bad = [0] * N_BINS
total = [0] * N_BINS
scans = 0
while reader.has_next():
    topic, data, _ = reader.read_next()
    if topic != "/scan":
        continue
    scan = deserialize_message(data, LaserScan)
    scans += 1
    for i, r in enumerate(scan.ranges):
        deg = math.degrees(scan.angle_min + i * scan.angle_increment)
        b = int((deg + 180) // BIN_DEG) % N_BINS
        total[b] += 1
        if not math.isfinite(r):
            bad[b] += 1

print(f"scans {scans}  beams {sum(total)}  inf {sum(bad)}  "
      f"({100 * sum(bad) / sum(total):.1f}%)")
print(" bin (deg)      inf%")
for b in range(N_BINS):
    lo = b * BIN_DEG - 180
    pct = 100 * bad[b] / total[b]
    print(f"{lo:5d}..{lo + BIN_DEG:<4d}  {pct:6.1f}  {'#' * round(pct / 2)}")
