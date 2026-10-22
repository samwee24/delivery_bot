"""L298N motor driver for the delivery robot.

Safety contract (do not weaken):
  * /cmd_vel drives the wheels; a command older than ``watchdog_s`` means stop.
  * Shutdown, Ctrl+C, an exception or rclpy context shutdown all zero PWM and
    drive the direction pins low.
  * ``dry_run`` (default True in the bringup launch file) never touches GPIO.

Raspberry Pi 4B / Ubuntu 24.04: gpiozero's lgpio pin factory is used because
RPi.GPIO has no wheels for aarch64. /dev/gpiochip0 is root:dialout on this
image, so membership of ``dialout`` is enough (see docs/pi_setup.md).
"""

from __future__ import annotations

import math
import time

import rclpy
from geometry_msgs.msg import Twist, TwistStamped
from rclpy.node import Node
from sensor_msgs.msg import Imu
from std_msgs.msg import Float32MultiArray


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


class _GpioWheels:
    """All GPIO writes live here so there is one place to make them safe."""

    def __init__(self, pins: dict[str, int], pwm_hz: float) -> None:
        # Imported lazily so dry-run works on a machine without gpiozero.
        from gpiozero import Device, DigitalOutputDevice, PWMOutputDevice
        from gpiozero.pins.lgpio import LGPIOFactory

        Device.pin_factory = LGPIOFactory()

        self._pwm = {
            "left": PWMOutputDevice(pins["ena"], frequency=pwm_hz, initial_value=0.0),
            "right": PWMOutputDevice(pins["enb"], frequency=pwm_hz, initial_value=0.0),
        }
        # (side, 1) = "forward" pin, (side, 2) = "reverse" pin.
        self._dir = {
            ("left", 1): DigitalOutputDevice(pins["in1"]),
            ("left", 2): DigitalOutputDevice(pins["in2"]),
            ("right", 1): DigitalOutputDevice(pins["in3"]),
            ("right", 2): DigitalOutputDevice(pins["in4"]),
        }

    def set_wheel(self, side: str, duty: float, direction: int) -> None:
        if duty <= 0.0 or direction == 0:
            self._pwm[side].value = 0.0
            self._dir[(side, 1)].off()
            self._dir[(side, 2)].off()
            return
        self._dir[(side, 1)].value = direction > 0
        self._dir[(side, 2)].value = direction < 0
        self._pwm[side].value = float(duty)

    def stop(self) -> None:
        for side in ("left", "right"):
            self._pwm[side].value = 0.0
        for device in self._dir.values():
            device.off()


