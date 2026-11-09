"""
L298N motor driver for the delivery robot.

What it does:
  * Subscribes to /cmd_vel (geometry_msgs/TwistStamped) and stores the latest
    linear.x (v, m/s), angular.z (w, rad/s) and the time it arrived.
  * A 20 Hz timer (_control_step) splits v and w into wheel speeds,
    v_left/right = v -/+ w * wheel_base / 2, and turns each one into a PWM duty
    and a direction: duty = min_duty + gain * |speed|, clamped to max_duty.
    A wheel slower than min_wheel_speed gets duty 0. A wheel starting from rest
    (or reversing) gets at least kick_duty for kick_s. Direction is +1 (forward)
    or -1 (backward), never 0; direction pins are set before the duty.

Safety contract (do not weaken):
  * Dry run is the default (``dry_run`` True): gpiozero is never imported, no
    pin is opened, set_wheel()/stop() only record the last duty and direction
    per wheel. Live needs the launch argument dry_run set to false.
  * A command older than ``watchdog_s`` means stop (duty 0, direction pins low).
  * Lidar stop: /scan is kept with its arrival time. If v > 0 and a finite
    range >= range_min lies under ``stop_dist_m`` within +-``stop_half_angle_deg``
    of the forward angle, linear speed is zeroed for that step (same behind
    for v < 0); w is kept so the robot can still turn away. No echo (inf)
    counts as free: a known limit of this lidar (a residual hazard).
  * Stale scan: no /scan for ``scan_timeout_s`` (or none yet) means stop.
  * Shutdown, Ctrl+C (KeyboardInterrupt), a launch shutdown
    (ExternalShutdownException) or an exception in spin all reach
    ``stop_all()`` in main's ``finally``: PWM zeroed, pins low, devices closed.

Raspberry Pi 4B / Ubuntu 24.04: gpiozero's lgpio pin factory is used because
RPi.GPIO has no wheels for aarch64. /dev/gpiochip0 is root:dialout on this
image, so membership of ``dialout`` is enough (see docs/pi_setup.md).
gpiozero is imported inside ``__init__``, so the module imports without it.

Parameters read (see config/drivers.yaml): dry_run, ena_pin, in1_pin, in2_pin,
enb_pin, in3_pin, in4_pin, pwm_hz, wheel_base, max_duty, min_duty, gain_left,
gain_right, min_wheel_speed, kick_duty, kick_s, watchdog_s, stop_dist_m, stop_half_angle_deg,
scan_timeout_s, laser_forward_rad. use_gyro_loop, kp_omega and ki_omega are in
the YAML but not read (the gyro loop in _on_imu is not implemented).
"""

from __future__ import annotations

import math

import rclpy
from rclpy.executors import ExternalShutdownException  # to shut node down
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data


def wheel_speeds(v: float, w: float, wheel_base: float) -> tuple[float, float]:
    """Differential drive: (v_left, v_right) in m/s from v (m/s), w (rad/s)."""
    return v - w * wheel_base / 2, v + w * wheel_base / 2


def duty_for(speed: float, gain: float, min_duty: float, max_duty: float,
             min_wheel_speed: float) -> tuple[float, int]:
    """Signed wheel speed (m/s) to (PWM duty, direction +1/-1)."""
    direction = 1 if speed > 0 else -1  # 1 forward, -1 backwards
    speed = abs(speed)
    if speed < min_wheel_speed:
        return 0.0, direction  # dont spin
    duty = min_duty + gain * speed
    return max(0.0, min(duty, max_duty)), direction  # clamp to max_duty


def kick(duty: float, direction: int, prev: tuple[float, int],
         started: float, now: float, kick_duty: float,
         kick_s: float) -> tuple[float, float]:
    """
    Kick-start a wheel from rest: (duty to write, start time).

    A wheel that was at duty 0 (or turned round) starts now; for kick_s
    seconds it gets at least kick_duty, then the fitted duty. Static friction
    needs about 0.20 duty, a rolling wheel much less (test_log 2026-11-09).
    """
    if duty <= 0:
        return duty, started
    if prev[0] <= 0 or prev[1] != direction:
        started = now
    if now - started < kick_s:
        duty = max(duty, kick_duty)
    return duty, started


