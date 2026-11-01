"""Live stream from the camera: microphone (ALSA card U2K) over HTTP, optionally with video.

Audio only:  python3 tools/streams/audio_stream.py              (port 8090)
Listen anywhere: vlc http://100.83.14.99:8090/audio.mp3
                 ffplay -nodisp http://100.83.14.99:8090/audio.mp3
                 or open the URL in a browser (expect 2-5 s of buffering)

Picture and sound in one stream:  python3 tools/streams/audio_stream.py --video [--size 1280x720] [--fps 30]
    vlc http://100.83.14.99:8090/stream.mkv    (VLC or ffplay; browsers do not play MJPEG in Matroska)
    The camera's MJPEG frames are copied, not re-encoded, so it costs little CPU; the network is the
    limit. Measured video data rate on 2026-11-02: 1280x720 15 fps 17 Mbit/s, 30 fps 33; 1920x1080
    15 fps 32, 30 fps 64; 2560x1440 15 fps 55, 30 fps 111. Received on the Mac over Tailscale (direct,
    7 ms): 1080p 15 fps 32.6, 720p 30 fps 32.9 (both keep up); 1080p 20 fps 38.2 of 42 needed, 1080p
    24/30 fps stuck at 31: the link tops out near 33-38 Mbit/s. A later 60 s pull at 1080p 15 fps
    got only 8 frames per second through, so the default is 1280x720 at 30 fps; 1080p is
    `--size 1920x1080 --fps 15` and may stutter. The mic is stereo, native 16 kHz. It opens
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
PORT = int(next((a for a in sys.argv[1:] if a.isdigit() and len(a) > 2), 8090))


def opt(name: str, default: str) -> str:
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


SIZE, FPS = opt('--size', '1280x720'), opt('--fps', '30')
HEAD = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-fflags', 'nobuffer']
if VIDEO:
    PATH, TYPE = '/stream.mkv', 'video/x-matroska'
    FFMPEG = HEAD + ['-use_wallclock_as_timestamps', '1', '-f', 'v4l2', '-input_format', 'mjpeg',
                     '-video_size', SIZE, '-framerate', FPS, '-i', '/dev/video0',
                     '-f', 'alsa', '-i', DEVICE, '-ac', '2', '-c:v', 'copy', '-c:a', 'aac',
                     '-b:a', '128k', '-flush_packets', '1', '-f', 'matroska', '-live', '1',
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
        self.q = queue.Queue(maxsize=320)  # 64 KB chunks: about 5 s at 32 Mbit/s
        self.started = not VIDEO  # video clients wait for the next cluster boundary
        self.prev = b''


def pump() -> None:
    global header
    proc = subprocess.Popen(FFMPEG, stdout=subprocess.PIPE)
    seen = b''
    while True:
        chunk = proc.stdout.read1(65536)
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
                except queue.Full:  # slow client: drop its backlog and rejoin at the next cluster
                    with c.q.mutex:
                        c.q.queue.clear()
                    c.started = not VIDEO
                    c.prev = b''


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
