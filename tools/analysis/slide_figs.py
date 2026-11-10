#!/usr/bin/env python3
"""Presentation figures from backed-up bags and logged numbers. Mac only (.venv: rosbags, matplotlib).

Usage: .venv/bin/python tools/analysis/slide_figs.py [BAGS_DIR] [OUT_DIR]
Defaults: ../delivery_bot_pi_backup/bags and report/figures. Writes 2026-11-10_*.png / .gif.
Times are bag receive times (as pushwall.py, turn_an.py). Hard-coded numbers are copied from
docs/test_log.md rows named next to them; bag-derived numbers are printed for the record.
"""
import math
import os
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from rosbags.highlevel import AnyReader

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from turn_an import unwrap, integrate  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BAGS = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / 'delivery_bot_pi_backup' / 'bags'
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / 'report' / 'figures'
P = '2026-11-10_'
LASER_X = 0.02  # base_link -> laser, /tf_static in every bag
BG, INK, MUTED, BLUE, ORANGE, GREY = '#fbfbf8', '#14213d', '#5a6372', '#1f6fb2', '#e07a1f', '#c9ccd1'
plt.rcParams.update({'figure.facecolor': BG, 'axes.facecolor': BG, 'savefig.facecolor': BG,
                     'text.color': INK, 'axes.labelcolor': INK, 'xtick.color': MUTED, 'ytick.color': MUTED,
                     'axes.edgecolor': GREY, 'font.size': 14, 'axes.titlesize': 16,
                     'axes.spines.top': False, 'axes.spines.right': False})


