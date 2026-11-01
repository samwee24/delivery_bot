"""Live stream from the camera: microphone (ALSA card U2K) over HTTP, optionally with video.

Audio only:  python3 tools/audio_stream.py              (port 8090)
Listen anywhere: vlc http://100.83.14.99:8090/audio.mp3
                 ffplay -nodisp http://100.83.14.99:8090/audio.mp3
                 or open the URL in a browser (expect 2-5 s of buffering)

Picture and sound in one stream:  python3 tools/audio_stream.py --video
    vlc http://100.83.14.99:8090/stream.mkv    (VLC or ffplay; browsers do not play MJPEG in Matroska)
    The camera's MJPEG frames are copied, not re-encoded, so it costs little CPU (about 17 Mbit/s
    at 1280x720, 15 fps: fine on the LAN, heavy over Tailscale from far away). It opens
    /dev/video0, so the ROS camera node (camera.launch.py) must not be running, and it needs
    the microphone, so the audio-only mode must not be running either.

Any number of clients can connect and leave at any time; ffmpeg runs once. To tap it
from code later, read the same URL (a recorder: `ffmpeg -i <url> -c copy out.mkv`).
Not ROS on purpose: the stack stays thin and this needs no apt install.
"""
import os
import queue
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DEVICE = 'plughw:U2K'  # by card id, so a reordered card number does not break it
VIDEO = '--video' in sys.argv
PORT = int(next((a for a in sys.argv[1:] if a.isdigit()), 8090))
HEAD = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-fflags', 'nobuffer']
if VIDEO:
    PATH, TYPE = '/stream.mkv', 'video/x-matroska'
    FFMPEG = HEAD + ['-use_wallclock_as_timestamps', '1', '-f', 'v4l2', '-input_format', 'mjpeg',
                     '-video_size', '1280x720', '-framerate', '15', '-i', '/dev/video0',
                     '-f', 'alsa', '-i', DEVICE, '-ac', '1', '-c:v', 'copy', '-c:a', 'aac',
                     '-b:a', '64k', '-flush_packets', '1', '-f', 'matroska', '-live', '1',
                     '-cluster_time_limit', '500', 'pipe:1']
else:
    PATH, TYPE = '/audio.mp3', 'audio/mpeg'
    FFMPEG = HEAD + ['-f', 'alsa', '-i', DEVICE, '-ac', '1', '-ar', '44100',
                     '-c:a', 'libmp3lame', '-b:a', '64k', '-flush_packets', '1', '-f', 'mp3', 'pipe:1']

CLUSTER = b'\x1f\x43\xb6\x75'  # Matroska Cluster id: the safe place for a new client to start
clients = set()
lock = threading.Lock()
header = b''  # Matroska only: everything before the first cluster; each new client gets it first


class Client:
    def __init__(self) -> None:
        self.q = queue.Queue(maxsize=400)
        self.started = not VIDEO  # video clients wait for the next cluster boundary
        self.prev = b''


def pump() -> None:
    global header
    proc = subprocess.Popen(FFMPEG, stdout=subprocess.PIPE)
    seen = b''
    while True:
        chunk = proc.stdout.read(1024)
        if not chunk:
            print('ffmpeg ended (device busy or missing?)', file=sys.stderr)
            os._exit(1)  # sys.exit would only end this thread
        if VIDEO and not header:
            seen += chunk
            i = seen.find(CLUSTER)
            if i >= 0:
                header = seen[:i]
        with lock:
            for c in list(clients):
                out = chunk
                if not c.started:
                    data = c.prev + chunk  # the id may straddle two chunks
                    k = data.find(CLUSTER)
                    c.prev = chunk[-3:]
                    if k < 0:
                        continue
                    c.started, out = True, data[k:]
                try:
                    c.q.put_nowait(out)
                except queue.Full:  # slow client: drop data rather than stall the others
                    pass


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != PATH:
            self.send_error(404)
            return
        for _ in range(50):  # video: the header exists once the first cluster has been seen
            if header or not VIDEO:
                break
            time.sleep(0.1)
        self.send_response(200)
        self.send_header('Content-Type', TYPE)
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        c = Client()
        with lock:
            clients.add(c)
        try:
            if VIDEO:
                self.wfile.write(header)
            while True:
                self.wfile.write(c.q.get())
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            with lock:
                clients.discard(c)

    def log_message(self, *_) -> None:
        pass


if __name__ == '__main__':
    threading.Thread(target=pump, daemon=True).start()
    ThreadingHTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
