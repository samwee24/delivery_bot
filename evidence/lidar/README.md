# Evidence — lidar

Append-only. New artefact = new dated file; never overwrite a run.

| File | Date | Machine | What it shows |
| --- | --- | --- | --- |
| `2026-10-21_scan_run1.png` | 2026-10-21 | `robot` @ 100.73.7.24 (offline) | One revolution from `test_lidar.py`: 105 points, nearest 0.23 m, farthest 7.45 m. Dotted arcs, no continuous walls. |
| `2026-10-21_composite_20revs.png` | 2026-10-21 | same | 20 revolutions overlaid. Confirms the sparsity is systematic, not a bad frame: 4.91 Hz, 95 valid points per revolution. |

## Key numbers from that session

| Quantity | Value |
| --- | --- |
| Model / firmware / hardware | A1M8 (`model 24`) / `1.29` / `7` |
| Serial | `EEA5ECF0C3E09ED2A0EA98F37D7D4110` |
| Health | `('Good', 0)` |
| Rotation | 4.9–6.9 Hz |
| Raw packets / revolution | 284 |
| Returns with a distance | 95–105 (**echo rate 33–35 %**) |
| Quality of arriving returns | median 15, max 15 |
| Max range seen | 8.7 m |
| Self-occlusion | 0.23 m returns at raw 230–250° |
| Dead sector | 45–75°, neighbours see 8.46 m (opening) |

Full analysis: [`../../docs/system/03_bringup.md`](../../docs/system/03_bringup.md).

## Reproduce

```bash
ssh robot@sherm-raspi.local
source ~/botenv/bin/activate
cd ~/delivery-bot
python scripts/test_lidar.py                # writes scan.png
python scripts/probe_echo_rate.py 6         # per-sector echo table
scp robot@sherm-raspi.local:~/delivery-bot/scan.png 2026-10-22_scan.png
```

The next artefact this folder needs is a **50 cm white-box control** on
`sherm-raspi` — that one decides whether the 33 % is optics or the room.