def yaw_of(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


def read(bag, topics):
    """topic -> list of (t_s, msg), bag receive time."""
    out = {t: [] for t in topics}
    with AnyReader([BAGS / bag]) as r:
        cons = [c for c in r.connections if c.topic in topics]
        for c, t, raw in r.messages(connections=cons):
            out[c.topic].append((t * 1e-9, r.deserialize(raw, c.msgtype)))
    return out


def scan_xy(m, every=1):
    """LaserScan -> (N, 2) points in base_footprint (laser is 2 cm ahead, no rotation)."""
    r = np.asarray(m.ranges, dtype=float)[::every]
    a = (m.angle_min + np.arange(len(m.ranges)) * m.angle_increment)[::every]
    ok = np.isfinite(r) & (r > max(m.range_min, 0.12)) & (r < m.range_max)
    return np.c_[r[ok] * np.cos(a[ok]) + LASER_X, r[ok] * np.sin(a[ok])]


def tf_track(tf_msgs, parent, child):
    """[(t, x, y, yaw)] for one TF edge."""
    rows = []
    for t, m in tf_msgs:
        for tr in m.transforms:
            if tr.header.frame_id == parent and tr.child_frame_id == child:
                rows.append((t, tr.transform.translation.x, tr.transform.translation.y, yaw_of(tr.transform.rotation)))
    return np.array(rows)


def pose_at(track, t, hold=False):
    """Pose of a TF track at time t: linear interpolation, or last value before t when hold."""
    if hold:
        i = max(np.searchsorted(track[:, 0], t) - 1, 0)
        return track[i, 1:]
    yaw = np.unwrap(track[:, 3])
    return np.array([np.interp(t, track[:, 0], track[:, k]) for k in (1, 2)] + [np.interp(t, track[:, 0], yaw)])


def compose(a, b):
    x, y, th = a
    return np.array([x + b[0] * math.cos(th) - b[1] * math.sin(th), y + b[0] * math.sin(th) + b[1] * math.cos(th), th + b[2]])


def place(pts, pose):
    c, s = math.cos(pose[2]), math.sin(pose[2])
    return pts @ np.array([[c, s], [-s, c]]) + pose[:2]


class Grid:
    """Hit counts on a 5 cm grid, the map's resolution."""
    def __init__(self, x0, y0, x1, y1, res=0.05):
        self.x0, self.y0, self.res = x0, y0, res
        self.h = np.zeros((int((y1 - y0) / res) + 1, int((x1 - x0) / res) + 1))

    def add(self, pts):
        i = ((pts[:, 1] - self.y0) / self.res).astype(int)
        j = ((pts[:, 0] - self.x0) / self.res).astype(int)
        ok = (i >= 0) & (i < self.h.shape[0]) & (j >= 0) & (j < self.h.shape[1])
        np.add.at(self.h, (i[ok], j[ok]), 1)

    def extent(self):
        return [self.x0, self.x0 + self.h.shape[1] * self.res, self.y0, self.y0 + self.h.shape[0] * self.res]


# ---------- map bag: building GIF and odometry-only vs SLAM ----------

def map_bag():
    d = read('2026-10-31_map_200956', ['/scan', '/tf'])
    odom_base = tf_track(d['/tf'], 'odom', 'base_footprint')
    map_odom = tf_track(d['/tf'], 'map', 'odom')
    t_ok = max(odom_base[0, 0], map_odom[0, 0]) + 6.0  # EKF settles: poses jump up to 3 m in the first 5 s
    scans = [(t, m) for t, m in d['/scan'] if t_ok <= t <= odom_base[-1, 0]]
    rows = []  # (t, odom-only pose, slam pose, points in base)
    for t, m in scans[::2]:
        ob = pose_at(odom_base, t)
        rows.append((t, ob, compose(pose_at(map_odom, t, hold=True), ob), scan_xy(m, every=2)))
    allp = np.vstack([place(p, s) for _, _, s, p in rows[::10]])
    lo, hi = np.percentile(allp, 0.5, axis=0) - 0.5, np.percentile(allp, 99.5, axis=0) + 0.5
    print(f'map bag: {len(scans)} scans used, {len(rows)} placed, {rows[-1][0] - rows[0][0]:.0f} s')
    return rows, lo, hi


def fig_odom_vs_slam(rows, lo, hi):
    fig, axs = plt.subplots(1, 2, figsize=(16, 7.5))
    for ax, k, title in ((axs[0], 1, 'Odometry only'), (axs[1], 2, 'With SLAM')):
        g = Grid(lo[0], lo[1], hi[0], hi[1])
        for r in rows:
            g.add(place(r[3], r[k]))
        ax.imshow(np.log1p(g.h), origin='lower', extent=g.extent(), cmap='Greys', vmax=np.log1p(g.h).max() * 0.6)
        path = np.array([r[k][:2] for r in rows])
        ax.plot(path[:, 0], path[:, 1], color=ORANGE, lw=2)
        ax.set_title(title, fontsize=22)
        ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values(): s.set_visible(False)
    fig.tight_layout(rect=(0, 0.04, 1, 0.95))
    fig.savefig(OUT / f'{P}odom_vs_slam.png', dpi=130)
    plt.close(fig)


def gif_map_build(rows, lo, hi, frames=90):
    g = Grid(lo[0], lo[1], hi[0], hi[1])
    fig, ax = plt.subplots(figsize=(9, 9 * (hi[1] - lo[1]) / (hi[0] - lo[0]) + 0.6))
    im = ax.imshow(np.zeros_like(g.h), origin='lower', extent=g.extent(), cmap='Greys', vmin=0, vmax=3)
    path_ln, = ax.plot([], [], color=ORANGE, lw=2)
    cur = ax.scatter([], [], s=4, color=BLUE)
    bot = ax.scatter([], [], s=120, color=ORANGE, edgecolor=INK, zorder=5)
    ttl = ax.text(0.02, 0.98, '', transform=ax.transAxes, va='top', fontsize=16, color=MUTED)
    ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_visible(False)
    idx = np.linspace(0, len(rows) - 1, frames).astype(int)
    state = {'n': 0}

    def step(f):
        for r in rows[state['n']:idx[f] + 1]:
            g.add(place(r[3], r[2]))
        state['n'] = idx[f] + 1
        r = rows[idx[f]]
        im.set_data(np.log1p(g.h))
        path = np.array([q[2][:2] for q in rows[:idx[f] + 1]])
        path_ln.set_data(path[:, 0], path[:, 1])
        cur.set_offsets(place(r[3], r[2]))
        bot.set_offsets([r[2][:2]])
        ttl.set_text(f'{r[0] - rows[0][0]:3.0f} s')
        return im, path_ln, cur, bot, ttl

    anim = FuncAnimation(fig, step, frames=frames, blit=False)
    anim.save(OUT / f'{P}map_build.gif', writer=PillowWriter(fps=12), dpi=80)
    plt.close(fig)


# ---------- OI-8: person behind the robot ----------

def gif_oi8(t_a=12.0, t_b=42.0, push=(17.0, 37.0), true_m=1.222):
    """Window from test_log 2026-11-03 'OI-8 bad bags of 2026-11-01 re-read' (17-37 s, 1.222 m front-wall change)."""
    d = read('2026-11-01_push_230535', ['/scan', '/odom_rf2o'])
    t0 = d['/scan'][0][0]
    scans = [(t - t0, m) for t, m in d['/scan'] if t_a <= t - t0 <= t_b]
    od = [(t - t0, m.pose.pose.position.x, m.pose.pose.position.y, yaw_of(m.pose.pose.orientation)) for t, m in d['/odom_rf2o']]
    od = np.array([o for o in od if t_a <= o[0] <= t_b])
    x0, y0, th0 = od[0, 1:]
    along = (od[:, 1] - x0) * math.cos(th0) + (od[:, 2] - y0) * math.sin(th0)

    def front(m):
        a = m.angle_min + np.arange(len(m.ranges)) * m.angle_increment
        r = np.asarray(m.ranges, float)
        ok = np.isfinite(r) & (np.abs(a) < math.radians(3))
        return np.median(r[ok]) if ok.any() else np.nan

    fr = np.array([front(m) for _, m in scans])
    fr = np.array([np.nanmedian(fr[max(0, i - 3):i + 4]) for i in range(len(fr))])
    ts = np.array([t for t, _ in scans])
    truth = fr[0] - fr
    print(f'OI-8 gif: {len(scans)} scans; wall change {truth[-1]:.3f} m (test_log 1.222), rf2o {along[-1]:.3f} m (test_log 0.291 max x)')

    fig = plt.figure(figsize=(14, 6.5))
    ax = fig.add_axes((0.03, 0.08, 0.42, 0.82))
    ax2 = fig.add_axes((0.55, 0.14, 0.42, 0.72))
    ax.set_xlim(-2.2, 2.6); ax.set_ylim(-2.0, 2.0); ax.set_aspect('equal')
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_visible(False)
    ax.add_patch(plt.Rectangle((-0.12, -0.1), 0.24, 0.2, color=INK))
    ax.annotate('', xy=(0.45, 0), xytext=(0.15, 0), arrowprops=dict(arrowstyle='->', color=INK, lw=2))
    sc_f = ax.scatter([], [], s=6, color=BLUE, label='scan')
    sc_r = ax.scatter([], [], s=14, color=ORANGE, label='person behind')
    ax.legend(loc='upper left', frameon=False, fontsize=14, markerscale=2)
    ax2.set_xlim(t_a, t_b); ax2.set_ylim(-0.05, 1.35)
    ax2.axvspan(*push, color=GREY, alpha=0.35, lw=0)
    ax2.text(push[0] + 0.3, 1.28, 'push', color=MUTED, fontsize=12)
    l_true, = ax2.plot([], [], color=INK, lw=2.5, label='real')
    l_rf, = ax2.plot([], [], color=ORANGE, lw=2.5, label='odometry')
    ax2.set_xlabel('time (s)'); ax2.set_ylabel('distance (m)')
    ax2.legend(loc='upper left', frameon=False, fontsize=15, bbox_to_anchor=(0, 0.93))

    def step(i):
        t, m = scans[i]
        p = scan_xy(m)
        a = np.arctan2(p[:, 1], p[:, 0] - LASER_X)
        rr = np.hypot(p[:, 0] - LASER_X, p[:, 1])
        rear = (np.abs(a) > math.radians(135)) & (rr < 1.2)
        sc_f.set_offsets(p[~rear]); sc_r.set_offsets(p[rear] if rear.any() else np.empty((0, 2)))
        l_true.set_data(ts[:i + 1], truth[:i + 1])
        k = od[:, 0] <= t
        l_rf.set_data(od[k, 0], along[k])
        return sc_f, sc_r, l_true, l_rf

    anim = FuncAnimation(fig, step, frames=len(scans), blit=False)
    anim.save(OUT / f'{P}oi8_person_behind.gif', writer=PillowWriter(fps=14), dpi=75)
    step(len(scans) - 1)
    fig.savefig(OUT / f'{P}oi8_person_behind_last.png', dpi=130)
    plt.close(fig)


# ---------- hand turn: gyro vs rf2o ----------

def fig_turn():
    d = read('2026-10-31_turn_194945', ['/imu/data', '/odom_rf2o'])
    t0 = d['/odom_rf2o'][0][0]
    u = unwrap([(t, yaw_of(m.pose.pose.orientation)) for t, m in d['/odom_rf2o']])
    gz = [(t, m.angular_velocity.z) for t, m in d['/imu/data']]
    g = np.cumsum([0] + [gz[i][1] * (gz[i][0] - gz[i - 1][0]) for i in range(1, len(gz))])
    rf_end, g_end = math.degrees(u[-1][1]), math.degrees(integrate(gz))
    print(f'turn: rf2o {rf_end:.1f} deg, gyro {g_end:.1f} deg (test_log -352.9 / -360.2)')
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot([t - t0 for t, _ in gz], -np.degrees(g), color=BLUE, lw=2.5, label=f'gyro {-g_end:.1f}°')
    ax.plot([t - t0 for t, _ in u], [-math.degrees(a) for _, a in u], color=ORANGE, lw=2.5, label=f'lidar odometry {-rf_end:.1f}°')
    ax.axhline(360, color=GREY, ls='--'); ax.text(76, 368, 'true 360°', color=MUTED)
    ax.set_xlim(75, 150)
    ax.set_xlabel('time (s)'); ax.set_ylabel('heading (deg)')
    ax.legend(loc='lower right', frameon=False, fontsize=16)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(OUT / f'{P}turn_gyro_vs_rf2o.png', dpi=130)
    plt.close(fig)


# ---------- straights: rf2o traces ----------

def fig_straights():
    runs = [  # bag, tape m, label (test_log 2026-11-10 CP5 rows)
        ('2026-11-10_CP5_straight_run2', 0.74, 'low battery'),
        ('2026-11-10_CP5_straight_run3', 0.38, 'flat battery'),
        ('2026-11-10_CP5_straight_run4', 1.06, 'pass'),
        ('2026-11-10_CP5_straight_run5', 1.16, 'overshoot'),
    ]
    cols = [GREY, '#9aa0a8', BLUE, ORANGE]
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.axhspan(0.9, 1.1, color=BLUE, alpha=0.08, lw=0)
    ax.text(13.8, 0.92, 'pass 0.9-1.1 m', color=MUTED, fontsize=13, ha='right')
    for (bag, tape, lab), c in zip(runs, cols):
        od = read(bag, ['/odom_rf2o'])['/odom_rf2o']
        a = np.array([(t, m.pose.pose.position.x, m.pose.pose.position.y, yaw_of(m.pose.pose.orientation)) for t, m in od])
        al = (a[:, 1] - a[0, 1]) * math.cos(a[0, 3]) + (a[:, 2] - a[0, 2]) * math.sin(a[0, 3])
        mv = np.nonzero(np.abs(al) > 0.005)[0]
        ts = a[:, 0] - (a[mv[0], 0] if len(mv) else a[0, 0])
        ax.plot(ts, al, color=c, lw=2.5, label=f'{lab}  {tape:.2f} m')
        print(f'{bag}: rf2o along {al[-1]:.3f} m, tape {tape}')
    ax.set_xlim(-1, 14)
    ax.set_xlabel('time (s)'); ax.set_ylabel('distance (m)')
    ax.legend(loc='lower right', frameon=False, fontsize=15)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(OUT / f'{P}straights.png', dpi=130)
    plt.close(fig)


# ---------- charts from logged numbers ----------

def fig_motor():
    duty = np.array([0.20, 0.16, 0.14, 0.12, 0.10])  # notes 2026-11-09 (late), duty staircase at 100 Hz
    speed = np.array([0.293, 0.213, 0.156, 0.094, 0.0])
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.axhspan(0, 0.094, color=ORANGE, alpha=0.12, lw=0)
    ax.text(0.205, 0.012, 'stall', color=ORANGE, fontsize=16, ha='right')
    xs = np.linspace(0.078, 0.21, 50)
    ax.plot(xs, 2.46 * (xs - 0.078), color=BLUE, lw=2, label='fit 2.46 x (duty - 0.078)')
    ax.scatter(duty, speed, s=80, color=INK, zorder=5, label='measured')
    for v, lab in ((0.15, 'cap 0.15'), (0.10, 'Nav2 min, after fix'), (0.045, 'Nav2 slowdown, before')):
        ax.axhline(v, color=MUTED, ls=':', lw=1.5)
        ax.text(0.081, v + 0.006, lab, color=MUTED, fontsize=14)
    ax.set_xlim(0.075, 0.21); ax.set_ylim(-0.01, 0.32)
    ax.set_xlabel('PWM duty'); ax.set_ylabel('speed (m/s)')
    ax.legend(loc='upper left', frameon=False, fontsize=15)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(OUT / f'{P}motor_curve.png', dpi=130)
    plt.close(fig)


def fig_bars():
    fig, axs = plt.subplots(1, 2, figsize=(16, 6.5), gridspec_kw={'width_ratios': [1.25, 1]})
    # OI-8: rf2o / real travel, test_log 2026-11-03 rows
    lab = ['nobody\nrun A', 'nobody\nrun B', 'person\nrun C', 'person\nrun D', 'person,\n0.6 m cut']
    val = [1.008, 0.961, 0.28, 0.25, 0.995]
    col = [BLUE, BLUE, ORANGE, ORANGE, BLUE]
    b = axs[0].bar(lab, [v * 100 for v in val], color=col)
    axs[0].bar_label(b, labels=[f'{v * 100:.0f} %' for v in val], fontsize=13)
    axs[0].axhline(100, color=GREY, ls='--')
    axs[0].set_ylabel('odometry / real (%)'); axs[0].set_ylim(0, 118)
    axs[0].tick_params(axis='x', labelsize=14)
    # replay repeatability, test_log 2026-11-03 'replay repeatability'
    lab2 = ['live', 'replay 1', 'replay 2', 'replay 3']
    val2 = [0.962, 0.679, 0.592, 0.531]
    b2 = axs[1].bar(lab2, val2, color=[BLUE, GREY, GREY, GREY])
    axs[1].bar_label(b2, labels=[f'{v:.3f} m' for v in val2], fontsize=13)
    axs[1].set_ylabel('odometry (m)'); axs[1].set_ylim(0, 1.1)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(OUT / f'{P}oi8_and_replay_bars.png', dpi=130)
    plt.close(fig)


def fig_power():
    fig, ax = plt.subplots(figsize=(11, 5.5))
    lab = ['wall supply', 'power bank']
    val = [193 / 286 * 100, 0.0]
    b = ax.bar(lab, val, color=[ORANGE, BLUE], width=0.5)
    ax.bar_label(b, labels=['67.5 %', '0 %'], fontsize=18)
    ax.set_ylabel('time under-voltage (%)'); ax.set_ylim(0, 85)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(OUT / f'{P}power.png', dpi=130)
    plt.close(fig)


CHALLENGES = [  # outline section 7: (id, start day, end day, layer, short label); day 0 = 2026-10-20
    ('C1', 1, 3, 'Sensor', 'lidar misses a third of pings'),
    ('C2', 2, 3, 'Platform', 'brief\'s Pi offline, SSH hangs'),
    ('C3', 2, 2.6, 'Software', 'own maths vs ROS 2 packages (D5)'),
    ('C4', 10, 11, 'Software', 'slam_toolbox drops every scan'),
    ('C5', 12, 13, 'Sensor', 'lidar start hang'),
    ('C6', 12, 14, 'Sensor', 'odometry reads 25 %: person behind'),
    ('C7', 13, 14, 'Method', 'replays not repeatable'),
    ('C8', 20, 20.6, 'Software', 'Nav2 message type, wheels silent'),
    ('C9', 20, 21, 'Motor', 'curve, stall, PWM overshoot'),
    ('C10', 20, 20.6, 'Hardware', 'loose wire reboots the Pi'),
    ('C11', 20, 21, 'Power', 'under-voltage, Nav2 shuts down'),
    ('C12', 21, 21.6, 'Software', '"live" runs were dry runs'),
    ('C13', 21, 21.6, 'Hardware', 'battery fades after one run'),
    ('C14', 21, 22, 'Navigation', 'Nav2 fails 7 ways, then succeeds'),
]
CHECKPOINTS = [(1, 'lidar up'), (2, 'stack chosen'), (11, 'robot built,\nfirst map'), (12, 'localisation'),
               (14, 'OI-8\nexplained'), (20, 'motors live'), (21, 'robot drives\n1 m'), (21.7, 'Nav2 goal,\nbox')]


def fig_timeline():
    layers = ['Sensor', 'Platform', 'Software', 'Method', 'Motor', 'Hardware', 'Power', 'Navigation']
    cmap = dict(zip(layers, ['#1f6fb2', '#7a8696', '#4c9bd6', '#9aa0a8', '#e07a1f', '#b8621a', '#f2a65a', '#14213d']))
    fig, ax = plt.subplots(figsize=(16, 8.5))
    n = len(CHALLENGES)
    for k, (cid, a, b, layer, lab) in enumerate(CHALLENGES):
        y = n - k
        ax.barh(y, max(b - a, 0.5), left=a, height=0.65, color=cmap[layer])
        ax.text(b + 0.25, y, f'{cid}  {lab}', va='center', fontsize=15)
    for k, (d, lab) in enumerate(CHECKPOINTS):  # alternate label heights, neighbours are 1 day apart
        ax.axvline(d, color=GREY, lw=1, ls=':', zorder=0)
        ax.text(d, n + 1.4 + 1.3 * (k % 2), lab, ha='center', va='bottom', fontsize=13, color=INK)
    ax.scatter([d for d, _ in CHECKPOINTS], [n + 1.0] * len(CHECKPOINTS), marker='D', s=70, color=INK, zorder=5)
    days = [0, 3, 8, 11, 14, 17, 20, 22]
    ax.set_xticks(days, [f'{20 + d}/10' if 20 + d <= 31 else f'{20 + d - 31}/11' for d in days])
    ax.set_yticks([]); ax.spines['left'].set_visible(False)
    ax.set_xlim(-0.5, 30); ax.set_ylim(0, n + 4.6)
    handles = [plt.Rectangle((0, 0), 1, 1, color=cmap[l]) for l in layers]
    ax.legend(handles, layers, loc='lower left', frameon=False, ncol=4, fontsize=14)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(OUT / f'{P}challenge_timeline.png', dpi=130)
    plt.close(fig)


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    fig_motor(); fig_bars(); fig_power(); fig_timeline()
    fig_turn(); fig_straights()
    gif_oi8()
    rows, lo, hi = map_bag()
    fig_odom_vs_slam(rows, lo, hi)
    gif_map_build(rows, lo, hi)
    for f in sorted(OUT.glob(f'{P}*')):
        print(f.name, f'{f.stat().st_size / 1e6:.2f} MB')
