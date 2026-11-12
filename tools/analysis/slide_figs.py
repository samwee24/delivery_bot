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
BG, INK, MUTED, BLUE, ORANGE, GREY = '#ffffff', '#14213d', '#5a6372', '#1f6fb2', '#e07a1f', '#c9ccd1'
plt.rcParams.update({'figure.facecolor': BG, 'axes.facecolor': BG, 'savefig.facecolor': BG,
                     'text.color': INK, 'axes.labelcolor': INK, 'xtick.color': MUTED, 'ytick.color': MUTED,
                     'axes.edgecolor': GREY, 'font.size': 16, 'axes.titlesize': 16,
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


def moving_span(rows):
    """Row indices from 3 s before the robot is first 0.3 m from its start (it sat still ~150 s while
    SLAM settled) to 3 s after it last moves."""
    t = np.array([r[0] for r in rows])
    far = next(i for i, r in enumerate(rows) if np.hypot(*(r[2][:2] - rows[0][2][:2])) > 0.3)
    step = np.hypot(*np.diff(np.array([r[2][:2] for r in rows]), axis=0).T)
    return (int(np.searchsorted(t, t[far] - 3.0)),
            int(np.searchsorted(t, t[np.nonzero(step > 0.01)[0][-1]] + 3.0)))


def gif_map_build(rows, lo, hi, frames=110, fps=8):
    g = Grid(lo[0], lo[1], hi[0], hi[1])
    k0, k1 = moving_span(rows)  # the scans before k0 seed the first frame
    for r in rows[:k0]:
        g.add(place(r[3], r[2]))
    t_start = rows[k0][0]
    print(f'map gif: {t_start - rows[0][0]:.0f}-{rows[min(k1, len(rows) - 1)][0] - rows[0][0]:.0f} s of the bag; '
          f'{frames} frames at {fps} fps = {frames / fps:.0f} s')
    rows = rows[k0:k1 + 1]
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
        ttl.set_text(f'{r[0] - t_start:3.0f} s')
        return im, path_ln, cur, bot, ttl

    anim = FuncAnimation(fig, step, frames=frames, blit=False)
    anim.save(OUT / f'{P}map_build.gif', writer=PillowWriter(fps=fps), dpi=80)
    plt.close(fig)


# ---------- OI-8: person behind the robot ----------

def gif_oi8(t_a=12.0, t_b=42.0, push=(17.0, 37.0), true_m=1.222, tall=False):
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

    if tall:  # stacked for a slide window: scan on top, distance below
        fig = plt.figure(figsize=(9, 7.6), facecolor='white')
        ax = fig.add_axes((0.02, 0.42, 0.96, 0.56))
        ax2 = fig.add_axes((0.11, 0.08, 0.86, 0.3))
    else:
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
    name = f'{P2}oi8_person_behind_tall' if tall else f'{P}oi8_person_behind'
    if tall:
        for a_ in (ax, ax2): a_.set_facecolor('white')
        ax.set_ylim(-1.7, 2.1)
    anim.save(OUT / f'{name}.gif', writer=PillowWriter(fps=14), dpi=75, savefig_kwargs={'facecolor': fig.get_facecolor()})
    step(len(scans) - 1)
    fig.savefig(OUT / f'{name}_last.png', dpi=130)
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
    fig, ax = plt.subplots(figsize=(12, 7.45))
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
    fig, ax = plt.subplots(figsize=(12, 6.9))
    ax.axhspan(0.9, 1.1, color=BLUE, alpha=0.08, lw=0)
    ax.text(13.8, 0.92, 'pass 0.9-1.1 m', color=MUTED, fontsize=13, ha='right')
    for (bag, tape, lab), c in zip(runs, cols):
        od = read(bag, ['/odom_rf2o'])['/odom_rf2o']
        a = np.array([(t, m.pose.pose.position.x, m.pose.pose.position.y, yaw_of(m.pose.pose.orientation)) for t, m in od])
        al = (a[:, 1] - a[0, 1]) * math.cos(a[0, 3]) + (a[:, 2] - a[0, 2]) * math.sin(a[0, 3])
        mv = np.nonzero(np.abs(al) > 0.005)[0]
        ts = a[:, 0] - (a[mv[0], 0] if len(mv) else a[0, 0])
        ax.plot(ts, al, color=c, lw=2.5, label=f'{lab}: tape {tape:.2f} m')
        print(f'{bag}: rf2o along {al[-1]:.3f} m, tape {tape}')
    ax.set_xlim(-1, 14)
    ax.set_xlabel('time (s)'); ax.set_ylabel('distance from lidar odometry (m)')
    ax.legend(loc='lower right', frameon=False, fontsize=15)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(OUT / f'{P}straights.png', dpi=130)
    plt.close(fig)


# ---------- charts from logged numbers ----------

def fig_motor():
    duty = np.array([0.20, 0.16, 0.14, 0.12, 0.10])  # notes 2026-11-09 (late), duty staircase at 100 Hz
    speed = np.array([0.293, 0.213, 0.156, 0.094, 0.0])
    fig, ax = plt.subplots(figsize=(12, 6.9))
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
    ('C3', 2, 2.6, 'Software', 'own maths vs ROS 2 packages'),
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
               (14, 'person behind\nexplained'), (20, 'motors live'), (21, 'robot drives\n1 m'), (21.7, 'Nav2 goal,\nbox')]


def fig_timeline():
    layers = ['Sensor', 'Platform', 'Software', 'Method', 'Motor', 'Hardware', 'Power', 'Navigation']
    cmap = dict(zip(layers, ['#1f6fb2', '#7a8696', '#4c9bd6', '#9aa0a8', '#e07a1f', '#b8621a', '#f2a65a', '#14213d']))
    fig, ax = plt.subplots(figsize=(16, 8.5))
    n = len(CHALLENGES)
    for k, (cid, a, b, layer, lab) in enumerate(CHALLENGES):
        y = n - k
        ax.barh(y, max(b - a, 0.5), left=a, height=0.65, color=cmap[layer])
        ax.text(b + 0.25, y, lab, va='center', fontsize=15)  # no IDs: the audience never sees the challenge table
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


# ---------- 2026-11-11 additions ----------
P2 = '2026-11-11_'


def inverse(a):
    x, y, th = a
    c, s_ = math.cos(th), math.sin(th)
    return np.array([-(c * x + s_ * y), s_ * x - c * y, -th])


def room_map():
    """Saved map (map_saver_cli) as an image and its extent in the map frame."""
    import yaml
    from PIL import Image
    meta = yaml.safe_load(open(ROOT / 'results' / 'maps' / '2026-10-31_room2.yaml'))
    img = np.asarray(Image.open(ROOT / 'results' / 'maps' / meta['image']))
    ox, oy, res = meta['origin'][0], meta['origin'][1], meta['resolution']
    return img, [ox, ox + img.shape[1] * res, oy, oy + img.shape[0] * res]


def drift_paths(rows):
    """Odometry-only path moved into the map frame at the first pose, and the SLAM path."""
    m0 = compose(rows[0][2], inverse(rows[0][1]))
    return np.array([compose(m0, r[1])[:2] for r in rows]), np.array([r[2][:2] for r in rows])


def _drift_axes(ax, odo, sl):
    img, ext = room_map()
    ax.imshow(img, cmap='gray', vmin=0, vmax=255, extent=ext, alpha=0.35)
    both = np.vstack([odo, sl])
    lo, hi = both.min(axis=0) - 0.8, both.max(axis=0) + 0.8
    ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1])
    ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.scatter(*sl[0], s=160, color=INK, zorder=6, marker='o')
    ax.annotate('start = end\n(taped mark)', sl[0], xytext=(12, -38), textcoords='offset points', fontsize=14, color=INK)


