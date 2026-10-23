#!/usr/bin/env python3
"""P1: check the RPLidar and save one scan as an image.

Run from the project root on the Pi:

    source ~/botenv/bin/activate
    python scripts/test_lidar.py [port]

Fetch the image with:

    scp robot@sherm-raspi.local:~/delivery-bot/scan.png .

Note on the printed scan rate: iter_scans(min_len=100) silently skips any
revolution with fewer than 100 valid returns, so 10 / elapsed underestimates the
true rotation rate. The real rate on our unit is 5-7 Hz (measured off the
new_scan flag; see CA3/docs/03_bringup.md). Use scripts/probe_echo_rate.py for
diagnostics instead of trusting this number.
"""
import sys
import time

import numpy as np
import matplotlib
matplotlib.use("Agg")                       # headless
import matplotlib.pyplot as plt
from rplidar import RPLidar, RPLidarException

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/rplidar"
BAUD = 115200

lidar = RPLidar(PORT, baudrate=BAUD, timeout=3)
try:
    print("Info:  ", lidar.get_info())
    health = lidar.get_health()
    print("Health:", health)
    if health[0] != "Good":
        print("Lidar reports a problem: check the cable and power.")

    lidar.start_motor()
    time.sleep(2)                           # spin up
    lidar.clean_input()

    scan, t0 = None, time.time()
    for i, scan in enumerate(lidar.iter_scans(max_buf_meas=3000, min_len=100)):
        print(f"scan {i}: {len(scan)} points")
        if i >= 9:
            break
    rate = 10 / (time.time() - t0)

    q, ang, dist = np.array(scan).T         # quality, angle (deg, clockwise), distance (mm)
    keep = (dist > 150) & (dist < 8000)
    a = -np.radians(ang[keep])              # convert to counter-clockwise
    d = dist[keep] / 1000.0
    x, y = d * np.cos(a), d * np.sin(a)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(x, y, s=2)
    ax.plot(0, 0, "r^", markersize=10)
    ax.set_aspect("equal")
    ax.grid(True)
    ax.set_xlabel("x (m): lidar 0 deg direction")
    ax.set_ylabel("y (m): left")
    fig.savefig("scan.png", dpi=120)
    print(f"Scan rate ~{rate:.1f} Hz. Saved scan.png: {keep.sum()} points, "
          f"nearest {d.min():.2f} m, farthest {d.max():.2f} m")
except RPLidarException as e:
    print("Lidar error:", e)
finally:
    lidar.stop()
    lidar.stop_motor()
    lidar.disconnect()
