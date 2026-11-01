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

import math
import struct

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu

# MPU6050 registers
_PWR_MGMT_1 = 0x6B
_CONFIG = 0x1A          # DLPF
_GYRO_CONFIG = 0x1B
_ACCEL_CONFIG = 0x1C
_ACCEL_XOUT_H = 0x3B    # 14 bytes: accel xyz, temp, gyro xyz (big-endian int16)
_WHO_AM_I = 0x75

_GYRO_LSB_PER_DPS = 131.0     # +-250 deg/s range
_ACCEL_LSB_PER_G = 16384.0    # +-2 g range
_G = 9.80665


def _to_signed(raw: bytes) -> tuple[int, int, int]:
    """Three big-endian int16 values from six bytes."""
    return struct.unpack('>hhh', raw)


class ImuNode(Node):
    """Reads the MPU6050 over I2C and publishes /imu/data."""

    def __init__(self) -> None:
        super().__init__('imu_node')
        self.declare_parameter('bus', 1)
        self.declare_parameter('address', 0x68)
        self.declare_parameter('rate_hz', 100.0)
        self.declare_parameter('calib_seconds', 3.0)
        self.declare_parameter('calib_max_std', 0.01)
        self.declare_parameter('gyro_scale_z', 1.0)
        self.declare_parameter('gyro_var', 0.0004)
        self.declare_parameter('accel_var', 0.04)
        self.declare_parameter('frame_id', 'imu_link')
        from smbus2 import SMBus
        self._bus = SMBus(self.get_parameter('bus').value)
        self._addr = self.get_parameter('address').value
        self._configure()
        self._bias = self._calibrate()
        self._pub = self.create_publisher(Imu, '/imu/data', 10)
        self.create_timer(1.0 / self.get_parameter('rate_hz').value, self._publish)

    def _configure(self) -> None:
        who = self._bus.read_byte_data(self._addr, _WHO_AM_I)
        if who != 0x68:
            raise RuntimeError(f'WHO_AM_I {who:#x} at {self._addr:#x}, expected 0x68')
        self._bus.write_byte_data(self._addr, _PWR_MGMT_1, 0x01)   # wake, PLL on gyro X
        self._bus.write_byte_data(self._addr, _CONFIG, 0x03)        # DLPF ~44 Hz
        self._bus.write_byte_data(self._addr, _GYRO_CONFIG, 0x00)   # +-250 deg/s
        self._bus.write_byte_data(self._addr, _ACCEL_CONFIG, 0x00)  # +-2 g

    def _read(self) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        """(accel m/s^2, gyro rad/s), uncorrected."""
        d = bytes(self._bus.read_i2c_block_data(self._addr, _ACCEL_XOUT_H, 14))
        a = [v / _ACCEL_LSB_PER_G * _G for v in _to_signed(d[0:6])]
        g = [math.radians(v / _GYRO_LSB_PER_DPS) for v in _to_signed(d[8:14])]
        return tuple(a), tuple(g)

    def _read_gyro_z(self) -> float:
        return self._read()[1][2]

    def _calibrate(self) -> tuple[float, float, float]:
        """Mean gyro at rest. Refuses a noisy (moving) board instead of baking it in."""
        secs = self.get_parameter('calib_seconds').value
        n = max(10, int(secs * 100))
        samples = []
        for _ in range(n):
            samples.append(self._read()[1])
            rclpy.spin_once(self, timeout_sec=0.01)
        mean = tuple(sum(s[k] for s in samples) / n for k in range(3))
        std_z = math.sqrt(sum((s[2] - mean[2]) ** 2 for s in samples) / n)
        if std_z > self.get_parameter('calib_max_std').value:
            raise RuntimeError(
                f'gyro z std {std_z:.4f} rad/s during calibration exceeds '
                f'calib_max_std; keep the robot still and restart')
        self.get_logger().info(
            f'gyro bias rad/s x={mean[0]:.5f} y={mean[1]:.5f} z={mean[2]:.5f}, '
            f'z std {std_z:.5f} over {n} samples')
        return mean

    def _publish(self) -> None:
        try:
            a, g = self._read()
        except OSError as e:
            self.get_logger().warn(f'I2C read failed: {e}', throttle_duration_sec=2.0)
            return
        m = Imu()
        m.header.stamp = self.get_clock().now().to_msg()
        m.header.frame_id = self.get_parameter('frame_id').value
        m.orientation_covariance[0] = -1.0   # no orientation estimate
        m.angular_velocity.x = g[0] - self._bias[0]
        m.angular_velocity.y = g[1] - self._bias[1]
        m.angular_velocity.z = (g[2] - self._bias[2]) * self.get_parameter('gyro_scale_z').value
        gv = float(self.get_parameter('gyro_var').value)
        av = float(self.get_parameter('accel_var').value)
        for k in (0, 4, 8):
            m.angular_velocity_covariance[k] = gv
            m.linear_acceleration_covariance[k] = av
        m.linear_acceleration.x, m.linear_acceleration.y, m.linear_acceleration.z = a
        self._pub.publish(m)

    def close(self) -> None:
        self._bus.close()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = ImuNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