def fig_drift_vs_slam(rows):
    odo, sl = drift_paths(rows)
    gap_o, gap_s = np.hypot(*(odo[-1] - odo[0])), np.hypot(*(sl[-1] - sl[0]))
    length = np.sum(np.hypot(*np.diff(sl, axis=0).T))
    print(f'drift: path {length:.1f} m, start-end gap odometry {gap_o:.3f} m, SLAM {gap_s:.3f} m')
    fig, ax = plt.subplots(figsize=(13, 8))
    _drift_axes(ax, odo, sl)
    ax.plot(odo[:, 0], odo[:, 1], color=ORANGE, lw=2.5, ls='--', label=f'odometry only: ends {gap_o:.2f} m from start')
    ax.plot(sl[:, 0], sl[:, 1], color=BLUE, lw=2.5, label=f'with SLAM: ends {gap_s:.2f} m from start')
    ax.scatter(*odo[-1], s=120, color=ORANGE, zorder=6, marker='X')
    ax.scatter(*sl[-1], s=120, color=BLUE, zorder=6, marker='X')
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.02), ncol=2, frameon=False, fontsize=16)
    fig.tight_layout()
    fig.savefig(OUT / f'{P2}drift_vs_slam.png', dpi=130)
    plt.close(fig)


def gif_drift_vs_slam(rows, frames=110, fps=8):
    """Both paths growing over the saved map; the odometry gap readout updates live."""
    odo, sl = drift_paths(rows)
    k0, k1 = moving_span(rows)
    t = np.array([r[0] for r in rows])
    fig, ax = plt.subplots(figsize=(11, 7.2))
    _drift_axes(ax, odo, sl)
    l_o, = ax.plot([], [], color=ORANGE, lw=2.5, ls='--', label='odometry only')
    l_s, = ax.plot([], [], color=BLUE, lw=2.5, label='with SLAM')
    d_o = ax.scatter([], [], s=110, color=ORANGE, zorder=7)
    d_s = ax.scatter([], [], s=110, color=BLUE, zorder=7)
    txt = ax.text(0.02, 0.98, '', transform=ax.transAxes, va='top', fontsize=16, color=INK)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.02), ncol=2, frameon=False, fontsize=16)
    fig.tight_layout()
    idx = np.linspace(k0, min(k1, len(rows) - 1), frames).astype(int)

    def step(f):
        k = idx[f] + 1
        l_o.set_data(odo[:k, 0], odo[:k, 1]); l_s.set_data(sl[:k, 0], sl[:k, 1])
        d_o.set_offsets([odo[k - 1]]); d_s.set_offsets([sl[k - 1]])
        txt.set_text(f'{t[k - 1] - t[k0]:3.0f} s   odometry off SLAM by {np.hypot(*(odo[k - 1] - sl[k - 1])):.2f} m')
        return l_o, l_s, d_o, d_s, txt

    FuncAnimation(fig, step, frames=frames, blit=False).save(OUT / f'{P2}drift_vs_slam.gif', writer=PillowWriter(fps=fps), dpi=80)
    print(f'drift gif: {frames} frames at {fps} fps = {frames / fps:.0f} s; final odometry-SLAM offset {np.hypot(*(odo[idx[-1]] - sl[idx[-1]])):.2f} m')
    plt.close(fig)


def fig_scan_gaps(rows, ray_m=3.0):
    """One real scan on the saved map at the robot's SLAM pose: what the lidar saw (blue) and the
    directions that returned nothing (orange rays). Picked mid-lap, in the open part of the room."""
    k0, k1 = moving_span(rows)
    t_pick, pose = rows[(k0 + k1) // 2][0], rows[(k0 + k1) // 2][2]
    d = read('2026-10-31_map_200956', ['/scan'])
    t, m = min(d['/scan'], key=lambda x: abs(x[0] - t_pick))
    r = np.asarray(m.ranges, float)
    a = m.angle_min + np.arange(len(r)) * m.angle_increment
    ok = np.isfinite(r) & (r > m.range_min)
    print(f'scan gaps: {len(r)} beams, {100 * (~ok).mean():.1f} % returned nothing; pose {pose[0]:.2f}, {pose[1]:.2f}')
    img, ext = room_map()
    fig, ax = plt.subplots(figsize=(13, 8))
    ax.imshow(img, cmap='gray', vmin=0, vmax=255, extent=ext, alpha=0.35)
    c, s_ = math.cos(pose[2]), math.sin(pose[2])
    ox, oy = pose[0] + LASER_X * c, pose[1] + LASER_X * s_
    for ang in a[~ok]:
        g = pose[2] + ang
        ax.plot([ox, ox + ray_m * math.cos(g)], [oy, oy + ray_m * math.sin(g)], color=ORANGE, lw=0.8, alpha=0.35)
    hits = place(scan_xy(m), pose)
    ax.scatter(hits[:, 0], hits[:, 1], s=10, color=BLUE, zorder=5)
    ax.scatter(pose[0], pose[1], s=180, color=INK, zorder=6)
    ax.annotate('', xy=(pose[0] + 0.5 * c, pose[1] + 0.5 * s_), xytext=(pose[0], pose[1]),
                arrowprops=dict(arrowstyle='->', color=INK, lw=2.5), zorder=6)
    ax.set_xlim(pose[0] - 5.5, pose[0] + 5.5); ax.set_ylim(pose[1] - 3.6, pose[1] + 3.6)
    ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.scatter([], [], s=60, color=BLUE, label='lidar return (what it saw)')
    ax.plot([], [], color=ORANGE, lw=3, alpha=0.6, label=f'no return: {100 * (~ok).mean():.0f} % of directions')
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.01), ncol=2, frameon=False, fontsize=16)
    fig.tight_layout()
    fig.savefig(OUT / f'{P2}scan_gaps.png', dpi=130)
    plt.close(fig)


def fig_sweep():
    """slam_toolbox settings sweep, test_log 2026-10-31 '5.5 sweep' (start-end gap over a 42 m lap)."""
    lab = ['chosen\nsettings', 'min range 0', 'travel 0.05 m', 'travel 0.2 m', 'loop closure\noff']
    val = [0.109, 0.123, 0.186, 0.113, 0.658]
    col = [BLUE, GREY, GREY, GREY, ORANGE]
    fig, ax = plt.subplots(figsize=(12, 6))
    b = ax.bar(lab, val, color=col, width=0.6)
    ax.bar_label(b, labels=[f'{v:.3f} m' for v in val], fontsize=16)
    ax.set_ylabel('start-end gap (m)'); ax.set_ylim(0, 0.75)
    ax.tick_params(axis='x', labelsize=15)
    fig.tight_layout()
    fig.savefig(OUT / f'{P2}slam_sweep.png', dpi=130)
    plt.close(fig)


