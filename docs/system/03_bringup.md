# 03 · Bring-up evidence (P0 / P1)

Raw artefacts: [`../evidence/lidar/`](../../evidence/lidar/). Session log: [`../notes.md`](../../notes/notes.md).

## P1 lidar — status: **partially verified**

All numbers below come from `robot` @ `100.73.7.24` (Debian 13), which is now
offline. **They are not re-verified on `sherm-raspi`.**

> **D5 update (2026-10-22).** The stack moves to `rplidar_ros` (see
> [07_ros_stack.md](07_ros_stack.md)). The probe must therefore read `/scan` rather
> than the `rplidar` Python API: invalid returns are published as `inf` (range_max),
> not as `distance = 0`. The 50 cm white-box test below is unchanged and still the
> gate.

### Identity and health ✅

```python
from rplidar import RPLidar
l = RPLidar("/dev/rplidar", baudrate=115200, timeout=3)
l.get_info()    # {'model': 24, 'firmware': (1, 29), 'hardware': 7,
                #  'serialnumber': 'EEA5ECF0C3E09ED2A0EA98F37D7D4110'}
l.get_health()  # ('Good', 0)
```

| Item | Value | Expected |
| --- | --- | --- |
| Model | `model: 24` → **A1M8** | 24 for A1-series ✅ |
| Firmware / hardware | `1.29` / `7` | — |
| Baud | 115200 (256000 tested, not needed) | A1 = 115200 ✅ |
| Health | `('Good', 0)` | `Good` ✅ |
| Motor on start / stop on exit | yes / yes, in `finally` | ✅ |

### Scan behaviour ⚠️

| Quantity | Measured | Brief's expectation | |
| --- | --- | --- | --- |
| Rotation rate | 4.9–6.9 Hz | 5–10 Hz | ✅ |
| Raw packets per revolution | 284 | ~360–400 | ⚠️ low |
| **Returns with a distance** | **95–105** | 300–400 | ❌ |
| **Echo rate** | **33–35 %** (3 consecutive runs: 34, 35, 35 %) | >90 % | ❌ |
| Quality of arriving returns | median 15, max 15 | strong | ✅ |
| Max range seen | 8.5–8.7 m | ~8 m | ✅ |
| Angular step | ~1.27°, smooth, no sync errors | — | ✅ |
| Exceptions raised | none (`Wrong body size`, descriptor errors absent) | — | ✅ |

**Conclusion:** the serial link is clean and the sensor is talking; the loss is
photonic, not electrical. 67 % of pings come back with `distance = 0`.

### Where the echoes are missing

Per 15° sector, from `scripts/probe_echo_rate.py`:

| raw angle | echo % | median dist | Reading |
| --- | --- | --- | --- |
| 0–15° | 41 % | 0.36 m | clutter near the robot |
| 15–30° | **11 %** | **1.31 m** (max 1.32) | flat surface at 1.3 m, one ping in nine → **not range, not geometry** |
| 30–45° | 25 % | 8.46 m | opening / long view |
| 45–75° | **0 %** | — | neighbours see 8.46 m → beam escapes through an opening ✅ |
| 120–150° | 66–68 % | 1.8–2.6 m | wall |
| 195–225° | **80–82 %** | 0.85 m | best sector in the room |
| 240–255° | 34 % | **0.23 m** | robot's own structure → `mask_deg` candidate |
| 315–330° | **10 %** | 0.56 m | |

No sector exceeds 82 %, so there is a uniform ~20 % loss floor even on the best
wall — consistent with film/dust on the scan window rather than room geometry.

### Decisive test still outstanding

Put a white box or sheet **50 cm** in front of the lidar, clear space all round,
and re-run `probe_echo_rate.py`:

| Result | Verdict |
| --- | --- |
| ~95–100 % | optics fine; the room is dark/glassy → mask the bad sectors, continue |
| ~30–50 % | film / dirty or damaged window → clean it, re-test |
| ~30 % after cleaning | weak laser → treat as a short-range sensor or swap the unit |

**Second control experiment:** `sherm-raspi` has its own CP210x lidar plugged in.
Same code, different mounting. ~90 % there means the old mounting was the problem;
~35 % there means the unit or the series is.

## Script quirk

The brief's `iter_scans(..., min_len=100)` drops every revolution with fewer than
100 valid points — about half of them — so the printed rate (`~0.9 Hz`) is an
artefact. True rate, measured off the `new_scan` flag: **5–7 Hz**. Diagnostics use
`min_len=5`.

## P1 — not started

| Check | State |
| --- | --- |
| Each wheel spins both ways | ⏸ `test_motors.py` not written; GPIO library choice still open on Ubuntu (see [02_pi_setup.md](02_pi_setup.md)) |
| Gyro reads ~0 °/s at rest after bias removal | ⏸ `i2cdetect -y 1` never run; MPU6050 not probed |
| Scan of the room plots correctly | ⚠️ plots, but sparse — see OI-4 |

## How to reproduce

```bash
ssh robot@sherm-raspi.local
source ~/botenv/bin/activate
python ~/delivery-bot/scripts/test_lidar.py            # image
python scripts/probe_echo_rate.py                      # per-sector echo table
scp robot@sherm-raspi.local:~/delivery-bot/scan.png .
```