class MotorNode(Node):
    def __init__(self) -> None:
        super().__init__("motor_node")

        # --- parameters -------------------------------------------------
        self.wheel_base = self.declare_parameter("wheel_base", 0.13).value
        self.max_duty = float(self.declare_parameter("max_duty", 0.85).value)
        self.dead_zone = {
            "left": float(self.declare_parameter("dead_zone_left", 0.35).value),
            "right": float(self.declare_parameter("dead_zone_right", 0.35).value),
        }
        self.gain = {
            "left": float(self.declare_parameter("gain_left", 2.0).value),
            "right": float(self.declare_parameter("gain_right", 2.0).value),
        }
        self.min_wheel_speed = float(
            self.declare_parameter("min_wheel_speed", 0.01).value
        )
        self.watchdog_s = float(self.declare_parameter("watchdog_s", 0.5).value)
        # Nav2 Jazzy's controller/server publishes geometry_msgs/TwistStamped by
        # default (no enable_stamped_cmd_vel parameter any more), so the default
        # here is True to match. teleop_twist_keyboard can publish stamped
        # messages with: --ros-args -p stamped:=true
        self.use_stamped = bool(self.declare_parameter("use_stamped", True).value)
        self.use_gyro_loop = bool(
            self.declare_parameter("use_gyro_loop", False).value
        )
        self.kp_omega = float(self.declare_parameter("kp_omega", 0.5).value)
        self.ki_omega = float(self.declare_parameter("ki_omega", 1.0).value)
        self.dry_run = bool(self.declare_parameter("dry_run", False).value)
        self.pwm_hz = float(self.declare_parameter("pwm_hz", 1000.0).value)
        self.control_dt = 0.02  # 50 Hz control loop

        pins = {
            "ena": int(self.declare_parameter("ena_pin", 12).value),
            "in1": int(self.declare_parameter("in1_pin", 5).value),
            "in2": int(self.declare_parameter("in2_pin", 6).value),
            "enb": int(self.declare_parameter("enb_pin", 13).value),
            "in3": int(self.declare_parameter("in3_pin", 20).value),
            "in4": int(self.declare_parameter("in4_pin", 21).value),
        }

        # --- state ------------------------------------------------------
        self._cmd: tuple[float, float] | None = None
        self._cmd_time: float | None = None
        self._gyro_z: float | None = None
        self._integral = 0.0
        self._last_status_log = 0.0
        self._gpio: _GpioWheels | None = None

        if not self.dry_run:
            self._gpio = _GpioWheels(pins, self.pwm_hz)
            self.get_logger().info(
                "Motor node live: L298N on GPIO %s, %.0f Hz PWM" % (pins, self.pwm_hz)
            )
        else:
            self.get_logger().warn(
                "dry_run=True: duties are computed and published, GPIO is untouched"
            )

        # --- interfaces -------------------------------------------------
        msg_type = TwistStamped if self.use_stamped else Twist
        self.create_subscription(msg_type, "cmd_vel", self._on_cmd, 10)
        if self.use_gyro_loop:
            self.create_subscription(Imu, "imu/data", self._on_imu, 10)
        self._duty_pub = self.create_publisher(Float32MultiArray, "motor/duty", 10)
        self.create_timer(self.control_dt, self._control_step)
        self.context.on_shutdown(self.stop_all)
        self.get_logger().info(
            "cmd_vel type: %s, watchdog %.2f s, gyro loop: %s"
            % ("TwistStamped" if self.use_stamped else "Twist",
               self.watchdog_s, self.use_gyro_loop)
        )

    # --- input ----------------------------------------------------------
    def _on_cmd(self, msg) -> None:
        twist = msg.twist if isinstance(msg, TwistStamped) else msg
        self._cmd = (float(twist.linear.x), float(twist.angular.z))
        self._cmd_time = time.monotonic()

    def _on_imu(self, msg: Imu) -> None:
        self._gyro_z = float(msg.angular_velocity.z)

    # --- control --------------------------------------------------------
    def _duty_for(self, side: str, wheel_speed: float) -> tuple[float, int]:
        """Map one wheel's speed (m/s) to (duty, direction)."""
        if abs(wheel_speed) <= self.min_wheel_speed:
            return 0.0, 0
        duty = self.dead_zone[side] + self.gain[side] * abs(wheel_speed)
        return _clamp(duty, 0.0, self.max_duty), (1 if wheel_speed > 0.0 else -1)

    def _control_step(self) -> None:
        now = time.monotonic()
        timed_out = (
            self._cmd_time is None or (now - self._cmd_time) > self.watchdog_s
        )
        if timed_out or self._cmd is None:
            left, right = (0.0, 0), (0.0, 0)
            omega_out = 0.0
            v_cmd = 0.0
            if self._cmd is not None:
                # Only log the transition, not every loop tick.
                if self._cmd != (0.0, 0.0):
                    self.get_logger().warn("cmd_vel timeout -> motors stopped")
                self._cmd = (0.0, 0.0)
        else:
            v_cmd, omega_out = self._cmd
            if self.use_gyro_loop and abs(v_cmd) + abs(omega_out) > 1e-3:
                if self._gyro_z is None:
                    self.get_logger().warn(
                        "use_gyro_loop is on but no /imu/data has arrived",
                        once=True,
                    )
                else:
                    error = omega_out - self._gyro_z
                    self._integral = _clamp(
                        self._integral + self.ki_omega * error * self.control_dt,
                        -0.5,
                        0.5,
                    )
                    omega_out = omega_out + self.kp_omega * error + self._integral
            elif abs(omega_out) < 1e-3:
                self._integral = 0.0  # no creep when not turning

            half = self.wheel_base / 2.0
            left = self._duty_for("left", v_cmd - omega_out * half)
            right = self._duty_for("right", v_cmd + omega_out * half)

        self._apply("left", left)
        self._apply("right", right)

        msg = Float32MultiArray()
        msg.data = [left[0] * left[1], right[0] * right[1]]
        self._duty_pub.publish(msg)

        if self.dry_run and now - self._last_status_log > 0.5:
            self._last_status_log = now
            self.get_logger().info(
                "dry_run L=%+.2f R=%+.2f (v=%.3f m/s, w=%+.3f rad/s, gyro=%s)"
                % (
                    left[0] * left[1],
                    right[0] * right[1],
                    v_cmd,
                    omega_out,
                    "n/a" if self._gyro_z is None else "%.3f" % self._gyro_z,
                )
            )

    def _apply(self, side: str, command: tuple[float, int]) -> None:
        if self._gpio is not None:
            self._gpio.set_wheel(side, command[0], command[1])

    def stop_all(self) -> None:
        """Idempotent all-stop; safe to call from any shutdown path."""
        if self._gpio is not None:
            self._gpio.stop()
        if rclpy.ok():
            try:
                msg = Float32MultiArray()
                msg.data = [0.0, 0.0]
                self._duty_pub.publish(msg)
            except Exception:  # publisher may already be gone
                pass


def main(args=None) -> None:
    rclpy.init(args=args)
    node: MotorNode | None = None
    try:
        node = MotorNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as exc:  # keep the motors off on any failure
        if node is not None:
            node.get_logger().fatal("motor_node crashed: %s" % exc)
        raise
    finally:
        if node is not None:
            node.stop_all()
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