GOALS_EVENING = [  # bt_navigator logs 2026-11-10 (launch pid, start epoch s, duration s, metres, outcome)
    ('7359', 1794323545.15, 92.8, 1.50, 'succeeded'),
    ('7359', 1794323751.82, 33.6, 1.50, 'cancelled'),
    ('7359', 1794323839.78, 42.3, 1.50, 'cancelled'),
    ('7930', 1794323944.31, 28.7, 1.50, 'cancelled'),
    ('1638', 1794324431.84, 29.3, 2.00, 'cancelled'),
    ('2673', 1794324607.50, 54.9, 2.00, 'cancelled'),
    ('3115', 1794324712.17, 21.9, 2.49, 'cancelled'),
    ('3503', 1794324812.62, 104.3, 2.50, 'cancelled'),
]
LADDER = [  # 2026-11-10 attempts before the first success, in order (test_log, handover, commits)
    ('aborted in 8 s, no motion', 'server timeout 20 → 1000 ms'),
    ('moved 0.30 m, TF error', 'tolerance 0.1 → 0.5 s'),
    ('"Failed to make progress"', 'home moved off obstacles'),
    ('"Transform data too old"', 'restamp_tf'),
    ('crept at 0.045 m/s, stalled', 'speeds ≥ 0.10 m/s'),
    ('drove backwards', 'reversing off'),
    ('final turn stalled', 'any final heading'),
]


def fig_goal_attempts():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 9), gridspec_kw={'width_ratios': [1.5, 1]})
    n = len(LADDER)
    for k, (sym, fix) in enumerate(LADDER):
        y = n - k
        ax1.barh(y, 1.25, color=ORANGE, height=0.7)
        ax1.text(0.03, y, sym, va='center', fontsize=17, color=BG)
        ax1.text(1.32, y, '→  ' + fix, va='center', fontsize=17, color=INK)
    ax1.barh(0, 1.25, color=BLUE, height=0.7)
    ax1.text(0.03, 0, '"Goal succeeded", 93 s', va='center', fontsize=17, color=BG)
    ax1.set_xlim(0, 2.6); ax1.set_ylim(-0.7, n + 0.7); ax1.axis('off')
    ax1.set_title('before the first success: symptom → fix', fontsize=19, loc='left')
    cmap = {'succeeded': BLUE, 'cancelled': GREY}
    for k, (pid, t, dur, dist, out) in enumerate(GOALS_EVENING):
        y = len(GOALS_EVENING) - k
        ax2.barh(y, dur, color=cmap[out], height=0.65)
        ax2.text(dur + 2, y, f'{dist:.1f} m, {out}', va='center', fontsize=16, color=INK)
    ax2.set_yticks([]); ax2.spines['left'].set_visible(False)
    ax2.set_xlabel('time on the goal (s)', fontsize=16); ax2.set_xlim(0, 175)
    ax2.set_title('evening goals, in order', fontsize=19, loc='left')
    fig.tight_layout()
    fig.savefig(OUT / f'{P2}nav_goal_attempts.png', dpi=130)
    plt.close(fig)


def fig_wrong_start():
    """test_log 2026-11-01 '6.4 wrong start' rows; placements by ruler and eye."""
    pts = [(30, 20, True), (30, 31, False), (60, 30, False)]
    fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.axhspan(0, 20, color=BLUE, alpha=0.08, lw=0)
    ax.text(68, 18.5, 'matcher search window ±20°', ha='right', va='top', fontsize=14, color=BLUE)
    for x, y, ok in pts:
        ax.scatter(x, y, s=260, color=BLUE if ok else ORANGE, marker='o' if ok else 'X', zorder=5)
        ax.annotate('recovers' if ok else 'lost', (x, y), xytext=(14, -6), textcoords='offset points', fontsize=15,
                    color=BLUE if ok else ORANGE)
    ax.scatter(0, 0, s=200, color=INK, marker='s', zorder=5)
    ax.annotate('home mark', (0, 0), xytext=(12, 6), textcoords='offset points', fontsize=14)
    ax.set_xlim(-5, 70); ax.set_ylim(-3, 40)
    ax.set_xlabel('placed off the mark (cm)'); ax.set_ylabel('turned off the mark (deg)')
    fig.tight_layout()
    fig.savefig(OUT / f'{P2}wrong_start.png', dpi=130)
    plt.close(fig)


ROOT_CAUSE = {  # slides_outline.md section 7, primary group per challenge (first listed)
    'cheap hardware': ['C1', 'C5', 'C9', 'C10', 'C11', 'C13'],
    'interface mismatch': ['C4', 'C8', 'C12'],
    'loaded computer': ['C7', 'C14'],
    'platform / process': ['C2', 'C3'],
    'algorithm assumption': ['C6'],
}
EXPECTED = {'C1', 'C3', 'C10', 'C13', 'C9', 'C14'}  # yes or partly, section 7
SHORT = {'C1': 'lidar gaps', 'C2': 'Pi offline', 'C3': 'own maths vs packages', 'C4': 'beam count',
         'C5': 'lidar start hang', 'C6': 'person behind', 'C7': 'replays', 'C8': 'message type',
         'C9': 'PWM, stall', 'C10': 'loose wire', 'C11': 'power', 'C12': 'dry run', 'C13': 'battery',
         'C14': 'Nav2 timing'}


def fig_root_cause():
    groups = list(ROOT_CAUSE)
    une = [sum(c not in EXPECTED for c in ROOT_CAUSE[g]) for g in groups]
    exp = [sum(c in EXPECTED for c in ROOT_CAUSE[g]) for g in groups]
    fig, ax = plt.subplots(figsize=(12, 6))
    y = np.arange(len(groups))[::-1]
    ax.barh(y, une, color=ORANGE, height=0.6, label='unexpected')
    ax.barh(y, exp, left=une, color=GREY, height=0.6, label='expected (or partly)')
    for yy, g in zip(y, groups):  # short names, not IDs
        ax.text(len(ROOT_CAUSE[g]) + 0.1, yy, ',\n'.join(', '.join(SHORT[c] for c in ROOT_CAUSE[g][i:i + 3]) for i in range(0, len(ROOT_CAUSE[g]), 3)), va='center', fontsize=13, color=MUTED)
    ax.set_yticks(y, groups, fontsize=15)
    ax.set_xlabel('challenges'); ax.set_xlim(0, 10); ax.set_xticks(range(0, 7))
    ax.legend(loc='lower right', frameon=False, fontsize=14)
    fig.tight_layout()
    fig.savefig(OUT / f'{P2}root_cause.png', dpi=130)
    plt.close(fig)



