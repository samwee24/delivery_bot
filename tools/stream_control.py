"""ROS services to start and stop the camera+mic stream from Foxglove (Call Service panel).

    /stream/start   Trigger   stops the ROS camera and any audio-only stream, starts audio_stream.py --video
    /stream/stop    Trigger   stops the stream (however it was started)

Run on the Pi (start_streams.sh does it):  python3 tools/stream_control.py
Stopping does not bring the ROS camera back: run `bash tools/start_streams.sh` for that.
Not part of the SLAM stack: a utility for watching the robot.
"""
import os
import subprocess
import sys
import time

import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audio_stream.py')


class StreamControl(Node):
    def __init__(self) -> None:
        super().__init__('stream_control')
        self.proc = None
        self.create_service(Trigger, '/stream/start', self.start)
        self.create_service(Trigger, '/stream/stop', self.stop)

    def running(self) -> bool:
        return subprocess.run(['pgrep', '-f', '[a]udio_stream.py --video'],
                              capture_output=True).returncode == 0

    def start(self, _, res):
        if self.running():
            res.success, res.message = True, 'already running'
            return res
        subprocess.run(['pkill', '-f', '[u]sb_cam_node_exe'])  # the ROS camera holds /dev/video0
        subprocess.run(['pkill', '-f', '[a]udio_stream.py'])    # an audio-only stream holds the mic
        time.sleep(2)
        self.proc = subprocess.Popen([sys.executable, SCRIPT, '--video'],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(4)
        res.success = self.running()
        res.message = 'streaming at http://<pi>:8090/stream.mkv' if res.success else 'failed to start'
        return res

    def stop(self, _, res):
        subprocess.run(['pkill', '-f', '[a]udio_stream.py'])
        if self.proc is not None:
            self.proc.wait(timeout=5)
            self.proc = None
        res.success, res.message = True, 'stopped'
        return res


def main() -> None:
    rclpy.init()
    rclpy.spin(StreamControl())


if __name__ == '__main__':
    main()
