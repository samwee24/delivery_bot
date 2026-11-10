"""navigation.launch.py must forward dry_run to base.launch.py (read by ast, no ROS needed).

On 2026-11-10 a live navigation.launch.py (dry_run set false) left motor_node in dry run: the
argument was not passed to the base include, so base.launch.py used its default.
"""
import ast
import os

LAUNCH = os.path.join(os.path.dirname(__file__), '..', '..',
                      'delivery_bot_bringup', 'launch', 'navigation.launch.py')


def _tree():
    with open(LAUNCH) as f:
        return ast.parse(f.read())


def _calls(tree, name):
    return [n for n in ast.walk(tree) if isinstance(n, ast.Call)
            and getattr(n.func, 'id', getattr(n.func, 'attr', None)) == name]


def test_dry_run_declared_and_defaults_to_true():
    decl = [c for c in _calls(_tree(), 'DeclareLaunchArgument')
            if isinstance(c.args[0], ast.Constant) and c.args[0].value == 'dry_run']
    assert len(decl) == 1
    default = {k.arg: k.value.value for k in decl[0].keywords}['default_value']
    assert default == 'true'


def test_base_include_forwards_dry_run():
    base = [c for c in _calls(_tree(), 'IncludeLaunchDescription')
            if 'base.launch.py' in ast.unparse(c)]
    assert len(base) == 1
    args = next(k.value for k in base[0].keywords if k.arg == 'launch_arguments')
    keys = {k.value for k in args.func.value.keys}   # {...}.items()
    assert 'dry_run' in keys


def test_drivers_yaml_leaves_dry_run_to_the_launch():
    """A node-specific dry_run in drivers.yaml beats the launch's /** value under a global
    SetParameter (checked on the Pi with rclpy, 2026-11-10), so it must not be there."""
    import yaml
    path = os.path.join(os.path.dirname(__file__), '..', '..',
                        'delivery_bot_drivers', 'config', 'drivers.yaml')
    with open(path) as f:
        params = yaml.safe_load(f)['motor_node']['ros__parameters']
    assert 'dry_run' not in params