def fig_beam_count():
    """S2: beams per scan in the first map recording (angle_compensate off) vs the second (on)."""
    fig, ax = plt.subplots(figsize=(12, 6.2))
    for bag, col, lab in (('2026-10-31_map_200132', ORANGE, 'first map: angle_compensate off'),
                          ('2026-10-31_map_200956', BLUE, 'second map: angle_compensate on')):
        d = read(bag, ['/scan'])['/scan']
        t0 = d[0][0]
        n = np.array([len(m.ranges) for _, m in d])
        ax.plot([t - t0 for t, _ in d], n, color=col, lw=1.5, label=f'{lab} ({n.min()}-{n.max()} beams)' if n.min() != n.max() else f'{lab} ({n.min()} beams)')
        print(f'{bag}: {len(n)} scans, {n.min()}-{n.max()} beams, {100 * (n != n[0]).mean():.2f} % differ from the first')
    ax.axhline(931, color=INK, ls=':', lw=1.5)
    ax.text(5, 945, 'slam_toolbox expects 931 (the first scan) and rejects the rest', fontsize=14, color=INK)
    ax.set_xlabel('time (s)'); ax.set_ylabel('beams per scan'); ax.set_ylim(650, 1120)
    ax.legend(loc='lower right', frameon=False, fontsize=14)
    fig.tight_layout()
    fig.savefig(OUT / f'{P2}beam_count.png', dpi=130)
    plt.close(fig)


def fig_pose_graph(rows, spacing=0.5, revisit_m=0.4):
    """Illustration of a pose graph from the real SLAM path: a node every 0.5 m, chain edges, and
    links where the path comes back within 0.4 m of an older node (where loop closure can act).
    These are geometric revisits, not slam_toolbox's own loop-closure list."""
    k0, k1 = moving_span(rows)
    sl = np.array([r[2][:2] for r in rows[k0:k1 + 1]])
    nodes, acc = [sl[0]], 0.0
    for a, b in zip(sl[:-1], sl[1:]):
        acc += np.hypot(*(b - a))
        if acc >= spacing:
            nodes.append(b); acc = 0.0
    nodes = np.array(nodes)
    loops = [(i, j) for j in range(len(nodes)) for i in range(j - 8)
             if np.hypot(*(nodes[j] - nodes[i])) < revisit_m]
    print(f'pose graph: {len(nodes)} nodes, {len(loops)} revisit links')
    img, ext = room_map()
    fig, ax = plt.subplots(figsize=(13, 8))
    ax.imshow(img, cmap='gray', vmin=0, vmax=255, extent=ext, alpha=0.3)
    for i, j in loops:
        ax.plot(*zip(nodes[i], nodes[j]), color=ORANGE, lw=3, zorder=4)
    ax.plot(nodes[:, 0], nodes[:, 1], color=MUTED, lw=1.5, zorder=3)
    ax.scatter(nodes[:, 0], nodes[:, 1], s=40, color=BLUE, edgecolor=BG, zorder=5)
    lo, hi = nodes.min(axis=0) - 0.8, nodes.max(axis=0) + 0.8
    ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1])
    ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.scatter([], [], s=60, color=BLUE, label='pose (node), every 0.5 m')
    ax.plot([], [], color=MUTED, lw=2, label='odometry link')
    ax.plot([], [], color=ORANGE, lw=3, label='revisit: loop closure can correct here')
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.01), ncol=3, frameon=False, fontsize=15)
    fig.tight_layout()
    fig.savefig(OUT / f'{P2}pose_graph.png', dpi=130)
    plt.close(fig)


def fig_safety_zones():
    """Top-down safety geometry from drivers.yaml (motor_node) and nav2_params.yaml (collision monitor)."""
    from matplotlib.patches import Circle, Wedge, Polygon
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.add_patch(Circle((0, 0), 0.25, fill=False, ls='--', lw=1.5, ec=MUTED))
    ax.add_patch(Wedge((0.02, 0), 0.20, -35, 35, color=ORANGE, alpha=0.35, lw=0))
    ax.add_patch(Polygon([[0, 0], [0.20, 0.14], [0.20, -0.14]], closed=True, fill=False, ec=BLUE, lw=2.5))
    ax.add_patch(Circle((0, 0), 0.12, fill=False, ec=INK, lw=3))
    ax.annotate('', xy=(0.10, 0), xytext=(-0.02, 0), arrowprops=dict(arrowstyle='->', color=INK, lw=2.5))
    ax.set_xlim(-0.3, 0.3); ax.set_ylim(-0.28, 0.28); ax.set_aspect('equal'); ax.axis('off')
    ax.plot([], [], color=INK, lw=3, label='robot, 0.12 m')
    ax.plot([], [], color=ORANGE, lw=8, alpha=0.5, label='our lidar stop, 0.20 m')
    ax.plot([], [], color=BLUE, lw=2.5, label='Nav2 stop zone')
    ax.plot([], [], color=MUTED, lw=1.5, ls='--', label='0.25 m inflation')
    ax.legend(loc='center left', bbox_to_anchor=(1.0, 0.5), frameon=False, fontsize=16)
    fig.tight_layout()
    fig.savefig(OUT / f'{P2}safety_zones.png', dpi=130, bbox_inches='tight', pad_inches=0.3)
    plt.close(fig)


def fig_goal_on_map(start=(-1.35, -0.29), goal=(-2.67, 0.42), inflate_m=0.25):
    """The goal that succeeded (bt_navigator log 2026-11-10, launch 7359), with Nav2's 0.25 m keep-out shaded."""
    from scipy.ndimage import distance_transform_edt
    img, ext = room_map()
    res = (ext[1] - ext[0]) / img.shape[1]
    keep_out = (distance_transform_edt(img > 100) * res < inflate_m) & (img > 100)
    fig, ax = plt.subplots(figsize=(12, 7.5))
    ax.imshow(img, cmap='gray', vmin=0, vmax=255, extent=ext, alpha=0.4)
    ax.imshow(np.ma.masked_where(~keep_out, keep_out), cmap='Oranges', vmin=0, vmax=2.5, extent=ext, alpha=0.5)
    ax.plot(*zip(start, goal), color=BLUE, lw=2.5, ls='--', label='straight line (driven path not recorded)')
    ax.scatter(*start, s=220, color=INK, zorder=5)
    ax.scatter(*goal, s=320, color=BLUE, marker='*', zorder=5)
    ax.annotate('home mark', start, xytext=(14, -22), textcoords='offset points', fontsize=16)
    ax.annotate('goal', goal, xytext=(14, 8), textcoords='offset points', fontsize=16, color=BLUE)
    d = math.hypot(goal[0] - start[0], goal[1] - start[1])
    ax.text(0.02, 0.97, f'{d:.1f} m, "Goal succeeded" in 93 s', transform=ax.transAxes, va='top', fontsize=17, color=INK)
    cx, cy = (start[0] + goal[0]) / 2, (start[1] + goal[1]) / 2
    ax.set_xlim(cx - 3.2, cx + 3.2); ax.set_ylim(cy - 2.0, cy + 2.0)
    ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.plot([], [], color=ORANGE, lw=8, alpha=0.5, label='within 0.25 m of an obstacle (planner avoids)')
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.01), ncol=2, frameon=False, fontsize=15)
    fig.tight_layout()
    fig.savefig(OUT / f'{P2}goal_on_map.png', dpi=130)
    plt.close(fig)



