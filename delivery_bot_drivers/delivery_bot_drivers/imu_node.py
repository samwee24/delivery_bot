"""MPU6050 (GY-521) gyro driver.

Publishes sensor_msgs/Imu with the gyro and accelerometer in SI units.
Only the gyro z (yaw rate) is used by the EKF; the accelerometer is exposed
for Foxglove and future work, with its covariance marked.

The absolute yaw is NOT published: the MPU6050 has no magnetometer, so any
integrated yaw would drift. orientation_covariance[0] = -1 tells consumers
the orientation field is invalid.
"""

from __future__ import annotations

import math
import statistics
import struct
import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu

try:
    from smbus2 import SMBus
except ImportError:  # pragma: no cover - only on a machine without the apt package
    SMBus = None

# Register map (MPU6050 datasheet, register map section)
REG_SMPLRT_DIV = 0x19
REG_CONFIG = 0x1A
REG_GYRO_CONFIG = 0x1B
REG_ACCEL_CONFIG = 0x1C
REG_ACCEL_XOUT_H = 0x3B
REG_PWR_MGMT_1 = 0x6B

GYRO_SCALE = 131.0        # LSB per deg/s at +-250 deg/s
ACCEL_SCALE = 16384.0     # LSB per g at +-2 g
GRAVITY = 9.80665


def _to_signed(raw: bytes) -> tuple[int, int, int]:
    return struct.unpack(">hhh", raw)


class ImuNode(Node):
    def __init__(self) -> None:
        super().__init__("imu_node")

        self.bus_number = int(self.declare_parameter("bus", 1).value)
        self.address = int(self.declare_parameter("address", 0x68).value)
        self.rate_hz = float(self.declare_parameter("rate_hz", 100.0).value)
        self.calib_seconds = float(
            self.declare_parameter("calib_seconds", 3.0).value
        )
        self.calib_max_std = float(
            self.declare_parameter("calib_max_std", 0.01).value
        )
        # Calibrated later by spinning the robot a known number of turns and
        # comparing the integrated gyro z with the lidar (docs/plan.md phase 3).
        self.gyro_scale_z = float(
            self.declare_parameter("gyro_scale_z", 1.0).value
        )
        self.gyro_var = float(self.declare_parameter("gyro_var", 0.0004).value)
        self.accel_var = float(self.declare_parameter("accel_var", 0.04).value)

        if SMBus is None:
            raise RuntimeError(
                "smbus2 is not installed; on the Pi run: "
                "sudo apt install python3-smbus2"
            )

        self._bus = SMBus(self.bus_number)
        self._configure()
        self._bias_z = self._calibrate()

        self._pub = self.create_publisher(Imu, "imu/data", 10)
        self.create_timer(1.0 / self.rate_hz, self._publish)
        self.get_logger().info(
            "IMU ready at 0x%02x on i2c-%d, %.0f Hz, gyro-z bias %.4f rad/s"
            % (self.address, self.bus_number, self.rate_hz, self._bias_z)
        )

    # --- device setup ---------------------------------------------------
    def _configure(self) -> None:
        self._bus.write_byte_data(self.address, REG_PWR_MGMT_1, 0x00)  # wake
        self._bus.write_byte_data(
            self.address, REG_CONFIG, 0x03
        )  # DLPF ~44 Hz
        self._bus.write_byte_data(self.address, REG_GYRO_CONFIG, 0x00)  # +-250 dps
        self._bus.write_byte_data(self.address, REG_ACCEL_CONFIG, 0x00)  # +-2 g
        time.sleep(0.1)  # let the DLPF settle before calibration

    def _read_gyro_z(self) -> float:
        raw = self._bus.read_i2c_block_data(self.address, 0x45, 2)
        return struct.unpack(">h", raw)[0] / GYRO_SCALE * math.pi / 180.0

    def _calibrate(self) -> float:
        samples_needed = max(1, int(self.calib_seconds * self.rate_hz))
        period = 1.0 / self.rate_hz
        for attempt in range(1, 4):
            samples = []
            for _ in range(samples_needed):
                samples.append(self._read_gyro_z())
                time.sleep(period)
            mean = statistics.fmean(samples)
            std = statistics.pstdev(samples)
            if std <= self.calib_max_std:
                self.get_logger().info(
                    "gyro calibration %d/3: bias %.4f rad/s, std %.4f rad/s"
                    % (attempt, mean, std)
                )
                return mean
            self.get_logger().error(
                "gyro calibration %d/3: std %.4f rad/s > %.4f — "
                "is the robot still? retrying"
                % (attempt, std, self.calib_max_std)
            )
        raise RuntimeError(
            "gyro calibration failed 3 times; robot moved or IMU is faulty"
        )

    # --- streaming ------------------------------------------------------
    def _publish(self) -> None:
        try:
            gyro_raw = self._bus.read_i2c_block_data(self.address, 0x43, 6)
            accel_raw = self._bus.read_i2c_block_data(
                self.address, REG_ACCEL_XOUT_H, 6
            )
        except OSError as exc:
            self.get_logger().warn("I2C read failed: %s" % exc, throttle_duration_sec=2.0)
            return

        gx, gy, gz = _to_signed(bytes(gyro_raw))
        ax, ay, az = _to_signed(bytes(accel_raw))

        deg_to_rad = math.pi / 180.0
        msg = Imu()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "imu_link"

        # Orientation is deliberately invalid (no magnetometer, no fusion here).
        msg.orientation.w = 1.0
        msg.orientation_covariance[0] = -1.0

        msg.angular_velocity.x = gx / GYRO_SCALE * deg_to_rad
        msg.angular_velocity.y = gy / GYRO_SCALE * deg_to_rad
        msg.angular_velocity.z = (
            gz / GYRO_SCALE * deg_to_rad - self._bias_z
        ) * self.gyro_scale_z
        msg.angular_velocity_covariance[0] = self.gyro_var
        msg.angular_velocity_covariance[4] = self.gyro_var
        msg.angular_velocity_covariance[8] = self.gyro_var

        msg.linear_acceleration.x = ax / ACCEL_SCALE * GRAVITY
        msg.linear_acceleration.y = ay / ACCEL_SCALE * GRAVITY
        msg.linear_acceleration.z = az / ACCEL_SCALE * GRAVITY
        msg.linear_acceleration_covariance[0] = self.accel_var
        msg.linear_acceleration_covariance[4] = self.accel_var
        msg.linear_acceleration_covariance[8] = self.accel_var

        self._pub.publish(msg)

    def close(self) -> None:
        try:
            self._bus.close()
        except Exception:
            pass


def main(args=None) -> None:
    rclpy.init(args=args)
    node: ImuNode | None = None
    try:
        node = ImuNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.close()
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
