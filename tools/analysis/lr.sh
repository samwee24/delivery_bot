#!/bin/bash
source /opt/ros/jazzy/setup.bash; source ~/ros2_ws/install/setup.bash
for k in 1 2 3; do timeout 10 ros2 topic echo /scan --once --csv --full-length > /tmp/lr$k.csv; done
python3 - <<'PY'
import math,statistics as st
for k in (1,2,3):
    v=open(f'/tmp/lr{k}.csv').read().strip().split(',')
    amin=float(v[3]);inc=float(v[5]);body=v[10:];n=len(body)//2
    r=[float(x) for x in body[:n]]
    def at(deg,w=3):
        out=[x for i,x in enumerate(r) if abs(math.degrees(amin+i*inc)-deg)<=w and math.isfinite(x) and x>0.15]
        return (round(st.median(out),3),len(out)) if out else None
    print(k,'left +90',at(90),'right -90',at(-90),'front 0',at(0),'back 180',at(180) or at(-180))
PY