def fig_dataflow():
    """Detailed ROS 2 data flow in the mermaid pipeline's style, three rows on a 16:9 canvas, every link drawn.
    Main flow grey; /scan (teal) and the EKF's odometry (purple) run as buses in the gaps between rows.
    Row 3 reads right to left so the controller drops straight into the smoother."""
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    TEAL, PURPLE = '#1D9E75', '#7F77DD'
    sty = {'ours': ('#fde8d2', ORANGE, '-'), 'pkg': ('#e3eef8', BLUE, '-'), 'hw': ('#eceef1', MUTED, '-'),
           'topic': (BG, '#9aa0a8', '--')}
    with plt.rc_context({'font.family': 'Arial'}):
        fig, ax = plt.subplots(figsize=(16, 8.6))
        ax.set_xlim(0, 16); ax.set_ylim(0, 8.6); ax.axis('off')

        def box(x, y, text, kind, w=1.9, h=0.8):
            fc, ec, ls = sty[kind]
            pill = kind == 'topic'
            ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                         boxstyle=f'round,pad=0,rounding_size={min(h / 2, 0.26) if pill else 0.04}',
                         fc=fc, ec=ec, lw=1.4 if pill else 1.8, ls=ls, zorder=3))
            ax.text(x, y, text, ha='center', va='center', fontsize=13 if pill else 14,
                    color=MUTED if pill else INK, zorder=4)
            return dict(x=x, y=y, l=x - w / 2, r=x + w / 2, t=y + h / 2, b=y - h / 2)

        def path(pts, color=MUTED, lw=1.4, label=None, lab_at=0, lab_off=(0, 0.1)):
            for p0, p1 in zip(pts[:-2], pts[1:-1]):
                ax.plot(*zip(p0, p1), color=color, lw=lw, zorder=1, solid_capstyle='round')
            ax.add_patch(FancyArrowPatch(pts[-2], pts[-1], arrowstyle='-|>', mutation_scale=14, lw=lw, color=color, zorder=2))
            if label:
                (x0, y0), (x1, y1) = pts[lab_at], pts[lab_at + 1]
                ax.text((x0 + x1) / 2 + lab_off[0], (y0 + y1) / 2 + lab_off[1], label, ha='center', va='bottom',
                        fontsize=12, color=color if color != MUTED else INK, bbox=dict(fc=BG, ec='none', pad=1), zorder=5)

        def right(a, b, label=None):
            path([(a['r'], a['y']), (b['l'], b['y'])], label=label)

        def left(a, b, label=None):
            path([(a['l'], a['y']), (b['r'], b['y'])], label=label)

        def row_title(y, text):
            ax.text(0.55, y, text, fontsize=13, color=MUTED, va='center')

        # row 1
        row_title(8.3, '1 · sense + odometry')
        mpu = box(1.0, 7.45, 'MPU6050', 'hw', w=1.5); imun = box(3.0, 7.45, 'imu_node', 'ours', w=1.6)
        imut = box(5.2, 7.45, '/imu/data · 100 Hz', 'topic', w=2.1, h=0.62)
        lid = box(1.0, 6.2, 'RPLidar A1M8', 'hw', w=1.5); rpl = box(3.0, 6.2, 'rplidar_ros', 'pkg', w=1.6)
        scan = box(5.2, 6.2, '/scan · 7 Hz', 'topic', w=1.7, h=0.62)
        rf2o = box(7.6, 6.2, 'rf2o\nlidar odometry', 'pkg'); rel = box(9.85, 6.2, 'covariance relay', 'ours', w=1.95)
        ekf = box(12.3, 6.8, 'EKF\nrobot_localization', 'pkg', w=2.1)
        odo = box(14.75, 6.8, '/odometry/filtered\n+ TF odom → base', 'topic', w=2.2, h=0.95)
        right(mpu, imun, 'I2C'); right(lid, rpl, 'USB'); right(imun, imut); right(rpl, scan)
        right(scan, rf2o); right(rf2o, rel)
        path([(rel['r'], rel['y']), (ekf['l'], ekf['y'] - 0.2)]); path([(imut['r'], imut['y']), (ekf['l'], ekf['y'] + 0.2)])
        right(ekf, odo)

        # row 2
        row_title(4.35, '2 · SLAM + planning')
        smap = box(1.15, 3.1, 'saved map', 'hw', w=1.5, h=0.6)
        slam = box(3.9, 3.1, 'slam_toolbox\nlocalisation', 'pkg', w=2.0)
        mapt = box(6.35, 3.1, '/map\n+ TF map → odom', 'topic', w=1.95, h=0.95)
        cost = box(9.05, 3.1, 'costmaps\nglobal + local', 'pkg')
        plan = box(11.3, 3.1, 'planner', 'pkg', w=1.5); goal = box(11.3, 4.15, 'goal', 'topic', w=1.1, h=0.5)
        ctrl = box(13.45, 3.1, 'RPP controller', 'pkg', w=1.9)
        right(smap, slam); right(slam, mapt); right(mapt, cost); right(cost, plan); right(plan, ctrl)
        path([(goal['x'], goal['b']), (plan['x'], plan['t'])])

        # row 3, right to left
        row_title(2.1, '3 · control + safety  (right to left)')
        smo = box(13.45, 0.8, 'velocity smoother', 'pkg', w=2.0)
        cm = box(10.85, 0.8, 'collision monitor', 'pkg', w=2.0)
        cmd = box(8.5, 0.8, '/cmd_vel', 'topic', w=1.4, h=0.6)
        mot = box(6.05, 0.8, 'motor_node\nwatchdog · lidar stop', 'ours', w=2.3)
        whl = box(2.85, 0.8, '4 DC motors, 2 ch', 'hw', w=1.7)
        path([(ctrl['x'], ctrl['b']), (smo['x'], smo['t'])], label='/cmd_vel_nav', lab_off=(0.75, -0.1))
        left(smo, cm); left(cm, cmd); left(cmd, mot); left(mot, whl, 'PWM')

        # /scan bus (teal): down the left edge, then under row 2; reaches the costmaps from below
        yb, xl, yb3 = 5.1, 0.3, 1.75
        ax.plot([scan['x'], scan['x']], [scan['b'], yb], color=TEAL, lw=1.8, zorder=1)
        ax.plot([xl, scan['x']], [yb, yb], color=TEAL, lw=1.8, zorder=1)
        path([(slam['x'] - 0.5, yb), (slam['x'] - 0.5, slam['t'])], color=TEAL, lw=1.8)
        ax.plot([xl, xl], [yb, yb3], color=TEAL, lw=1.8, zorder=1)
        ax.plot([xl, cm['x']], [yb3, yb3], color=TEAL, lw=1.8, zorder=1)
        path([(mot['x'], yb3), (mot['x'], mot['t'])], color=TEAL, lw=1.8)
        path([(cm['x'], yb3), (cm['x'], cm['t'])], color=TEAL, lw=1.8)
        path([(cost['x'], yb3), (cost['x'], cost['b'])], color=TEAL, lw=1.8)
        ax.text(2.0, yb + 0.08, '/scan', color=TEAL, fontsize=13, va='bottom', ha='center',
                bbox=dict(fc=BG, ec='none', pad=1), zorder=5)

        # odometry bus (purple), below the /scan bus: to slam_toolbox and down the right edge to the smoother
        yo, xr = 4.75, 15.35
        ax.plot([odo['x'], odo['x']], [odo['b'], yo], color=PURPLE, lw=1.8, zorder=1)
        ax.plot([slam['x'] + 0.5, xr], [yo, yo], color=PURPLE, lw=1.8, zorder=1)
        path([(slam['x'] + 0.5, yo), (slam['x'] + 0.5, slam['t'])], color=PURPLE, lw=1.8)
        ax.plot([xr, xr], [yo, smo['y']], color=PURPLE, lw=1.8, zorder=1)
        path([(xr, smo['y']), (smo['r'], smo['y'])], color=PURPLE, lw=1.8)
        ax.text(8.0, yo + 0.08, 'odometry (EKF)', color=PURPLE, fontsize=13, va='bottom', ha='center',
                bbox=dict(fc=BG, ec='none', pad=1), zorder=5)

        # legend
        items = (('ours', 'our code'), ('pkg', 'ROS 2 package'), ('hw', 'hardware / file'), ('topic', 'topic'))
        for k, (kind, lab) in enumerate(items):
            fc, ec, ls = sty[kind]
            x0 = 6.2 + k * 1.75
            ax.add_patch(FancyBboxPatch((x0, 8.2), 0.32, 0.22, boxstyle='round,pad=0,rounding_size=0.03',
                                        fc=fc, ec=ec, ls=ls, lw=1.4))
            ax.text(x0 + 0.42, 8.31, lab, va='center', fontsize=12, color=INK)
        for k, (c, lab) in enumerate(((TEAL, '/scan bus'), (PURPLE, 'odometry bus'))):
            x0 = 13.2 + k * 1.45
            ax.plot([x0, x0 + 0.35], [8.31, 8.31], color=c, lw=2.2)
            ax.text(x0 + 0.42, 8.31, lab, va='center', fontsize=12, color=INK)
        fig.tight_layout(pad=0.15)
        fig.savefig(OUT / f'{P2}pipeline_detailed.png', dpi=130)
        plt.close(fig)


