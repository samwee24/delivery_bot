"""Pure helpers for goals.yaml: no rclpy, so they can be unit-tested anywhere."""

from __future__ import annotations

import math

import yaml


def yaw_from_quaternion(x: float, y: float, z: float, w: float) -> float:
    """Yaw (rad, -pi..pi) of a quaternion."""
    return math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))


def quaternion_from_yaw(yaw: float) -> tuple[float, float, float, float]:
    """(x, y, z, w) for a rotation of ``yaw`` about z."""
    return 0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0)


def load_goals(path: str) -> dict:
    """Read goals.yaml; every goal needs x and y, and ``home`` must exist."""
    with open(path) as f:
        goals = yaml.safe_load(f) or {}
    if 'home' not in goals:
        raise ValueError(f'{path} has no "home" goal')
    for name, goal in goals.items():
        if not isinstance(goal, dict) or 'x' not in goal or 'y' not in goal:
            raise ValueError(f'goal "{name}" in {path} needs x and y')
    return goals


def pick_goals(goals: dict, names: list[str]) -> list[str]:
    """Check every requested name exists; return them in order."""
    missing = [n for n in names if n not in goals]
    if missing:
        raise ValueError(f'unknown goal(s) {missing}; known: {sorted(goals)}')
    return names


def pose_fields(goal: dict) -> tuple[float, float, float, float, float, float]:
    """goals.yaml entry to (x, y, qx, qy, qz, qw); yaw defaults to 0."""
    qx, qy, qz, qw = quaternion_from_yaw(float(goal.get('yaw', 0.0)))
    return float(goal['x']), float(goal['y']), qx, qy, qz, qw


def save_goal(path: str, name: str, x: float, y: float, yaw: float,
              overwrite: bool = False) -> None:
    """Add one goal to goals.yaml, keeping every other entry.

    A new name is appended as text so the file's comments survive. Replacing an
    existing name (only with ``overwrite``) rewrites the file and loses comments.
    """
    goals = load_goals(path)
    entry = {'x': round(x, 3), 'y': round(y, 3), 'yaw': round(yaw, 3)}
    if name in goals and not overwrite:
        raise ValueError(f'goal "{name}" already exists; pass overwrite:=true to replace')
    if name in goals:
        goals[name] = entry
        with open(path, 'w') as f:
            yaml.safe_dump(goals, f, sort_keys=False)
        return
    with open(path) as f:
        text = f.read()
    sep = '' if text.endswith('\n') else '\n'
    with open(path, 'a') as f:
        f.write(sep + yaml.safe_dump({name: entry}, sort_keys=False))
