"""LaserScan diagnostics.

Prints every ``period_s``: points per scan, scan rate, the fraction of returns
that are zero / inf / outside [range_min, range_max], and a 12-bin (30 deg)
histogram of where the invalid returns fall.

Motivation: on this hardware about two thirds of pings can come back with no
distance. That is a photonic problem, not a driver one, and this tool is how the
phase-1 lidar test is judged.
"""

from __future__ import annotations

import math
import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan

BINS = 12
BIN_WIDTH = 2.0 * math.pi / BINS


def _bin_index(angle: float, angle_min: float) -> int:
    rel = (angle - angle_min) % (2.0 * math.pi)
    return min(BINS - 1, int(rel / BIN_WIDTH))


class ScanStats(Node):
    def __init__(self) -> None:
        super().__init__("scan_stats")
        self.period_s = float(self.declare_parameter("period_s", 2.0).value)

        self._scans = 0
        self._points = 0
        self._zero = 0
        self._inf = 0
        self._out = 0
        self._valid = 0
        self._bin_invalid = [0] * BINS
        self._bin_total = [0] * BINS
        self._window_start = time.monotonic()
        self._last_scan_time: float | None = None
        self._intervals: list[float] = []

        self.create_subscription(LaserScan, "scan", self._on_scan, 10)
        self.create_timer(self.period_s, self._report)
        self.get_logger().info(
            "scan_stats: waiting for /scan, reporting every %.1f s" % self.period_s
        )

    def _on_scan(self, msg: LaserScan) -> None:
        now = time.monotonic()
        if self._last_scan_time is not None:
            self._intervals.append(now - self._last_scan_time)
            if len(self._intervals) > 50:
                self._intervals.pop(0)
        self._last_scan_time = now

        self._scans += 1
        n = len(msg.ranges)
        self._points += n

        for i, r in enumerate(msg.ranges):
            angle = msg.angle_min + i * msg.angle_increment
            b = _bin_index(angle, msg.angle_min)
            self._bin_total[b] += 1

            if r == 0.0:
                self._zero += 1
                self._bin_invalid[b] += 1
            elif math.isinf(r) or math.isnan(r):
                self._inf += 1
                self._bin_invalid[b] += 1
            elif r < msg.range_min or r > msg.range_max:
                self._out += 1
                self._bin_invalid[b] += 1
            else:
                self._valid += 1

    def _report(self) -> None:
        elapsed = time.monotonic() - self._window_start
        if self._scans == 0:
            self.get_logger().info("scan_stats: no /scan received yet")
            return

        pts_per_scan = self._points / self._scans
        total = self._points or 1
        rate = self._scans / elapsed if elapsed > 0 else 0.0
        inst_rate = (
            1.0 / (sum(self._intervals) / len(self._intervals))
            if self._intervals
            else 0.0
        )

        lines = [
            "--- /scan window: %d scans in %.1f s (%.1f Hz avg, %.1f Hz recent)" %
            (self._scans, elapsed, rate, inst_rate),
            "points/scan %.1f | valid %.1f%% | zero %.1f%% | inf %.1f%% | out-of-range %.1f%%" %
            (
                pts_per_scan,
                100.0 * self._valid / total,
                100.0 * self._zero / total,
                100.0 * self._inf / total,
                100.0 * self._out / total,
            ),
            "invalid per 30 deg bin (raw angle, 0 = first scan point):",
        ]
        for b in range(BINS):
            lo = math.degrees(b * BIN_WIDTH)
            hi = math.degrees((b + 1) * BIN_WIDTH)
            frac = 100.0 * self._bin_invalid[b] / self._bin_total[b] if self._bin_total[b] else 0.0
            bar = "#" * int(round(frac / 5.0))
            lines.append(
                "  %3.0f-%3.0f deg  %5.1f %%  %s" % (lo, hi, frac, bar)
            )
        self.get_logger().info("\n".join(lines))

        self._scans = self._points = self._valid = 0
        self._zero = self._inf = self._out = 0
        self._bin_invalid = [0] * BINS
        self._bin_total = [0] * BINS
        self._window_start = time.monotonic()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = ScanStats()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