# ---------- 2026-11-11 v5 additions (teach-first deck) ----------
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle  # noqa: E402

LIGHT_BLUE, LIGHT_ORANGE, LIGHT_GREY = '#e3eef8', '#fde8d2', '#eceef1'


def _box(ax, x, y, w, h, text, fc, ec, fs=15):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.01,rounding_size=0.02', fc=fc, ec=ec, lw=2))
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center', fontsize=fs, color=INK)


def _arrow(ax, a, b, text='', off=(0, 0.03)):
    ax.annotate('', b, a, arrowprops=dict(arrowstyle='-|>', color=MUTED, lw=2, mutation_scale=20))
    if text:
        ax.text((a[0] + b[0]) / 2 + off[0], (a[1] + b[1]) / 2 + off[1], text, ha='center', va='bottom', fontsize=13, color=MUTED)


def _blank(ax, xlim=(0, 1), ylim=(0, 1)):
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.axis('off')


def fig_lidar_plane():
    """1.2: side view of the one scan plane (lidar 12 cm up, URDF). A sketch, not data."""
    fig, ax = plt.subplots(figsize=(12, 6))
    z = 0.12
    ax.plot([-0.2, 4.4], [0, 0], color=INK, lw=2)
    ax.add_patch(Rectangle((0, 0.03), 0.26, 0.07, fc=LIGHT_GREY, ec=INK, lw=2))
    ax.add_patch(Rectangle((0.10, 0.10), 0.07, 0.04, fc=INK, ec=INK))
    ax.plot([0.17, 4.2], [z, z], color=BLUE, lw=2, ls='--')
    ax.text(0.3, z + 0.04, 'scan plane, 12 cm', color=BLUE, fontsize=22)
    for x in (1.0, 1.35):  # chair
        ax.add_patch(Rectangle((x, 0), 0.03, 0.45, fc=MUTED, ec=MUTED))
    ax.add_patch(Rectangle((0.98, 0.45), 0.42, 0.04, fc=MUTED, ec=MUTED))
    ax.add_patch(Rectangle((1.36, 0.45), 0.03, 0.40, fc=MUTED, ec=MUTED))
    for x in (2.0, 2.75):  # table
        ax.add_patch(Rectangle((x, 0), 0.04, 0.72, fc=MUTED, ec=MUTED))
    ax.add_patch(Rectangle((1.9, 0.72), 1.0, 0.05, fc=MUTED, ec=MUTED))
    ax.add_patch(Rectangle((3.35, 0), 0.03, 0.95, fc='#cfe3f2', ec='#8fb8d8', lw=1.5))
    ax.add_patch(Rectangle((4.2, 0), 0.08, 1.0, fc=INK, ec=INK))
    ax.scatter([1.0, 2.0, 4.2], [z] * 3, s=120, color=BLUE, zorder=5)
    ax.scatter([3.365], [z], s=180, color=ORANGE, marker='X', zorder=5)
    for x, lab in ((1.2, 'chair'), (2.4, 'table'), (3.365, 'glass'), (4.24, 'wall')):
        ax.text(x, -0.09, lab, ha='center', fontsize=22, color=MUTED)
    ax.text(2.4, 0.83, 'missed', ha='center', fontsize=22, color=ORANGE)
    ax.text(3.365, 1.02, 'no echo', ha='center', fontsize=22, color=ORANGE)
    _blank(ax, (-0.25, 4.45), (-0.2, 1.12))  # ponytail: not equal-aspect, a sketch stretched to fill a 2:1 slide window
    fig.tight_layout()
    fig.savefig(OUT / f'{P2}lidar_plane.png', dpi=130, transparent=True)
    plt.close(fig)


def fig_fusion_flow():
    """1.3: what feeds the EKF (ekf.yaml: rf2o vx + vyaw, IMU vyaw; 20 Hz)."""
    fig, ax = plt.subplots(figsize=(14, 5))
    _blank(ax)
    h = 0.24
    _box(ax, 0.02, 0.61, 0.16, h, 'Lidar\n7 Hz', LIGHT_GREY, MUTED, fs=18)
    _box(ax, 0.30, 0.61, 0.16, h, 'rf2o', LIGHT_BLUE, BLUE, fs=18)
    _box(ax, 0.02, 0.15, 0.16, h, 'Gyro\n100 Hz', LIGHT_ORANGE, ORANGE, fs=18)
    _box(ax, 0.60, 0.15, 0.16, 0.70, 'EKF\n20 Hz', LIGHT_BLUE, BLUE, fs=20)
    _arrow(ax, (0.18, 0.73), (0.30, 0.73), 'scans')
    _arrow(ax, (0.46, 0.73), (0.60, 0.73), 'v, ω')
    _arrow(ax, (0.18, 0.27), (0.60, 0.27), 'ω')
    _arrow(ax, (0.76, 0.50), (0.88, 0.50))
    ax.text(0.94, 0.50, 'pose', ha='center', va='center', fontsize=20, color=INK)
    fig.tight_layout()
    fig.savefig(OUT / f'{P2}fusion_flow.png', dpi=130)
    plt.close(fig)


