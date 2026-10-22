"""LaserScan diagnostics.

Prints every ``period_s``: points per scan, scan rate, the fraction of returns
that are zero / inf / outside [range_min, range_max], and a 12-bin (30 deg)
histogram of where the invalid returns fall.

Motivation: on this hardware about two thirds of pings can come back with no
distance. That is a photonic problem, not a driver one, and this tool is how the
phase-1 lidar test is judged.

Parameter: period_s (default 2.0).
"""

from __future__ import annotations

import rclpy
from rclpy.node import Node


def _bin_index(angle: float, angle_min: float) -> int:
    raise NotImplementedError


class ScanStats(Node):
    """Accumulates /scan and prints the invalid-return histogram."""

    def __init__(self) -> None:
        raise NotImplementedError

    def _on_scan(self, msg) -> None:
        raise NotImplementedError

    def _report(self) -> None:
        raise NotImplementedError


def main(args=None) -> None:
    raise NotImplementedError
