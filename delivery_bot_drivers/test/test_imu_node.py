"""Checks imu_node against a fake smbus2: calibration, unit conversion, covariances."""

from math import radians
from pathlib import Path
import struct
import sys
from types import ModuleType, SimpleNamespace

from delivery_bot_drivers.imu_node import ImuNode
import pytest
import rclpy
import yaml

CONFIG = Path(__file__).parents[1] / 'config' / 'drivers.yaml'
PARAMS = yaml.safe_load(CONFIG.read_text())['imu_node']['ros__parameters']
G = 9.80665


@pytest.fixture
def make_node(monkeypatch):
    """Build an ImuNode on a fake bus; extra -p overrides go after drivers.yaml."""
    made = []

    def build(who=0x68, gyro=lambda n: (0, 0, 0), accel=(0, 0, 0), **overrides):
        state = SimpleNamespace(who=who, gyro=gyro, accel=accel, reads=0, fail=False)

        class FakeBus:

            def __init__(self, bus):
                pass

            def read_byte_data(self, addr, reg):
                return state.who

            def write_byte_data(self, addr, reg, value):
                pass

            def read_i2c_block_data(self, addr, reg, length):
                if state.fail:
                    raise OSError('i2c gone')
                gx, gy, gz = state.gyro(state.reads)
                state.reads += 1
                return list(struct.pack('>hhhhhhh', *state.accel, 0, gx, gy, gz))

            def close(self):
                pass

        fake = ModuleType('smbus2')
        fake.SMBus = FakeBus
        monkeypatch.setitem(sys.modules, 'smbus2', fake)
        args = ['--ros-args', '--params-file', str(CONFIG), '-p', 'calib_seconds:=0.1']
        for name, value in overrides.items():
            args += ['-p', f'{name}:={value}']
        rclpy.init(args=args)
        node = ImuNode()
        node.state = state
        node.sent = []
        node._pub.publish = node.sent.append
        made.append(node)
        return node

    yield build
    for node in made:
        node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()


def publish_once(node):
    node._publish()
    return node.sent[-1]


def test_wrong_who_am_i_raises(make_node) -> None:
    with pytest.raises(RuntimeError, match='WHO_AM_I'):
        make_node(who=0x70)


def test_noisy_gyro_during_calibration_raises(make_node) -> None:
    # +-200 raw is +-0.027 rad/s, std well over calib_max_std (0.01 in drivers.yaml)
    with pytest.raises(RuntimeError, match='std'):
        make_node(gyro=lambda n: (0, 0, 200 if n % 2 else -200))


def test_unit_conversion(make_node) -> None:
    node = make_node(accel=(0, 0, 16384))
    node.state.gyro = lambda n: (131, 262, 393)
    msg = publish_once(node)
    assert msg.angular_velocity.x == pytest.approx(radians(1))
    assert msg.angular_velocity.y == pytest.approx(radians(2))
    assert msg.angular_velocity.z == pytest.approx(radians(3))
    assert msg.linear_acceleration.z == pytest.approx(G)
    assert msg.linear_acceleration.x == 0.0


def test_calibration_bias_is_removed(make_node) -> None:
    node = make_node(gyro=lambda n: (13, -7, 26))
    msg = publish_once(node)
    assert msg.angular_velocity.x == pytest.approx(0.0, abs=1e-12)
    assert msg.angular_velocity.y == pytest.approx(0.0, abs=1e-12)
    assert msg.angular_velocity.z == pytest.approx(0.0, abs=1e-12)


def test_gyro_scale_applies_to_z_after_bias(make_node) -> None:
    node = make_node(gyro=lambda n: (0, 0, 100), gyro_scale_z=2.5)
    node.state.gyro = lambda n: (131, 262, 231)   # z is 131 above the bias: 1 deg/s
    msg = publish_once(node)
    assert msg.angular_velocity.z == pytest.approx(2.5 * radians(1))
    assert msg.angular_velocity.x == pytest.approx(radians(1))
    assert msg.angular_velocity.y == pytest.approx(radians(2))


def test_covariances_and_frame(make_node) -> None:
    msg = publish_once(make_node())
    assert msg.header.frame_id == 'imu_link'
    assert msg.orientation_covariance[0] == -1.0
    for k in (0, 4, 8):
        assert msg.angular_velocity_covariance[k] == PARAMS['gyro_var']
        assert msg.linear_acceleration_covariance[k] == PARAMS['accel_var']


def test_i2c_error_publishes_nothing(make_node) -> None:
    node = make_node()
    node.state.fail = True
    node._publish()
    assert node.sent == []


def test_recalibrate_updates_bias_and_keeps_old_on_noise(make_node) -> None:
    node = make_node(gyro=lambda n: (0, 0, 0))
    node.state.gyro = lambda n: (0, 0, 131)
    res = node._recalibrate(None, SimpleNamespace(success=None, message=''))
    assert res.success and 'z=0.01745' in res.message
    assert publish_once(node).angular_velocity.z == pytest.approx(0.0, abs=1e-12)
    node.state.gyro = lambda n: (0, 0, 200 if n % 2 else -200)
    res = node._recalibrate(None, SimpleNamespace(success=None, message=''))
    assert not res.success and 'std' in res.message
    assert node._bias[2] == pytest.approx(radians(1))