def blocked(ranges, angle_min: float, angle_increment: float,
            range_min: float, v: float, stop_dist: float, half_angle: float,
            forward_angle: float) -> bool:
    """
    Return True if v pushes toward a finite range in [range_min, stop_dist).

    Looks within +-half_angle (rad) of forward_angle (v > 0) or of the rear
    (v < 0), angles in the scan frame. inf/NaN (no echo) counts as free.
    """
    if v == 0:
        return False
    centre = forward_angle if v > 0 else forward_angle + math.pi
    for i, r in enumerate(ranges):
        if not math.isfinite(r) or r < range_min or r >= stop_dist:
            continue
        a = angle_min + i * angle_increment - centre
        a = math.atan2(math.sin(a), math.cos(a))  # wrap to [-pi, pi]
        if abs(a) <= half_angle:
            return True
    return False


class MotorNode(Node):
    """Subscribes /cmd_vel, writes the L298N, stops when commands go stale."""

    def __init__(self) -> None:
        super().__init__('motor_node')  # called from rclpy.node parent class
        self.pwm_hz = self.declare_parameter('pwm_hz', 1000).value
        self.wheel_base = self.declare_parameter('wheel_base', 0.156).value
        self.max_duty = self.declare_parameter('max_duty', 0.85).value
        self.min_duty = self.declare_parameter('min_duty', 0.15).value
        self.watchdog_s = self.declare_parameter('watchdog_s', 0.5).value
        self.ena_pin = self.declare_parameter('ena_pin', 12).value
        self.in1_pin = self.declare_parameter('in1_pin', 5).value
        self.in2_pin = self.declare_parameter('in2_pin', 6).value
        self.enb_pin = self.declare_parameter('enb_pin', 13).value
        self.in3_pin = self.declare_parameter('in3_pin', 26).value
        self.in4_pin = self.declare_parameter('in4_pin', 16).value
        self.gain = {'l': self.declare_parameter('gain_left', 2.0).value,
                     'r': self.declare_parameter('gain_right', 2.0).value}
        self.min_wheel_speed = self.declare_parameter('min_wheel_speed',
                                                      0.01).value
        self.dry_run = self.declare_parameter('dry_run', True).value
        self.stop_dist = self.declare_parameter('stop_dist_m', 0.20).value
        self.half_angle = math.radians(
            self.declare_parameter('stop_half_angle_deg', 35.0).value)
        self.scan_timeout_s = self.declare_parameter('scan_timeout_s',
                                                     0.5).value
        self.forward_angle = self.declare_parameter('laser_forward_rad',
                                                    0.0).value
        # kick-start from rest, clamped to max_duty
        self.kick_duty = min(
            self.declare_parameter('kick_duty', 0.30).value, self.max_duty)
        self.kick_s = self.declare_parameter('kick_s', 0.15).value
        self.kick_start = {'l': -math.inf, 'r': -math.inf}
        # last duty and direction per wheel, what dry run "drives"
        self.last = {'l': (0.0, 1), 'r': (0.0, 1)}
        self._driving = False  # edge-triggers the watchdog log line

        # subscribe to /cmd_vel
        from geometry_msgs.msg import TwistStamped
        self.v = 0.0
        self.w = 0.0
        self.last_cmd_time = self.get_clock().now()
        self.create_subscription(TwistStamped, '/cmd_vel', self._on_cmd, 10)
        # _on_cmd listens to /cmd_vel, 10 is queue size to keep

        from sensor_msgs.msg import LaserScan
        self.scan = None
        self.scan_time = None
        self.create_subscription(LaserScan, '/scan', self._on_scan,
                                 qos_profile_sensor_data)

        self.create_timer(0.05, self._control_step)
        # runs control_step at 20Hz
        if self.dry_run:
            self.get_logger().info('dry run: no GPIO, duties only logged')
            return

        from gpiozero import PWMOutputDevice, DigitalOutputDevice
        from gpiozero.pins.lgpio import LGPIOFactory
        # setting devices for wheel motion
        f = LGPIOFactory()
        self.ena = PWMOutputDevice(pin=self.ena_pin,
                                   frequency=self.pwm_hz, pin_factory=f)
        self.in1 = DigitalOutputDevice(pin=self.in1_pin, pin_factory=f)
        self.in2 = DigitalOutputDevice(pin=self.in2_pin, pin_factory=f)
        self.enb = PWMOutputDevice(pin=self.enb_pin,
                                   frequency=self.pwm_hz, pin_factory=f)
        self.in3 = DigitalOutputDevice(pin=self.in3_pin, pin_factory=f)
        self.in4 = DigitalOutputDevice(pin=self.in4_pin, pin_factory=f)

    def set_wheel(self, side: str, duty: float, direction: int) -> None:
        self.last[side] = (duty, direction)
        if self.dry_run:
            return
        if (side == 'l'):
            if (direction > 0):  # forward
                self.in1.on()
                self.in2.off()
            elif (direction < 0):  # backward
                self.in1.off()
                self.in2.on()
            self.ena.value = duty
        elif (side == 'r'):
            if (direction > 0):  # forward
                self.in3.on()
                self.in4.off()
            elif (direction < 0):  # backward
                self.in3.off()
                self.in4.on()
            self.enb.value = duty

    def stop(self) -> None:
        self.last = {'l': (0.0, 0), 'r': (0.0, 0)}
        if self.dry_run:
            return
        self.ena.value = 0
        self.enb.value = 0
        self.in1.off()
        self.in2.off()
        self.in3.off()
        self.in4.off()

    def _on_cmd(self, msg) -> None:
        # stores latest linear vel&turn rate (w)+timestamp frm /cmd_vel
        self.v = msg.twist.linear.x  # forward speed
        self.w = msg.twist.angular.z  # turn rate
        self.last_cmd_time = self.get_clock().now()
        # time message arrived for watchdog

    def _on_imu(self, msg) -> None:
        # for gyro correction if needed
        raise NotImplementedError

    def _on_scan(self, msg) -> None:
        self.scan = msg
        self.scan_time = self.get_clock().now()

    def _control_step(self) -> None:
        # runs at 20hz, called in __init__
        # converts v and w into v_left and v_right from _on_cmd
        now = self.get_clock().now()
        age = (now - self.last_cmd_time).nanoseconds * 1e-9
        # compares current time to timestamp of last received message
        if age > self.watchdog_s:
            self.stop()  # if no commands for 0.5s, stops all motors
            if self._driving:
                self.get_logger().info(
                    f'watchdog: no /cmd_vel for {age:.2f} s, stop')
                self._driving = False
            return
        self._driving = True
        scan_age = (math.inf if self.scan_time is None
                    else (now - self.scan_time).nanoseconds * 1e-9)
        if scan_age > self.scan_timeout_s:
            self.stop()  # fail safe: blind means stop
            self.get_logger().warn(
                f'stale scan ({scan_age:.2f} s old), stop',
                throttle_duration_sec=1.0)
            return
        v = self.v
        s = self.scan
        if v != 0 and blocked(s.ranges, s.angle_min, s.angle_increment,
                              s.range_min, v, self.stop_dist, self.half_angle,
                              self.forward_angle):
            v = 0.0  # keep w: the robot may still turn away
            self.get_logger().warn(
                f'lidar stop: obstacle within {self.stop_dist} m, '
                'linear zeroed', throttle_duration_sec=1.0)
        # differential drive
        self.v_left, self.v_right = wheel_speeds(v, self.w, self.wheel_base)
        t = now.nanoseconds * 1e-9
        for side, speed in (('l', self.v_left), ('r', self.v_right)):
            _, duty, direction = self._duty_for(side, speed)
            duty, self.kick_start[side] = kick(
                duty, direction, self.last[side], self.kick_start[side], t,
                self.kick_duty, self.kick_s)
            self.set_wheel(side, duty, direction)
        if self.dry_run:
            self.get_logger().info(
                f'dry run duty/dir: l={self.last["l"]} r={self.last["r"]}',
                throttle_duration_sec=1.0)

    def _duty_for(
            self, side: str, wheel_speed: float) -> tuple[str, float, int]:
        # turns v_left and v_right into pwm duty&direction, clamps to max_duty
        duty, direction = duty_for(wheel_speed, self.gain[side],
                                   self.min_duty, self.max_duty,
                                   self.min_wheel_speed)
        return side, duty, direction

    def stop_all(self) -> None:
        self.stop()  # sets everything back to zero
        if self.dry_run:
            return
        for dev in (self.ena, self.enb, self.in1,
                    self.in2, self.in3, self.in4):
            dev.close()  # off any current, from gpiozero library


def main(args=None) -> None:
    rclpy.init()
    node = MotorNode()
    try:
        rclpy.spin(node)  # inifite loop to run node
    except (KeyboardInterrupt, ExternalShutdownException):
        pass  # passes to finally node
    finally:  # catchall to make sure it shuts down eventually
        node.stop_all()
        node.destroy_node()
        if rclpy.ok():  # check if ros is still up before shutdown
            rclpy.shutdown()
