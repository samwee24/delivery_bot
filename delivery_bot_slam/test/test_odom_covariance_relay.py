"""Checks that the relay rewrites only twist.covariance, using the shipped config."""

from pathlib import Path

from delivery_bot_slam.odom_covariance_relay import OdomCovarianceRelay
from nav_msgs.msg import Odometry
import pytest
import rclpy
import yaml

CONFIG = Path(__file__).parents[1] / 'config' / 'odom_covariance.yaml'
# PyYAML reads '1.0e3' (no sign) as a string; rcl_yaml reads it as a float.
PARAMS = {k: float(v) for k, v in yaml.safe_load(CONFIG.read_text())[
    'odom_covariance_relay']['ros__parameters'].items() if k.endswith('variance')}


@pytest.fixture(scope='module', autouse=True)
def ros_context():
    # The node takes no parameter_overrides argument, so the YAML goes in the way
    # launch passes it: --params-file. The node's defaults differ from the YAML.
    rclpy.init(args=['--ros-args', '--params-file', str(CONFIG)])
    yield
    rclpy.shutdown()


@pytest.fixture
def relay():
    node = OdomCovarianceRelay()
    node.sent = []
    node._pub.publish = node.sent.append   # no spinning; capture instead
    yield node
    node.destroy_node()


def odom(twist_cov=None) -> Odometry:
    m = Odometry()
    m.header.stamp.sec = 1234
    m.header.stamp.nanosec = 567890123
    m.header.frame_id = 'odom'
    m.child_frame_id = 'base_footprint'
    m.pose.pose.position.x = 1.5
    m.pose.pose.position.y = -2.5
    m.pose.pose.orientation.z = 0.6
    m.pose.pose.orientation.w = 0.8
    m.pose.covariance = [0.001 * (i + 1) for i in range(36)]
    m.twist.twist.linear.x = 0.12
    m.twist.twist.angular.z = -0.34
    if twist_cov is not None:
        m.twist.covariance = twist_cov
    return m


def test_twist_covariance_layout(relay) -> None:
    relay._on_odom(odom())
    cov = relay.sent[0].twist.covariance
    assert len(cov) == 36
    assert cov[0] == PARAMS['vx_variance']
    assert cov[35] == PARAMS['vyaw_variance']
    for i in (7, 14, 21, 28):
        assert cov[i] == PARAMS['unused_variance']
    diagonal = {0, 7, 14, 21, 28, 35}
    assert all(cov[i] == 0.0 for i in range(36) if i not in diagonal)


def test_everything_else_is_carried_over(relay) -> None:
    msg = odom()
    relay._on_odom(msg)
    out = relay.sent[0]
    assert out.header.stamp.sec == 1234
    assert out.header.stamp.nanosec == 567890123
    assert out.header.frame_id == 'odom'
    assert out.child_frame_id == 'base_footprint'
    assert out.pose == msg.pose
    assert list(out.pose.covariance) == [0.001 * (i + 1) for i in range(36)]
    assert out.twist.twist == msg.twist.twist


def test_nonzero_input_covariance_is_overwritten(relay) -> None:
    relay._on_odom(odom(twist_cov=[7.0] * 36))
    cov = relay.sent[0].twist.covariance
    assert cov[0] == PARAMS['vx_variance']
    assert cov[1] == 0.0
    assert cov[35] == PARAMS['vyaw_variance']


def test_logs_once_and_keeps_publishing(relay) -> None:
    calls = []

    class Logger:

        def warn(self, text):
            calls.append(('warn', text))

        def info(self, text):
            calls.append(('info', text))

    relay.get_logger = Logger
    assert relay._warned is False
    relay._on_odom(odom())
    relay._on_odom(odom())
    assert relay._warned is True
    assert [kind for kind, _ in calls] == ['warn']
    assert len(relay.sent) == 2
    for out in relay.sent:
        assert out.twist.covariance[0] == PARAMS['vx_variance']
        assert out.twist.covariance[35] == PARAMS['vyaw_variance']


def test_nonzero_input_logs_info_not_warn(relay) -> None:
    kinds = []

    class Logger:

        def warn(self, text):
            kinds.append('warn')

        def info(self, text):
            kinds.append('info')

    relay.get_logger = Logger
    relay._on_odom(odom(twist_cov=[1.0] * 36))
    assert kinds == ['info']
