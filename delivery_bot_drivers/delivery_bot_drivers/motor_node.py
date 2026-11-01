"""
L298N motor driver for the delivery robot.

Safety contract (do not weaken):
  * /cmd_vel drives the wheels; a command older than ``watchdog_s`` means stop.
  * Shutdown, Ctrl+C, an exception or rclpy context shutdown all zero PWM and
    drive the direction pins low.
  * ``dry_run`` (default True in the bringup launch file) never touches GPIO.

Raspberry Pi 4B / Ubuntu 24.04: gpiozero's lgpio pin factory is used because
RPi.GPIO has no wheels for aarch64. /dev/gpiochip0 is root:dialout on this
image, so membership of ``dialout`` is enough (see docs/pi_setup.md).

Parameters (see config/drivers.yaml): ena_pin, in1_pin, in2_pin, enb_pin,
in3_pin, in4_pin, pwm_hz, wheel_base, max_duty, dead_zone_left,
dead_zone_right, gain_left, gain_right, min_wheel_speed, watchdog_s,
use_stamped, use_gyro_loop, kp_omega, ki_omega, dry_run.
"""

from __future__ import annotations

from rclpy.node import Node


def _clamp(value: float, low: float, high: float) -> float:
    raise NotImplementedError


class _GpioWheels:
    """All GPIO writes live here so there is one place to make them safe."""

    def __init__(self, pins: dict[str, int], pwm_hz: float) -> None:
        raise NotImplementedError

    def set_wheel(self, side: str, duty: float, direction: int) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError


class MotorNode(Node):
    """Subscribes /cmd_vel, writes the L298N, stops when commands go stale."""

    def __init__(self) -> None:
        raise NotImplementedError

    def _on_cmd(self, msg) -> None:
        raise NotImplementedError

    def _on_imu(self, msg) -> None:
        raise NotImplementedError

    def _duty_for(self, side: str, wheel_speed: float) -> tuple[float, int]:
        raise NotImplementedError

    def _control_step(self) -> None:
        raise NotImplementedError

    def _apply(self, side: str, command: tuple[float, int]) -> None:
        raise NotImplementedError

    def stop_all(self) -> None:
        raise NotImplementedError


def main(args=None) -> None:
    raise NotImplementedError
