"""Hold the RPLidar A1 motor off: assert DTR on the USB adapter and keep the port open.

The adapter's DTR line drives the motor (asserted = off, released = on, as in the rplidar SDK).
Closing the port releases DTR, so the motor would spin up again: this script therefore stays
running until you stop it (Ctrl-C or `pkill -f lidar_off.py`). While it runs the lidar driver
cannot open /dev/rplidar, so stop it before launching lidar.launch.py.

    python3 tools/lidar_off.py            on the Pi
"""
import time

import serial

port = serial.Serial('/dev/rplidar', 115200)
port.dtr = True
print('lidar motor held off; Ctrl-C to release', flush=True)
while True:
    time.sleep(60)
