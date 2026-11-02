"""
One-button run save: /run/save (std_srvs/Trigger).

Calls slam_toolbox's save_map (PGM + YAML) and serialize_map (.posegraph + .data, the
file navigation.launch.py localises on) under one dated name, then copies the live
config YAMLs next to them, so the numbers travel with the map (AGENTS.md rules 3, 6).

Output, in `maps_dir`:  <date>_<HHMM>.{pgm,yaml,posegraph,data} and <date>_<HHMM>_config/
Needs mapping.launch.py running; the Foxglove Call Service panel makes it a button.
"""

from datetime import datetime
import glob
import os
import shutil

from ament_index_python.packages import get_package_share_directory
import rclpy
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from slam_toolbox.srv import SaveMap, SerializePoseGraph
from std_msgs.msg import String
from std_srvs.srv import Trigger

# (package, subdir) whose *.yaml are copied beside each saved run
CALL_TIMEOUT_S = 60.0
CONFIG_SOURCES = (('delivery_bot_bringup', 'config'), ('delivery_bot_drivers', 'config'))


def copy_configs(dirs: list[str], dest: str) -> list[str]:
    """Copy every *.yaml from `dirs` into `dest`; return the file names copied."""
    os.makedirs(dest, exist_ok=True)
    names = []
    for d in dirs:
        for f in sorted(glob.glob(os.path.join(d, '*.yaml'))):
            shutil.copy(f, dest)
            names.append(os.path.basename(f))
    return names


class RunSave(Node):
    """Saves map, pose graph and configs under one dated name."""

    def __init__(self) -> None:
        super().__init__('run_save')
        self.declare_parameter('maps_dir', os.path.expanduser('~/maps'))
        cb = ReentrantCallbackGroup()   # the service callback blocks on the two clients
        self._save = self.create_client(SaveMap, '/slam_toolbox/save_map', callback_group=cb)
        self._serialize = self.create_client(
            SerializePoseGraph, '/slam_toolbox/serialize_map', callback_group=cb)
        self.create_service(Trigger, '/run/save', self._on_save, callback_group=cb)

    def _on_save(self, _req, res):
        if not (self._save.service_is_ready() and self._serialize.service_is_ready()):
            res.success, res.message = False, 'slam_toolbox services not up: is mapping running?'
            return res
        maps_dir = self.get_parameter('maps_dir').value
        base = os.path.join(maps_dir, datetime.now().strftime('%Y-%m-%d_%H%M'))
        os.makedirs(maps_dir, exist_ok=True)
        grid = self._save.call(SaveMap.Request(name=String(data=base)), timeout_sec=CALL_TIMEOUT_S)
        graph = self._serialize.call(
            SerializePoseGraph.Request(filename=base), timeout_sec=CALL_TIMEOUT_S)
        if grid is None or graph is None:
            res.success, res.message = False, f'slam_toolbox did not answer in {CALL_TIMEOUT_S} s'
            return res
        if grid.result != 0 or graph.result != 0:
            res.success = False
            res.message = (f'save_map result {grid.result} (1 = no map yet), '
                           f'serialize_map result {graph.result}; nothing copied')
            return res
        dirs = [os.path.join(get_package_share_directory(p), s) for p, s in CONFIG_SOURCES]
        names = copy_configs(dirs, base + '_config')
        res.success = True
        res.message = f'{base}.* and {len(names)} config files in {base}_config/'
        return res


def main(args=None) -> None:
    rclpy.init(args=args)
    node = RunSave()
    try:
        ex = MultiThreadedExecutor(num_threads=2)
        ex.add_node(node)
        ex.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
