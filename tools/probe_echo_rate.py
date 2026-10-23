#!/usr/bin/env python3
"""Diagnostic: where do the lidar's echoes go?

Counts every measurement packet for N seconds (not just the ones with a
distance), then reports per-15-degree-sector:

    nodes   how many packets the sensor sent in that sector
    echo%   how many of them returned a distance
    medQ    median quality of the returning ones
    medD_m  median distance of the returning ones
    maxD_m  longest return in that sector

Reading it: a sector with echo% near 100 and a short median distance is a solid
nearby surface. A sector with 0% and long returns in its neighbours is an
opening (beam escapes - normal). A sector with low echo% but a *tight* median
distance means a surface is there and the light is not coming back - optics, not
geometry.

    source ~/botenv/bin/activate
    python probe_echo_rate.py [seconds] [port]

Always stops the motor and disconnects, even on error.
"""
import sys
import time

import numpy as np
from rplidar import RPLidar

SECONDS = float(sys.argv[1]) if len(sys.argv) > 1 else 6.0
PORT = sys.argv[2] if len(sys.argv) > 2 else "/dev/rplidar"
BAUD = 115200

lidar = RPLidar(PORT, baudrate=BAUD, timeout=3)
try:
    print("info  :", lidar.get_info())
    print("health:", lidar.get_health())

    lidar.start_motor()
    time.sleep(2)
    lidar.clean_input()

    angles, dists, quals = [], [], []
    t0 = time.time()
    for _new_scan, q, a, d in lidar.iter_measures(max_buf_meas=3000):
        angles.append(a)
        dists.append(d)
        quals.append(q)
        if time.time() - t0 >= SECONDS:
            break
    elapsed = time.time() - t0

    ang = np.array(angles)
    dist = np.array(dists)
    qual = np.array(quals)

    # Revolution boundaries come from the new_scan flag: counting backward angle
    # jumps over-counts, because sampling jitter is ~12% of transitions.
    revs = int((np.array([True] + list(np.diff(ang) < 0))).sum())
    echo = dist > 0

    print(f"\n{elapsed:.1f}s  raw nodes {len(ang)} ({len(ang) / elapsed:.0f}/s)  "
          f"~{revs / elapsed:.2f} Hz rotation")
    print(f"echo rate overall: {100 * echo.mean():.0f}%  "
          f"({echo.sum()} returning, {(~echo).sum()} silent)")

    print(f"\n{'sector':<10} {'nodes':>6} {'echo%':>6} {'medQ':>5} {'medD_m':>8} {'maxD_m':>8}")
    for lo in range(0, 360, 15):
        m = (ang >= lo) & (ang < lo + 15)
        if not m.any():
            print(f"{lo:>3}-{lo + 15:<4} {'-':>6}")
            continue
        hit = echo[m]
        if hit.any():
            med_q = np.median(qual[m][hit])
            med_d = np.median(dist[m][hit]) / 1000.0
            max_d = dist[m][hit].max() / 1000.0
        else:
            med_q = med_d = max_d = float("nan")
        print(f"{lo:>3}-{lo + 15:<4} {m.sum():6d} {100 * hit.mean():6.0f} "
              f"{med_q:5.0f} {med_d:8.2f} {max_d:8.2f}")
finally:
    lidar.stop()
    lidar.stop_motor()
    lidar.disconnect()
