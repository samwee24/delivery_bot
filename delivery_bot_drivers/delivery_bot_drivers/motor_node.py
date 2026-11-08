"""
L298N motor driver for the delivery robot.

What it does:
  * Subscribes to /cmd_vel (geometry_msgs/TwistStamped) and stores the latest
    linear.x (v, m/s), angular.z (w, rad/s) and the time it arrived.
  * A 20 Hz timer (_control_step) splits v and w into wheel speeds,
    v_left/right = v -/+ w * wheel_base / 2, and turns each one into a PWM duty
    and a direction: duty = min_duty + gain * |speed|, clamped to max_duty.
    A wheel slower than min_wheel_speed gets duty 0. Direction is +1 (forward)
    or -1 (backward), never 0; direction pins are set before the duty.

Safety contract (do not weaken):
  * A command older than ``watchdog_s`` means stop (duty0, direction pins low).
  * Shutdown, Ctrl+C (KeyboardInterrupt), a launch shutdown
    (ExternalShutdownException) or an exception in spin all reach
    ``stop_all()`` in main's ``finally``: PWM zeroed, pins low, devices closed.
  * There is no dry run in this node: it always opens the GPIO pins and drives
    the motors. A ``dry_run`` parameter passed by a launch file is ignored.

Raspberry Pi 4B / Ubuntu 24.04: gpiozero's lgpio pin factory is used because
RPi.GPIO has no wheels for aarch64. /dev/gpiochip0 is root:dialout on this
image, so membership of ``dialout`` is enough (see docs/pi_setup.md).
gpiozero is imported inside ``__init__``, so the module imports without it.

Parameters read (see config/drivers.yaml): ena_pin, in1_pin, in2_pin, enb_pin,
in3_pin, in4_pin, pwm_hz, wheel_base, max_duty, min_duty, gain_left,
gain_right, min_wheel_speed, watchdog_s. use_stamped, use_gyro_loop,
kp_omega, ki_omega and dry_run are in the YAML but not read (/cmd_vel is
always TwistStamped; the gyro loop in _on_imu is not implemented).
"""

from __future__ import annotations

import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException  # to shut node down


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

        # subscribe to /cmd_vel
        from geometry_msgs.msg import TwistStamped
        self.v = 0.0
        self.w = 0.0
        self.last_cmd_time = self.get_clock().now()
        self.create_subscription(TwistStamped, '/cmd_vel', self._on_cmd, 10)
        # _on_cmd listens to /cmd_vel, 10 is queue size to keep

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

        self.create_timer(0.05, self._control_step)
        # runs control_step at 20Hz

    def set_wheel(self, side: str, duty: float, direction: int) -> None:
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

    def _control_step(self) -> None:
        # runs at 20hz, called in __init__
        # converts v and w into v_left and v_right from _on_cmd
        age = (self.get_clock().now() - self.last_cmd_time).nanoseconds * 1e-9
        # compares current time to timestamp of last received message
        if age > self.watchdog_s:
            self.stop()  # if no commands for 0.5s, stops all motors
            return
        # differential drive
        self.v_left = self.v - self.w * self.wheel_base / 2
        self.v_right = self.v + self.w * self.wheel_base / 2
        # self._duty_for returns a tuple used directly by set_wheel
        self.set_wheel(*self._duty_for('l', self.v_left))
        self.set_wheel(*self._duty_for('r', self.v_right))

    def _duty_for(
            self, side: str, wheel_speed: float) -> tuple[str, float, int]:
        # turns v_left and v_right into pwm duty&direction, clamps to max_duty
        direction = 1 if wheel_speed > 0 else -1  # 1 forward, -1 backwards
        speed = abs(wheel_speed)
        if speed < self.min_wheel_speed:
            return side, 0.0, direction  # dont spin
        duty = self.min_duty + self.gain[side] * speed
        duty = max(0.0, min(duty, self.max_duty))  # clamping the duty
        return side, duty, direction

    def stop_all(self) -> None:
        self.stop()  # sets everything back to zero
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
