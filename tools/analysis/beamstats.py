"""usage: beamstats.py <bag> [t0 t1]
/scan beam-format stats, t0 t1 in s from the first /scan (default whole bag). Per scan: beam count, fraction of
ranges that are inf/nan/0 ("bad"), fraction of adjacent finite pairs with exactly equal range (binning
duplicates), longest run of consecutive bad beams. Prints min/max beam count and medians over the scans."""
import sys, math, statistics as st


def scan_stats(ranges):
    """(bad fraction, duplicate fraction, longest bad run) for one list of ranges. Bad = inf, nan or 0.
    Duplicate fraction = equal adjacent finite non-zero pairs / adjacent finite non-zero pairs."""
    n = len(ranges)
    ok = [math.isfinite(v) and v > 0 for v in ranges]
    run = best = 0
    for g in ok:
        run = 0 if g else run + 1
        best = max(best, run)
    pairs = [(a, b) for a, b, ga, gb in zip(ranges, ranges[1:], ok, ok[1:]) if ga and gb]
    dup = sum(1 for a, b in pairs if a == b) / len(pairs) if pairs else 0.0
    return (n - sum(ok)) / n, dup, best


def summarise(scans):
    """scans: list of range lists. Beam count min/max and medians of the per-scan stats."""
    counts = [len(s) for s in scans]
    per = [scan_stats(s) for s in scans]
    return {'scans': len(scans), 'beams_min': min(counts), 'beams_max': max(counts),
            'bad_med': st.median(p[0] for p in per), 'dup_med': st.median(p[1] for p in per),
            'run_med': st.median(p[2] for p in per), 'run_max': max(p[2] for p in per)}


if __name__ == '__main__':
    import rosbag2_py
    from rclpy.serialization import deserialize_message
    from sensor_msgs.msg import LaserScan
    r = rosbag2_py.SequentialReader()
    r.open(rosbag2_py.StorageOptions(uri=sys.argv[1], storage_id='mcap'), rosbag2_py.ConverterOptions('cdr', 'cdr'))
    S = []
    while r.has_next():
        t, d, ts = r.read_next()
        if t == '/scan': S.append((ts * 1e-9, list(deserialize_message(d, LaserScan).ranges)))
    t0 = S[0][0]
    lo, hi = (float(sys.argv[2]), float(sys.argv[3])) if len(sys.argv) > 3 else (-1, 1e18)
    s = summarise([x for t, x in S if lo <= t - t0 <= hi])
    print('scans %(scans)d beams %(beams_min)d-%(beams_max)d bad(inf/nan/0) median %(bad_med).3f '
          'duplicate-pairs median %(dup_med).3f longest bad run median %(run_med)g max %(run_max)d' % s)
