"""MPU6050 (GY-521) gyro driver.

Publishes sensor_msgs/Imu with the gyro and accelerometer in SI units.
Only the gyro z (yaw rate) is used by the EKF; the accelerometer is exposed
for Foxglove and future work, with its covariance marked.

The absolute yaw is NOT published: the MPU6050 has no magnetometer, so any
integrated yaw would drift. orientation_covariance[0] = -1 tells consumers
the orientation field is invalid.

Parameters (see config/drivers.yaml): bus, address, rate_hz, calib_seconds,
calib_max_std, gyro_scale_z, gyro_var, accel_var.
"""

from __future__ import annotations

import rclpy
from rclpy.node import Node


def _to_signed(raw: bytes) -> tuple[int, int, int]:
    raise NotImplementedError


class ImuNode(Node):
    """Reads the MPU6050 over I2C and publishes /imu/data."""

    def __init__(self) -> None:
        raise NotImplementedError

    def _configure(self) -> None:
        raise NotImplementedError

    def _read_gyro_z(self) -> float:
        raise NotImplementedError

    def _calibrate(self) -> float:
        raise NotImplementedError

    def _publish(self) -> None:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError


def main(args=None) -> None:
    raise NotImplementedError