def fig_motor_drive():
    """1.4: H-bridge (one channel) and the four-wheel base driven as two sides."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 6))
    _blank(a1, (0, 1), (0, 1))
    for y, s in ((0.88, '+'), (0.12, '−')):
        a1.plot([0.15, 0.85], [y, y], color=INK, lw=2); a1.text(0.08, y, s, ha='center', va='center', fontsize=22)
    for x in (0.25, 0.75):
        a1.plot([x, x], [0.88, 0.12], color=GREY, lw=2)
    for x, y, on in ((0.25, 0.70, 1), (0.75, 0.70, 0), (0.25, 0.30, 0), (0.75, 0.30, 1)):
        a1.add_patch(Rectangle((x - 0.05, y - 0.06), 0.10, 0.12, fc=ORANGE if on else BG, ec=INK, lw=2))
    a1.plot([0.25, 0.42], [0.5, 0.5], color=INK, lw=2); a1.plot([0.58, 0.75], [0.5, 0.5], color=INK, lw=2)
    a1.add_patch(Circle((0.5, 0.5), 0.08, fc=BG, ec=INK, lw=2)); a1.text(0.5, 0.5, 'M', ha='center', va='center', fontsize=20)
    a1.text(0.5, 0.0, 'PWM duty → speed', ha='center', va='center', fontsize=18)
    _blank(a2, (-0.45, 0.45), (-0.38, 0.42))
    a2.add_patch(Rectangle((-0.16, -0.2), 0.32, 0.4, fc=LIGHT_GREY, ec=INK, lw=2))
    for sx, col, name in ((-1, BLUE, 'left'), (1, ORANGE, 'right')):
        for sy in (-1, 1):
            a2.add_patch(Rectangle((sx * 0.2 - 0.04, sy * 0.13 - 0.07), 0.08, 0.14, fc=col, ec=INK))
        a2.text(sx * 0.33, 0.0, name, ha='center', va='center', fontsize=18, color=col)
    a2.annotate('', (0, 0.34), (0, 0.10), arrowprops=dict(arrowstyle='-|>', color=INK, lw=2.5))
    a2.text(0, -0.31, 'v ∓ ω·b/2', ha='center', va='center', fontsize=18)
    fig.tight_layout()
    fig.savefig(OUT / f'{P2}motor_drive.png', dpi=130)
    plt.close(fig)


def _grid(img, ext):
    from scipy.ndimage import distance_transform_edt
    res = (ext[1] - ext[0]) / img.shape[1]
    occ = img < 100
    return res, distance_transform_edt(~occ) * res


def _px(p, ext, res, shape):
    return shape[0] - 1 - int(math.floor((p[1] - ext[2]) / res)), int(math.floor((p[0] - ext[0]) / res))


def _plan(img, ext, start, goal, robot_r=0.12, inflate=0.25):
    """Dijkstra on an inflated grid, 8-connected: an offline stand-in for NavFn, for illustration only."""
    import heapq
    res, d = _grid(img, ext)
    cost = np.where(d < inflate, 1 + 20 * (inflate - d) / (inflate - robot_r), 1.0)
    cost[(d < robot_r) | (np.abs(img.astype(int) - 205) < 3)] = np.inf
    s, g = _px(start, ext, res, img.shape), _px(goal, ext, res, img.shape)
    assert np.isfinite(cost[s]) and np.isfinite(cost[g]), (cost[s], cost[g])
    dist = {s: 0.0}; prev = {}; q = [(0.0, s)]
    while q:
        c, u = heapq.heappop(q)
        if u == g: break
        if c > dist[u]: continue
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                v = (u[0] + dr, u[1] + dc)
                if (dr or dc) and 0 <= v[0] < img.shape[0] and 0 <= v[1] < img.shape[1] and np.isfinite(cost[v]):
                    nc = c + cost[v] * math.hypot(dr, dc)
                    if nc < dist.get(v, np.inf):
                        dist[v] = nc; prev[v] = u; heapq.heappush(q, (nc, v))
    path = [g]
    while path[-1] != s:
        path.append(prev[path[-1]])
    rc = np.array(path[::-1], dtype=float)
    return np.c_[ext[0] + (rc[:, 1] + 0.5) * res, ext[2] + (img.shape[0] - 1 - rc[:, 0] + 0.5) * res], d


def fig_nav2_concept(start=(-1.3, -0.3), goal=(2.0, -1.0), look=0.3):
    """1.5: costmap (0.25 m inflation, nav2_params.yaml), a planned path and the RPP lookahead point. Path computed offline."""
    img, ext = room_map()
    path, d = _plan(img, ext, start, goal)
    infl = (d < 0.25) & (img > 100)
    fig, ax = plt.subplots(figsize=(14, 9))
    ax.imshow(img, cmap='gray', vmin=0, vmax=255, extent=ext, alpha=0.4)
    ax.imshow(np.ma.masked_where(~infl, infl), cmap='Oranges', vmin=0, vmax=2.5, extent=ext, alpha=0.5)
    ax.plot(path[:, 0], path[:, 1], color=BLUE, lw=3, label='planned path')
    arc = np.r_[0, np.cumsum(np.hypot(*np.diff(path, axis=0).T))]
    c = path[np.searchsorted(arc, look)]
    ax.add_patch(Circle(start, 0.12, fc=INK, ec=INK, zorder=5))
    ax.plot(*zip(start, c), color=ORANGE, lw=2.5, zorder=6)
    ax.scatter(*c, s=140, color=ORANGE, zorder=7)
    ax.annotate('lookahead', c, xytext=(40, -60), textcoords='offset points',
                fontsize=15, color=ORANGE, arrowprops=dict(arrowstyle='-', color=ORANGE))
    ax.scatter(*goal, s=380, color=BLUE, marker='*', zorder=5)
    ax.annotate('goal', goal, xytext=(12, 10), textcoords='offset points', fontsize=16, color=BLUE)
    ax.annotate('robot', start, xytext=(-30, -32), textcoords='offset points', fontsize=16)
    lo = np.minimum(start, goal) - 1.0; hi = np.maximum(start, goal) + 1.0
    ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1])
    ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.plot([], [], color=ORANGE, lw=8, alpha=0.5, label='0.25 m inflation')
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.01), ncol=2, frameon=False, fontsize=15)
    fig.tight_layout()
    fig.savefig(OUT / f'{P2}nav2_concept.png', dpi=130)
    plt.close(fig)
    print(f'nav2 concept: path {arc[-1]:.2f} m, lookahead ({c[0]:.2f}, {c[1]:.2f})')


def fig_home_move(old=(0.0, 0.0), new=(-1.3, -0.3)):
    """3.3: clearance to the nearest obstacle at the old and new home (distance transform; notes 2026-11-10: 0.21 and 0.67 m)."""
    img, ext = room_map()
    res, d = _grid(img, ext)
    cl = [d[_px(p, ext, res, img.shape)] for p in (old, new)]
    print(f'home clearance: old {cl[0]:.2f} m, new {cl[1]:.2f} m (notes 0.21, 0.67)')
    assert abs(cl[0] - 0.21) < 0.03 and abs(cl[1] - 0.67) < 0.03, cl
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.imshow(img, cmap='gray', vmin=0, vmax=255, extent=ext, alpha=0.45)
    for p, r, col, lab, up in ((old, cl[0], ORANGE, f'old home: {cl[0]:.2f} m', True),
                               (new, cl[1], BLUE, f'new home: {cl[1]:.2f} m', False)):
        ax.add_patch(Circle(p, r, fc=col, ec=col, alpha=0.25, lw=2))
        ax.add_patch(Circle(p, r, fc='none', ec=col, lw=2.5))
        ax.scatter(*p, s=160, color=col, zorder=5)
        ax.annotate(lab, p, xytext=(0, 45 if up else -r / res * 1.2 - 40), textcoords='offset points', ha='center', fontsize=15, color=col,
                    bbox=dict(fc=BG, ec='none', alpha=0.85))
    ax.annotate('', new, old, arrowprops=dict(arrowstyle='-|>', color=INK, lw=2, ls='--'))
    ax.set_xlim(-2.6, 1.2); ax.set_ylim(-1.7, 1.0)
    ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / f'{P2}home_move.png', dpi=130)
    plt.close(fig)


OI8_STEPS = [  # report/slam_challenges.md S7 table (test_log 2026-11-01 to 11-03): date, test, result, conclusion, kind
    ('1 Nov', 'Push 1.00 m by hand', 'odometry 0.24 m (24 %)', 'odometry broken?', 'lead'),
    ('1 Nov', 'Repeat: 1.20 m, new spot', '0.29 m (24 %)', 'same ratio: a scale bug?', 'lead'),
    ('1 Nov', 'Compare scan format, 5 recordings', 'good 1045 beams, bad 720', 'suspect: beam count', 'lead'),
    ('2 Nov', 'Replay the bad recording, 1x and 0.25x', '0.291 m and 0.289 m', 'ruled out: CPU, timing', 'out'),
    ('3 Nov', 'Live pushes, nobody near, beam fix on and off', '101 % and 96 %', 'ruled out: beam count', 'out'),
    ('3 Nov', 'Count scan points behind the robot', '127-152 (bad) vs 16-18 (good)', 'cause: a person walking behind', 'cause'),
    ('3 Nov', 'Replay with returns < 0.6 m removed', '99.5 % of the push', 'fix works (offline)', 'fix'),
]


def fig_oi8_ladder():
    """3.4: suspects in the order tested (slam_challenges.md S7 table, test_log 2026-11-01 to 11-03)."""
    steps = [('beam count', 'live push: 101 %, 96 %', 'out'), ('CPU, timing', 'replay: same 0.29 m', 'out'),
             ('person behind', '127-152 points\nbehind vs 16-18', 'cause'), ('range cut', 'ignore < 0.6 m\n→ 99.5 % (offline)', 'fix')]
    col = {'out': (LIGHT_GREY, MUTED, INK), 'cause': (ORANGE, ORANGE, BG), 'fix': (BLUE, BLUE, BG)}
    fig, ax = plt.subplots(figsize=(16, 5))
    _blank(ax)
    ax.text(0.0, 0.9, '1 m push reads 24 %', fontsize=20, color=INK, va='center')
    w, gap = 0.19, 0.067
    tag = {'out': 'ruled out', 'cause': 'cause', 'fix': 'fix'}
    for k, (name, ev, kind) in enumerate(steps):
        x = 0.012 + k * (w + gap)
        fc, ec, tc = col[kind]
        _box(ax, x, 0.42, w, 0.24, name, fc, ec, fs=19)
        ax.texts[-1].set_color(tc)
        ax.text(x + w / 2, 0.24, ev, ha='center', va='top', fontsize=15, color=MUTED)
        ax.text(x + w / 2, 0.72, tag[kind], ha='center', va='bottom', fontsize=15, color=ec)
        if k < len(steps) - 1:
            _arrow(ax, (x + w, 0.54), (x + w + gap, 0.54))
    fig.tight_layout()
    fig.savefig(OUT / f'{P2}oi8_ladder.png', dpi=130)
    plt.close(fig)






def fig_map_overlay(rows, lo, hi, min_hits=3):
    """3.3: walls rebuilt from the same scans, placed by SLAM poses (grey) and by odometry-only poses (orange),
    the odometry path moved into the map frame at the first pose as in drift_paths. Doubled orange walls = drift."""
    m0 = compose(rows[0][2], inverse(rows[0][1]))
    gs, go = Grid(lo[0], lo[1], hi[0], hi[1]), Grid(lo[0], lo[1], hi[0], hi[1])
    for r in rows:
        gs.add(place(r[3], r[2]))
        go.add(place(r[3], compose(m0, r[1])))
    fig, ax = plt.subplots(figsize=(14, 8.85))
    for g, col, a in ((gs, INK, 0.9), (go, ORANGE, 0.75)):
        m = g.h >= min_hits
        rgba = np.zeros(m.shape + (4,)); rgba[m] = matplotlib.colors.to_rgba(col, a)
        ax.imshow(rgba, origin='lower', extent=g.extent(), interpolation='nearest')
    ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_visible(False)
    ax.plot([], [], color=INK, lw=8, label='walls placed by SLAM')
    ax.plot([], [], color=ORANGE, lw=8, label='same scans placed by odometry only')
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.01), ncol=2, frameon=False, fontsize=16)
    fig.tight_layout()
    fig.savefig(OUT / f'{P2}map_overlay.png', dpi=130)
    plt.close(fig)


def figs_v5():
    fig_lidar_plane(); fig_fusion_flow(); fig_motor_drive(); fig_nav2_concept(); fig_home_move()
    fig_oi8_ladder(); fig_timeline(); fig_root_cause()



if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    fig_motor(); fig_bars(); fig_power(); fig_timeline()
    fig_turn(); fig_straights()
    gif_oi8()
    rows, lo, hi = map_bag()
    fig_odom_vs_slam(rows, lo, hi)
    gif_map_build(rows, lo, hi)
    fig_map_overlay(rows, lo, hi); fig_drift_vs_slam(rows); gif_drift_vs_slam(rows); fig_scan_gaps(rows); fig_sweep(); fig_goal_attempts(); fig_wrong_start(); fig_root_cause(); fig_beam_count()
    fig_pose_graph(rows); fig_safety_zones(); fig_goal_on_map(); fig_dataflow()
    figs_v5(); gif_oi8(tall=True)
    for f in sorted(list(OUT.glob(f'{P}*')) + list(OUT.glob(f'{P2}*'))):
        print(f.name, f'{f.stat().st_size / 1e6:.2f} MB')
