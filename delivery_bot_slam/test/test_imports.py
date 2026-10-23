"""Import checks: catch syntax errors without starting anything.

colcon test runs this on Jazzy, where rclpy and the message packages exist, so
the modules are imported normally. Nothing is constructed and no node is spun:
importing a module only runs its docstring, imports and def statements, which
is enough for CI to fail on a typo before the Pi ever sees it.
"""

from delivery_bot_slam import odom_covariance_relay, trajectory_recorder


def test_odom_covariance_relay_imports() -> None:
    assert callable(odom_covariance_relay.main)


def test_trajectory_recorder_imports() -> None:
    assert callable(trajectory_recorder.main)
