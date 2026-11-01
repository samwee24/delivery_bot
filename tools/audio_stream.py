"""Live microphone stream: camera mic (ALSA card U2K) -> ffmpeg -> MP3 over HTTP.

Run on the Pi:   python3 tools/audio_stream.py            (port 8090)
Listen anywhere: vlc http://100.83.14.99:8090/audio.mp3
                 ffplay -nodisp http://100.83.14.99:8090/audio.mp3
                 or open the URL in a browser (expect 2-5 s of buffering)

Any number of clients can connect and leave at any time; ffmpeg runs once. To tap it
from code later, read the same URL (a ROS node, a recorder: `ffmpeg -i <url> -c copy out.mp3`).
Not ROS on purpose: the stack stays thin and this needs no apt install.
"""
import os
import queue
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DEVICE = 'plughw:U2K'  # by card id, so a reordered card number does not break it
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8090
FFMPEG = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-fflags', 'nobuffer',
          '-f', 'alsa', '-i', DEVICE, '-ac', '1', '-ar', '44100',
          '-c:a', 'libmp3lame', '-b:a', '64k', '-flush_packets', '1', '-f', 'mp3', 'pipe:1']

clients = set()
lock = threading.Lock()


def pump() -> None:
    proc = subprocess.Popen(FFMPEG, stdout=subprocess.PIPE)
    while True:
        chunk = proc.stdout.read(1024)
        if not chunk:
            print('ffmpeg ended (device busy or missing?)', file=sys.stderr)
            os._exit(1)  # sys.exit would only end this thread
        with lock:
            for q in clients:
                try:
                    q.put_nowait(chunk)
                except queue.Full:  # slow client: drop audio rather than stall the others
                    pass


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != '/audio.mp3':
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', 'audio/mpeg')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        q = queue.Queue(maxsize=200)
        with lock:
            clients.add(q)
        try:
            while True:
                self.wfile.write(q.get())
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            with lock:
                clients.discard(q)

    def log_message(self, *_) -> None:
        pass


if __name__ == '__main__':
    threading.Thread(target=pump, daemon=True).start()
    ThreadingHTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
