"""Pure-logic checks for the recorder's append rule and quaternion handling."""

import math

from delivery_bot_slam.trajectory_recorder import accept, normalise


def pose(x=0.0, y=0.0, yaw=0.0):
    return (0.0, x, y, 0.0, 0.0, 0.0, math.sin(yaw / 2), math.cos(yaw / 2))


def test_append_rule() -> None:
    assert accept(pose(), None, 0.02, 2.0)           # first pose always kept
    assert not accept(pose(0.019), pose(), 0.02, 2.0)
    assert accept(pose(0.021), pose(), 0.02, 2.0)
    assert not accept(pose(yaw=math.radians(1.9)), pose(), 0.02, 2.0)
    assert accept(pose(yaw=math.radians(2.1)), pose(), 0.02, 2.0)
    # yaw wraps across +-pi: 179 -> -179 is 2 degrees, not 358
    assert accept(pose(yaw=math.radians(-179)), pose(yaw=math.radians(177)), 0.02, 2.0)


def test_normalise() -> None:
    assert normalise((0, 0, 0, 0)) is None
    assert abs(sum(c * c for c in normalise((0, 0, 3, 4))) - 1.0) < 1e-12
