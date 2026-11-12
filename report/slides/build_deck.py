"""Full CA3 deck on the group's template. Usage: build_deck.py TEMPLATE OUT FIG_DIR SCRIPTS_PY POSTER_JPG"""
import copy, sys
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, PP_PLACEHOLDER
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn

TPL, OUT, FIG, SCRIPTS, POSTER, ROBOT = sys.argv[1:7]
ns = {}; exec(open(SCRIPTS).read(), ns); SCRIPT = ns['S']
INK, MUTED, WHITE = RGBColor(0x11, 0x11, 0x11), RGBColor(0x5E, 0x5E, 0x5E), RGBColor(0xFF, 0xFF, 0xFF)
YEL, BLU, COR, GRN = RGBColor(0xFF, 0xC6, 0x00), RGBColor(0x11, 0x9B, 0xFE), RGBColor(0xFF, 0x6B, 0x4D), RGBColor(0x28, 0xC8, 0x40)
PALE_YEL, STRUCK, FIGBG, LINE = RGBColor(0xFF, 0xF4, 0xCC), RGBColor(0x8A, 0x8A, 0x8A), RGBColor(0xFB, 0xFB, 0xF8), 'E3E1E1'
FONT, LIGHT = 'Lexend', 'Lexend Light'
SECTION = {'o': ('Overview', INK), 'y': ('Background', YEL), 'c': ('Implementation', COR), 'g': ('Results', GRN)}

prs = Presentation(TPL)
orig = list(prs.slides)
find = lambda sl, name: next(x for x in sl.shapes if x.name == name)
CARD, DOTS, PILL = (find(orig[4], 'Google Shape;1961;p37'), find(orig[4], 'Google Shape;1967;p37'), find(orig[4], 'Google Shape;1976;p37'))
BUBBLE = find(orig[1], 'Google Shape;1907;p34')
FOLDERS = {'y': find(orig[2], 'Google Shape;1930;p35'), 'c': find(orig[2], 'Google Shape;1938;p35'), 'g': find(orig[2], 'Google Shape;1922;p35')}
LAYOUT = orig[4].slide_layout
_id = [5000]

# The play triangle in every layout's top bar reads as a stray icon: remove it once, at the layout.
for lay in prs.slide_layouts:
    for sh in list(lay.shapes):
        if sh.left is not None and sh.left < Inches(0.3) and sh.top < Inches(0.2) and sh.width < Inches(0.25) and 'triangle' in sh._element.xml:
            sh._element.getparent().remove(sh._element)


# ---------- helpers ----------
def cap(s):
    """Sentence case for labels; leaves names that are lowercase by design (rf2o) alone."""
    return s if not s or not s[0].isalpha() or s.startswith('rf2o') else s[0].upper() + s[1:]


def spans(t, o):
    """Split 'plain **bold** plain' into runs, bold where marked."""
    out = []
    for i, part in enumerate(t.split('**')):
        if part:
            out.append((part, dict(o, bold=True) if i % 2 else o))
    return out

def clone(src, slide, x=None, y=None, w=None, h=None):
    el = copy.deepcopy(src._element)
    for c in el.iter(qn('p:cNvPr')):
        _id[0] += 1; c.set('id', str(_id[0]))
    slide.shapes._spTree.append(el)
    sh = slide.shapes[-1]
    if x is not None:
        sh.left, sh.top = Inches(x), Inches(y)
    if w is not None:
        sh.width, sh.height = Inches(w), Inches(h)
    return sh


def text(slide, x, y, w, h, paras, size=12, color=INK, light=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, space=0):
    """paras: str, or list of paragraphs; each paragraph a str or a list of (text, options) runs."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    for i, para in enumerate(paras if isinstance(paras, list) else [paras]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align; p.space_after = Pt(space)
        for t, o in [sp for seg in (para if isinstance(para, list) else [(para, {})]) for sp in spans(*seg)]:
            r = p.add_run(); r.text = t; f = r.font
            f.name = LIGHT if o.get('light', light) else FONT
            f.size = Pt(o.get('size', size)); f.bold = o.get('bold', False); f.color.rgb = o.get('color', color)
            if o.get('strike'):
                f._rPr.set('strike', 'sngStrike')
    return tb


def card(slide, x, y, w, h, fill=None, dots=False):
    c = clone(CARD, slide, x, y, w, h)
    if fill is not None:
        c.fill.solid(); c.fill.fore_color.rgb = fill
    if dots:
        clone(DOTS, slide, x + 0.08, y + 0.11)
    return c


def fit(path, w, h):
    iw, ih = Image.open(path).size
    s = min(w / iw, h / ih)
    return iw * s, ih * s


def window(slide, name, x, y, w, h, bg=FIGBG):
    """Window card holding one figure, scaled to fit and centred under the dots."""
    card(slide, x, y, w, h, fill=bg)
    path = f'{FIG}/{name}'
    ix, iy, iw, ih = x + 0.12, y + 0.12, w - 0.24, h - 0.24
    pw, ph = fit(path, iw, ih)
    return slide.shapes.add_picture(path, Inches(ix + (iw - pw) / 2), Inches(iy + (ih - ph) / 2), Inches(pw), Inches(ph))


def photo(slide, path, x, y, w, h, frame=False):
    """Photo cropped to fill (x, y, w, h) exactly; frame=True puts it on a white panel first."""
    if frame:
        card(slide, x, y, w, h, fill=WHITE)
        x, y, w, h = x + 0.1, y + 0.1, w - 0.2, h - 0.2
    iw, ih = Image.open(path).size
    pic = slide.shapes.add_picture(path, Inches(x), Inches(y), Inches(w), Inches(h))
    want, have = w / h, iw / ih
    if have > want:
        c = (1 - want / have) / 2; pic.crop_left = pic.crop_right = c
    else:
        c = (1 - have / want) / 2; pic.crop_top = pic.crop_bottom = c
    return pic


def callout(slide, pic, size, px, py, lx, ly, label, col):
    """Dot on a photo pixel (px, py), a leader line, and a coloured label pill at (lx, ly) inches."""
    from pptx.enum.shapes import MSO_CONNECTOR
    iw, ih = size
    cl, cr, ct, cb = pic.crop_left, pic.crop_right, pic.crop_top, pic.crop_bottom
    vx = (px / iw - cl) / (1 - cl - cr); vy = (py / ih - ct) / (1 - ct - cb)
    ax = pic.left / 914400 + vx * pic.width / 914400; ay = pic.top / 914400 + vy * pic.height / 914400
    w = 0.16 + 0.085 * len(label)
    ln = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(ax), Inches(ay), Inches(lx + w / 2), Inches(ly + 0.17))
    ln.line.color.rgb = INK; ln.line.width = Pt(1.5)
    d = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(ax - 0.07), Inches(ay - 0.07), Inches(0.14), Inches(0.14))
    d.fill.solid(); d.fill.fore_color.rgb = col; d.line.color.rgb = INK; d.line.width = Pt(1.25)
    pill(slide, lx, ly, w, 0.34, label, col, WHITE if col in (COR, BLU, GRN) else INK, size=11)


def credit(slide, line):
    text(slide, 0.45, 5.08, 7.2, 0.16, line, size=7, color=MUTED, light=True)


def pill(slide, x, y, w, h, label, fill, fg=INK, size=10):
    p = clone(PILL, slide, x, y, w, h)
    p.fill.solid(); p.fill.fore_color.rgb = fill
    tf = p.text_frame
    for para in list(tf.paragraphs)[1:]:
        para._p.getparent().remove(para._p)
    par = tf.paragraphs[0]
    for r in list(par.runs)[1:]:
        r._r.getparent().remove(r._r)
    r = par.runs[0]; r.text = cap(label); r.font.size = Pt(size); r.font.color.rgb = fg; r.font.name = FONT
    tf.margin_top = tf.margin_bottom = 0; tf.word_wrap = False; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    return p


def stat(slide, x, y, w, h, big, label, color=INK, fill=None, big_size=28):
    card(slide, x, y, w, h, fill=fill)
    fg = WHITE if fill in (COR, BLU, GRN) else color
    text(slide, x + 0.2, y + 0.08, w - 0.4, h - 0.16,
         [[(big, {'size': big_size, 'light': True, 'color': fg})], [(cap(label), {'size': 12, 'light': True, 'color': WHITE if fill in (COR, BLU, GRN) else MUTED})]], space=2, anchor=MSO_ANCHOR.MIDDLE)


def point(slide, x, y, w, h, head, body, label=None, fill=None, strike=False, hs=15, bs=12, icon=None, ring=YEL):
    """Small card: optional icon in a coloured circle, optional caps label, a heading, one short line.
    Text is centred vertically so short cards do not leave a gap at the bottom."""
    card(slide, x, y, w, h, fill=fill)
    if icon:
        d = 0.5
        o = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x + 0.2), Inches(y + (h - d) / 2), Inches(d), Inches(d))
        o.fill.solid(); o.fill.fore_color.rgb = ring; o.line.fill.background()
        st = o._element.find(qn('p:style'))
        if st is not None:
            o._element.remove(st)
        tone = 'ink' if ring == YEL else 'white'
        slide.shapes.add_picture(f'{FIG}/icons/{icon}_{tone}.png', Inches(x + 0.2 + 0.11), Inches(y + (h - d) / 2 + 0.11), Inches(0.28), Inches(0.28))
        x, w = x + 0.62, w - 0.62
    on = fill in (COR, BLU, GRN)
    fg, sub = (WHITE, WHITE) if on else (INK, MUTED)
    paras = []
    if label:
        paras.append([(label, {'size': 9, 'color': sub})])
    paras.append([(head, {'size': hs, 'color': STRUCK if strike else fg, 'strike': strike, 'bold': not strike})])
    if body:
        paras.append([(cap(body), {'size': bs, 'color': sub, 'light': True})])
    text(slide, x + 0.2, y + 0.08, w - 0.4, h - 0.16, paras, space=2, anchor=MSO_ANCHOR.MIDDLE)


def take(slide, x, y, w, h, line):
    """Yellow speech bubble for the one-line 'Our take': a rounded callout whose tail points down-left,
    with the text centred in its body (h is the body; the tail hangs below it)."""
    b = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGULAR_CALLOUT, Inches(x), Inches(y), Inches(w), Inches(h))
    b.adjustments[0] = -0.36        # tail tip, as a fraction of width from the centre
    b.adjustments[1] = 0.68         # tail tip, as a fraction of height below the centre
    b.adjustments[2] = 0.45         # corner rounding
    b.fill.solid(); b.fill.fore_color.rgb = YEL; b.line.fill.background()
    st = b._element.find(qn('p:style'))
    if st is not None:
        b._element.remove(st)   # no theme shadow or effects
    tf = b.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.4); tf.margin_top = tf.margin_bottom = Inches(0.05)
    for i, (s_, size) in enumerate([('**OUR TAKE**', 9), (line, 15)]):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = PP_ALIGN.LEFT; para.space_after = Pt(2)
        for seg, o in spans(s_, {}):
            r = para.add_run(); r.text = seg; r.font.size = Pt(size); r.font.name = FONT; r.font.color.rgb = INK; r.font.bold = o.get('bold', False)
            if i == 0:
                r.font._rPr.set('spc', '120')


def content(sec, who, title_text, sub=None):
    """New content slide: title, optional subtitle, bottom caption and section folders."""
    s = prs.slides.add_slide(LAYOUT)
    for ph in list(s.placeholders):
        if ph.placeholder_format.type != PP_PLACEHOLDER.TITLE:
            ph._element.getparent().remove(ph._element)
    ttl = next(ph for ph in s.placeholders if ph.placeholder_format.type == PP_PLACEHOLDER.TITLE)
    ttl.left, ttl.top, ttl.width, ttl.height = Inches(0.45), Inches(0.4), Inches(9.1), Inches(0.62)
    ttl.text = title_text
    tf = ttl.text_frame; tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for r in tf.paragraphs[0].runs:
        r.font.name = LIGHT; r.font.size = Pt(26); r.font.color.rgb = INK
    if sub:
        text(s, 0.45, 0.98, 9.1, 0.3, sub, size=15, color=MUTED, light=True)
    name, _ = SECTION[sec]
    text(s, 0.45, 5.25, 6, 0.2, [[(name, {'size': 9.5}), (f'   ·   {who}', {'size': 9.5, 'color': MUTED, 'light': True})]])
    for k, (key, f) in enumerate(FOLDERS.items()):
        g = clone(f, s, 8.31 + k * 0.36, 5.17, 0.28, 0.2)
        if key != sec:
            for c in list(g._element.iter()):
                if c.tag in (qn('a:schemeClr'), qn('a:srgbClr')):
                    c.append(c.makeelement(qn('a:alpha'), {'val': '28000'}))
    order.append(s)
    return s


def notes(slide, key):
    """Speaker notes as plain paragraphs: line wraps joined, the hand-over line last, no bullets."""
    sc, tr = SCRIPT[key]
    paras = [' '.join(par.split()) for par in sc.split('\n\n')] + ([] if tr == 'None.' else [tr])
    tf = slide.notes_slide.notes_text_frame
    tf.text = paras[0]
    for par in paras[1:]:
        tf.add_paragraph().text = par
    for par in tf.paragraphs:
        pPr = par._p.get_or_add_pPr()
        pPr.set('marL', '0'); pPr.set('indent', '0')
        for b in pPr.findall(qn('a:buChar')) + pPr.findall(qn('a:buAutoNum')) + pPr.findall(qn('a:buNone')):
            pPr.remove(b)
        pPr.insert(0, pPr.makeelement(qn('a:buNone'), {}))
        par.space_after = Pt(8)


def page_numbers():
    for n, s in enumerate(order, 1):
        if s in content_slides:
            text(s, 9.15, 5.25, 0.4, 0.2, f'{n:02d}', size=9.5, color=MUTED, align=PP_ALIGN.RIGHT)


def divider(src):
    order.append(src)
    for ph in src.placeholders:
        ph.left = Inches(4.4); ph.width = Inches(5.0)
        for p in ph.text_frame.paragraphs:
            for r in p.runs:
                r.font.size = Pt(34); r.font.name = LIGHT; r.font.color.rgb = INK


order = []
# ---------- title and aim (the group's own slides) ----------
order.append(orig[0]); notes(orig[0], 'T')
order.append(orig[1]); notes(orig[1], 'A')
for g in orig[1].shapes:                         # drop the window dots from the Aim slide's resources card
    if g.name == 'Google Shape;1910;p34':
        for sp in list(g._element.iter(qn('p:sp'))):
            if 'prst="ellipse"' in __import__('lxml').etree.tostring(sp).decode():
                sp.getparent().remove(sp)
content_slides = []
WEB = f'{FIG}/web'

# ---------- the robot, before any theory ----------
s = content('o', 'Yujie', 'This is the robot we built', 'Off-the-shelf parts on a four-wheel base, **no wheel encoders**')
top = photo(s, f'{FIG}/2026-11-11_robot_top.jpg', 0.45, 1.4, 4.9, 3.68, frame=True)
side = photo(s, f'{WEB}/robot_side_crop.jpg', 5.5, 1.4, 4.05, 3.68, frame=True)
for (px, py), (lx, ly), lab, col in [((800, 410), (3.95, 1.55), 'RPLidar A1M8', YEL), ((545, 470), (0.6, 1.55), 'Raspberry Pi 4B', BLU),
                                     ((772, 604), (3.75, 4.6), 'MPU6050 IMU', GRN), ((330, 415), (0.6, 4.6), 'L298N driver', COR)]:
    callout(s, top, (1280, 960), px, py, lx, ly, lab, col)
for (px, py), (lx, ly), lab, col in [((390, 610), (5.65, 4.6), '4 DC gear motors', COR), ((760, 230), (7.9, 1.55), 'Lidar 12 cm up', YEL)]:
    callout(s, side, (1080, 860), px, py, lx, ly, lab, col)
notes(s, 'R'); content_slides.append(s)


# ---------- 1. Background ----------
divider(orig[3])



s = content('y', 'Yujie', 'Same loop as a road AV, scaled down to one room', 'Odometry alone drifts up to **0.46 m** over one lap. **SLAM holds it.**')
window(s, '2026-11-11_drift_vs_slam.gif', 0.45, 1.5, 4.9, 3.45)
for k, (img, h, b) in enumerate([(f'{WEB}/waymo_crop.jpg', 'Waymo robotaxi', '29 cameras, lidar and radar all around'),
                                 (f'{WEB}/robot_side_crop.jpg', 'Our robot', 'One 2D lidar, one IMU, a Raspberry Pi 4')]):
    y = 1.5 + k * 1.75
    card(s, 5.55, y, 4.0, 1.6)
    photo(s, img, 5.67, y + 0.12, 1.75, 1.36)
    text(s, 7.6, y + 0.3, 1.85, 1.1, [[(h, {'size': 15})], [(b, {'size': 11.5, 'light': True, 'color': MUTED})]], space=3)
credit(s, 'Waymo photo: Dllu, CC BY 4.0, Wikimedia Commons')
notes(s, '1.1'); content_slides.append(s)

s = content('y', 'Yujie', 'A 7 Hz single-plane lidar replaces the encoders', 'RPLidar A1M8 · one plane, 12 cm above the floor')
window(s, '2026-11-11_lidar_plane.png', 0.45, 1.5, 5.6, 3.0, bg=WHITE)
for k, (h, b) in enumerate([('Static scene', 'Anything moving with the robot reads as "not moving"'),
                            ('Instant scan', 'At 7 Hz the robot turns about 8° per sweep'),
                            ('Every surface echoes', 'Glass returns nothing, table tops sit above')]):
    y = 1.5 + k * 1.15
    card(s, 6.25, y, 3.3, 1.0)
    o = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(6.4), Inches(y + 0.29), Inches(0.42), Inches(0.42))
    o.fill.solid(); o.fill.fore_color.rgb = YEL; o.line.fill.background()
    o.text_frame.margin_left = o.text_frame.margin_right = 0; o.text_frame.text = str(k + 1)
    rr = o.text_frame.paragraphs[0].runs[0]; rr.font.size = Pt(14); rr.font.name = FONT; rr.font.color.rgb = INK
    o.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    text(s, 7.0, y + 0.13, 2.45, 0.8, [[(h, {'size': 15})], [(b, {'size': 11, 'color': MUTED, 'light': True})]], space=2)
pill(s, 0.45, 4.65, 2.5, 0.38, 'rf2o · lidar odometry', WHITE, size=11)
pill(s, 3.1, 4.65, 2.95, 0.38, 'SLAM Toolbox · graph SLAM', WHITE, size=11)
notes(s, '1.2'); content_slides.append(s)

s = content('y', 'Yujie', 'The EKF fuses lidar odometry with the gyro')
window(s, '2026-11-11_fusion_flow.png', 1.55, 1.3, 6.9, 2.35, bg=WHITE)
for k, (h, b, ic) in enumerate([('Velocities, not poses', 'One bad reading cannot drag the estimate', 'TbGauge'),
                                ('Fitted noise values', 'From our own hand tests', 'TbChartDots'),
                                ('One publisher only', 'Two publishers of odom → base spin the map', 'TbBroadcast')]):
    point(s, 0.45 + k * 3.1, 3.85, 2.9, 1.15, h, b, icon=ic, hs=14, bs=11)
notes(s, '1.3'); content_slides.append(s)

s = content('y', 'Yujie', 'Skid steer, driven open loop, with a stall floor')
window(s, '2026-11-11_motor_drive.png', 0.45, 1.85, 5.6, 2.6, bg=WHITE)
for k, (h, b, ic) in enumerate([('Open loop', 'No encoders, no speed feedback', 'TbRefreshOff'),
                                ('Skid steer', 'Wheels scrape on turns, so the real track is wider', 'TbSteeringWheel'),
                                ('Stall floor', 'Below a certain duty, the wheels do not turn', 'TbArrowBarToDown')]):
    point(s, 6.25, 1.3 + k * 1.27, 3.3, 1.13, h, b, icon=ic)
notes(s, '1.4'); content_slides.append(s)

s = content('y', 'Yujie', 'Nav2: Dijkstra planner, Regulated Pure Pursuit')
window(s, '2026-11-11_nav2_concept.png', 0.45, 1.3, 5.6, 3.7)
card(s, 6.25, 1.3, 3.3, 3.7)
rows = [('Inflation', '0.25 m'), ('Lookahead', '0.2 to 0.4 m'), ('Speed cap', '0.15 m/s'), ('Safety', 'collision monitor, lidar stop, watchdog, switch')]
text(s, 6.47, 1.4, 2.9, 3.5, [p for k_, v in rows for p in ([(k_.upper(), {'size': 9, 'color': MUTED})], [(v, {'size': 15})])], space=7, anchor=MSO_ANCHOR.MIDDLE)
notes(s, '1.5'); content_slides.append(s)

s = content('y', 'Yujie', 'Papers used better sensors. We measured live')
card(s, 0.45, 1.2, 9.1, 2.75)
rows = [('', 'Lidar', 'Encoders', 'Results from', 'They found', 'We saw'),
        ('Kudriashov 2026', 'Ouster 3D, cut to 2D', 'no', 'desktop replay', 'Runs repeat to 0.2 m', '3 replays, 3 answers'),
        ('Merrick 2026', 'Hokuyo UTM-30LX', 'yes', 'PR2 dataset', 'IMU cuts error 60–75 %', 'gyro 360.2° vs lidar 352.9°'),
        ('Ye 2021', 'Hokuyo, 40 Hz', '', '', 'People ruin the map', 'Person behind: 24 %'),
        ('Salem 2023', 'low-rate 2D lidars', '', '', 'motion skews each scan', 'about 8° per scan at 1 rad/s'),
        ('Ours', 'A1M8, 7 Hz', 'no', 'Pi 4, live', '', '')]
widths = [1.3, 1.45, 0.75, 1.25, 2.05, 2.0]
tbl = s.shapes.add_table(len(rows), len(widths), Inches(0.6), Inches(1.32), Inches(sum(widths)), Inches(2.5)).table
tbl._tbl.tblPr.set('firstRow', '0'); tbl._tbl.tblPr.set('bandRow', '0')
for c, w in enumerate(widths):
    tbl.columns[c].width = Inches(w)
for r, row in enumerate(rows):
    tbl.rows[r].height = Inches(0.42)
    ours = row[0] == 'Ours'
    for c, v in enumerate(row):
        cell = tbl.cell(r, c)
        cell.fill.solid(); cell.fill.fore_color.rgb = PALE_YEL if ours else WHITE
        cell.margin_left = cell.margin_right = Inches(0.06); cell.margin_top = cell.margin_bottom = Inches(0.02)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        tcPr = cell._tc.get_or_add_tcPr()
        for side in ('a:lnL', 'a:lnR', 'a:lnT', 'a:lnB'):
            line = side == 'a:lnB' and not ours and r < len(rows) - 2
            ln = tcPr.makeelement(qn(side), {'w': '9525' if line else '0'})
            if line:
                sf = ln.makeelement(qn('a:solidFill'), {}); sf.append(sf.makeelement(qn('a:srgbClr'), {'val': LINE})); ln.append(sf)
            else:
                ln.append(ln.makeelement(qn('a:noFill'), {}))
            tcPr.append(ln)
        tf = cell.text_frame; tf.word_wrap = True
        run = tf.paragraphs[0].add_run(); run.text = cap(v); f = run.font
        f.size = Pt(9.5 if r == 0 else 11); f.name = FONT if (c == 0 or ours or (r == 1 and c == 5)) else LIGHT
        f.color.rgb = MUTED if r == 0 else INK
credit(s, 'Full references on the last slide')
take(s, 0.45, 4.12, 7.0, 0.82, 'Published numbers come from good sensors and desktop replays. **We measured live.**')
notes(s, '1.6'); content_slides.append(s)

s = content('y', 'Yujie', 'Robots on sale add cameras and drive up to 8x faster')
for k, (img, n, sens, spd, fill) in enumerate([(f'{WEB}/bellabot_crop.jpg', 'Pudu BellaBot', 'Lidar + 3 depth cameras', 'Indoors · up to 1.2 m/s', None),
                                               (f'{WEB}/starship_crop.jpg', 'Starship', 'Cameras + radar', 'Sidewalks · up to 6 km/h', None),
                                               (f'{WEB}/robot_side_crop.jpg', 'Ours', 'One 2D lidar + IMU', 'Indoors · capped 0.15 m/s', PALE_YEL)]):
    x = 0.45 + k * 3.1
    card(s, x, 1.3, 2.9, 3.7, fill=fill)
    photo(s, img, x + 0.15, 1.45, 2.6, 1.8)
    text(s, x + 0.2, 3.4, 2.5, 1.5, [[(n, {'size': 17})], [(sens, {'size': 12.5, 'light': True})], [(spd, {'size': 12, 'light': True, 'color': MUTED})]], space=5)
credit(s, 'Photos: MIKI Yoshihito, CC BY 2.0; Ohpuu, CC0 (Wikimedia Commons)')
notes(s, '1.7'); content_slides.append(s)


# ---------- 2. Implementation (pipeline first) ----------
divider(orig[7])
s = content('c', 'Sherman  ·  overview', 'Six blocks, left to right', 'ROS 2 Jazzy · Foxglove to watch live · rosbag to record every run')
window(s, '2026-11-11_pipeline.png', 0.45, 1.5, 9.1, 1.85)
for k, (h, items, fill) in enumerate([('Written by us', 'IMU node · motor node · robot model · launch files', RGBColor(0xFD, 0xE8, 0xD2)),
                                      ('Existing packages', 'rf2o · EKF · SLAM Toolbox · Nav2', RGBColor(0xE3, 0xEE, 0xF8))]):
    x = 0.45 + k * 4.65
    card(s, x, 3.6, 4.45, 1.4, fill=fill)
    text(s, x + 0.25, 3.78, 4.0, 1.1, [[(h, {'size': 16})], [(items, {'size': 13, 'light': True})]], space=6)
notes(s, '2.1'); content_slides.append(s)
s = content('c', 'Sherman  ·  blocks 1 and 2', 'We made two cheap sensors trustworthy', 'Fixes: **fitted noise values** for rf2o, **EKF at 20 Hz**')
window(s, '2026-11-11_scan_gaps.png', 0.45, 1.5, 4.45, 2.85)
window(s, '2026-11-10_turn_gyro_vs_rf2o.png', 5.1, 1.5, 4.45, 2.85)
text(s, 0.5, 4.48, 4.4, 0.6, [[('≈ 25 %', {'size': 22, 'light': True})], [('of pings empty, following glass and dark surfaces', {'size': 11, 'light': True, 'color': MUTED})]])
text(s, 5.15, 4.48, 4.4, 0.6, [[('360.2° vs 352.9°', {'size': 22, 'light': True})], [('gyro vs rf2o, one full turn by hand', {'size': 11, 'light': True, 'color': MUTED})]])
notes(s, '3.1'); content_slides.append(s)

s = content('c', 'Sherman  ·  block 3', 'One hand-pushed lap made the map', 'Once every scan had **the same number of beams**')
window(s, '2026-11-10_map_build.gif', 0.45, 1.5, 4.1, 3.5)
window(s, '2026-11-11_beam_count.png', 4.75, 1.5, 4.8, 2.6)
pill(s, 4.75, 4.3, 2.3, 0.42, 'expected 931, got 1041', COR, WHITE, size=11)
pill(s, 7.15, 4.3, 2.4, 0.42, 'fixed at 720 beams', BLU, WHITE, size=11)
notes(s, '3.2'); content_slides.append(s)

s = content('c', 'Sherman  ·  blocks 3 and 4', 'Loop closure kept the walls single', 'Localisation then finds the robot within **3 cm**, if it starts within **20°**')
window(s, '2026-11-11_map_overlay.png', 0.45, 1.5, 5.4, 3.5)
stat(s, 6.05, 1.5, 3.5, 1.2, '0.20 m vs 0.36 m', 'start-end gap, SLAM vs odometry (live)')
window(s, '2026-11-11_wrong_start.png', 6.05, 2.85, 3.5, 2.15)
notes(s, '3.3'); content_slides.append(s)

s = content('c', 'Sherman  ·  block 2', 'A person behind the robot fooled the odometry', 'A 1 m push read **24 %** of the distance, twice')
for k, (lab, h, b, fill) in enumerate([('RULED OUT', 'Beam count', 'Live: 101 %, 96 %', None),
                                       ('RULED OUT', 'CPU, timing', 'Slow replay: same', None),
                                       ('CAUSE', 'Person behind', '127–152 points vs 16–18', COR),
                                       ('FIX, OFFLINE', 'Range cut', 'Ignore under 0.6 m', BLU)]):
    point(s, 0.45 + (k % 2) * 2.2, 1.5 + (k // 2) * 1.17, 2.05, 1.05, h, b, label=lab, fill=fill, strike=lab == 'RULED OUT', hs=14, bs=11)
stat(s, 0.45, 3.9, 4.25, 1.1, '24 %  →  99.5 %', 'of the push, after the range cut (offline)', big_size=26)
window(s, '2026-11-11_oi8_person_behind_tall.gif', 4.95, 1.5, 4.6, 3.5, bg=WHITE)
notes(s, '3.4'); content_slides.append(s)

s = content('c', 'Sherman  ·  block 5', 'Nav2 failed seven ways before reaching a goal', 'Every fix was **a setting, not new code**')
for k, (lab, h, b, ic) in enumerate([('SILENT', 'Twist vs TwistStamped', 'Wheels never moved, no error', 'TbVolumeOff'),
                                     ('SLOW PI', 'Timeouts too short', 'Raised from 20 ms to 1 s', 'TbHourglass'),
                                     ('SLOW PI', 'Transform data too old', 'Scans 0.5 s apart, tolerance 0.5 s', 'TbClockExclamation'),
                                     ('STALL FLOOR', 'Slowed to 0.045 m/s', 'Minimum speed now 0.10 m/s', 'TbArrowBarToDown')]):
    point(s, 0.45 + (k % 2) * 4.65, 1.45 + (k // 2) * 1.25, 4.45, 1.1, h, b, label=lab, icon=ic, ring=COR)
take(s, 0.45, 4.02, 7.6, 0.82, 'Navigation defaults assume motors that can crawl and a fast computer. **Ours had neither.**')
notes(s, '3.5'); content_slides.append(s)

s = content('c', 'Chloe  ·  block 6', 'To drive itself, the robot first needed stable power')
for k, (big, lab, fill) in enumerate([('67.5 %', 'of power samples under-voltage on the wall supply', COR),
                                      ('0 %', 'on a power bank: 0 of 60 samples', GRN)]):
    x = 0.45 + k * 2.75
    card(s, x, 1.3, 2.55, 3.7, fill=fill)
    text(s, x + 0.25, 1.5, 2.1, 3.3, [[(big, {'size': 44, 'light': True, 'color': WHITE})], [(lab, {'size': 13, 'light': True, 'color': WHITE})]],
         space=6, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0.45, 5.03, 5.2, 0.18, 'Pi power status logged every 2 s while Nav2 ran', size=8, color=MUTED, light=True)
point(s, 6.05, 1.3, 3.5, 1.15, 'Nav2 kept shutting down', 'The Pi rebooted mid-run on wall power', icon='TbHourglass', ring=COR)
point(s, 6.05, 2.58, 3.5, 1.15, 'Loose motor wire', 'Rebooted the Pi twice', icon='TbPlugConnectedX', ring=COR)
point(s, 6.05, 3.86, 3.5, 1.14, 'Motor switch', 'The physical kill switch', icon='TbPower', ring=COR)
notes(s, '3.6'); content_slides.append(s)

s = content('c', 'Chloe  ·  block 6', 'The wheels stall below 0.10 m/s', 'Fitted: **speed = 2.46 × (duty − 0.078)**')
window(s, '2026-11-10_motor_curve.png', 0.45, 1.5, 4.45, 2.65)
window(s, '2026-11-10_straights.png', 5.1, 1.5, 4.45, 2.65)
pill(s, 0.45, 4.4, 2.85, 0.44, 'PWM 1 kHz → 100 Hz', WHITE, size=11)
pill(s, 3.45, 4.4, 2.85, 0.44, 'Kick start: 0.30 duty, 0.35 s', WHITE, size=11)
pill(s, 6.45, 4.4, 3.1, 0.44, 'Silent: "live" flag never passed', COR, WHITE, size=11)
notes(s, '3.7'); content_slides.append(s)

# ---------- 4. Results ----------
divider(orig[8])
s = content('g', 'Chloe', 'It reached a goal on its own, around a box')
card(s, 0.45, 1.3, 5.8, 3.7, fill=WHITE)
mw, mh = 5.56, 5.56 * 720 / 1280
s.shapes.add_movie(f'{FIG}/2026-11-10_V2_box_full.mp4', Inches(0.57), Inches(1.3 + (3.7 - mh) / 2), Inches(mw), Inches(mh), poster_frame_image=POSTER, mime_type='video/mp4')
stat(s, 6.45, 1.3, 3.1, 1.3, 'Goal succeeded', '1.5 m in 93 s, nobody touching it', big_size=24, fill=GRN)
stat(s, 6.45, 2.75, 3.1, 1.05, '1 of 8', 'goals that evening, the rest cancelled', big_size=24)
card(s, 6.45, 3.95, 3.1, 1.05, fill=PALE_YEL)
text(s, 6.65, 4.07, 2.75, 0.9, [[('OUR TAKE', {'size': 9, 'bold': True})], [('The loop closes. **Reliability is not shown yet.**', {'size': 13})]])
notes(s, '3.8'); content_slides.append(s)

s = content('g', 'Chloe', 'Almost every challenge was integration', '**Fourteen challenges** in three weeks, grouped by root cause')
card(s, 0.45, 1.5, 3.3, 2.15, fill=GRN)
text(s, 0.7, 1.65, 2.9, 1.9, [[('13', {'size': 66, 'light': True, 'color': WHITE}), (' of 14', {'size': 26, 'light': True, 'color': WHITE})],
                              [('came from hardware, load, interfaces or process', {'size': 13, 'light': True, 'color': WHITE})]])
card(s, 0.45, 3.8, 3.3, 1.2)
text(s, 0.7, 3.95, 2.9, 0.95, [[('8', {'size': 30, 'light': True}), (' of 14', {'size': 15, 'light': True})], [('were surprises', {'size': 13, 'light': True, 'color': MUTED})]])
card(s, 3.95, 1.5, 5.6, 3.5)
groups = [('Cheap hardware', 6, YEL), ('Interface mismatch', 3, YEL), ('Loaded computer', 2, YEL), ('Platform, process', 2, YEL), ('Algorithm assumption', 1, COR)]
for k, (g, n, col) in enumerate(groups):
    y = 1.78 + k * 0.62
    text(s, 4.2, y, 2.1, 0.42, g, size=13, light=True, anchor=MSO_ANCHOR.MIDDLE)
    bar = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.35), Inches(y + 0.05), Inches(0.45 * n), Inches(0.32))
    bar.adjustments[0] = 0.5; bar.fill.solid(); bar.fill.fore_color.rgb = col; bar.line.fill.background()
    text(s, 6.45 + 0.45 * n, y, 0.5, 0.42, str(n), size=14, anchor=MSO_ANCHOR.MIDDLE)
text(s, 4.2, 4.85, 5.2, 0.2, 'Only one came from an algorithm: the person behind the robot', size=10, color=MUTED, light=True)
notes(s, '3.9'); content_slides.append(s)

s = content('g', 'Chloe', 'What we learned, and what comes next')
card(s, 0.45, 1.3, 5.2, 3.75)
pill(s, 0.7, 1.5, 1.5, 0.42, 'Lessons', YEL, INK, size=13)
for k, it in enumerate(['Integration is the hard part', 'Measure physical limits on day one', 'Test live, not on replays',
                        'No ground truth? Design one', 'Make silent failures loud']):
    y = 2.12 + k * 0.56
    o = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.72), Inches(y), Inches(0.38), Inches(0.38))
    o.fill.solid(); o.fill.fore_color.rgb = YEL; o.line.fill.background()
    o.text_frame.margin_left = o.text_frame.margin_right = 0; o.text_frame.text = str(k + 1)
    rr = o.text_frame.paragraphs[0].runs[0]; rr.font.size = Pt(13); rr.font.name = FONT; rr.font.color.rgb = INK
    o.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    text(s, 1.28, y, 4.2, 0.38, it, size=15, light=True, anchor=MSO_ANCHOR.MIDDLE)
for k, (h, col, fg, items) in enumerate([('Limits', COR, WHITE, ['No encoders', 'One goal reached', 'Slow computer', 'One lidar plane']),
                                         ('Next', BLU, WHITE, ['Wheel encoders', 'Hardware PWM', 'Faster computer', 'Live people filter'])]):
    y = 1.3 + k * 1.92
    card(s, 5.85, y, 3.7, 1.83)
    pill(s, 6.05, y + 0.18, 1.3, 0.4, h, col, fg, size=13)
    for m, it in enumerate(items):
        pill(s, 6.05 + (m % 2) * 1.72, y + 0.72 + (m // 2) * 0.5, 1.6, 0.38, it, RGBColor(0xF4, 0xF2, 0xF2), INK, size=11)
notes(s, '3.10'); content_slides.append(s)

# ---------- close: the group's "Aim" slide design, reused ----------
close = prs.slides.add_slide(orig[1].slide_layout)
for sh in list(close.shapes):
    sh._element.getparent().remove(sh._element)
for sh in orig[1].shapes:
    if sh.name == 'Google Shape;1910;p34':      # the "Our resources" card is not needed here
        continue
    c = clone(sh, close)
    if sh.name == 'Google Shape;1907;p34':      # narrower bubble, robot goes on the right
        c.width = Inches(4.8)
    if sh.name == 'Google Shape;1917;p34':
        c.text_frame.paragraphs[0].runs[0].text = 'Verdict'
    if sh.name == 'Google Shape;1909;p34':
        p = c.text_frame.paragraphs[0]
        for r in list(p.runs)[1:]:
            r._r.getparent().remove(r._r)
        for extra in list(c.text_frame.paragraphs)[1:]:
            extra._p.getparent().remove(extra._p)
        p.runs[0].text = 'A low-cost robot can map a room and navigate it on its own, once every physical limit is measured and designed around.'
        c.left, c.top, c.width, c.height = Inches(1.78), Inches(1.92), Inches(3.8), Inches(1.75)
        c.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE; c.text_frame.word_wrap = True
        from pptx.enum.text import MSO_AUTO_SIZE
        c.text_frame.auto_size = MSO_AUTO_SIZE.NONE
        p.alignment = PP_ALIGN.LEFT
        p.runs[0].font.size = Pt(19)
src = next(x for x in orig[0].shapes if x.shape_type == 13)   # title slide's robot cut-out, same crop
rw = 3.2; rh = rw * src.height / src.width
pic = close.shapes.add_picture(ROBOT, Inches(6.2), Inches(1.7), Inches(rw), Inches(rh))
pic.crop_left, pic.crop_right, pic.crop_top, pic.crop_bottom = src.crop_left, src.crop_right, src.crop_top, src.crop_bottom
text(close, 5.6, 4.35, 4.0, 0.5, [[('Thank you  ·  Questions?', {'size': 20, 'light': True})]], align=PP_ALIGN.CENTER)
order.append(close); notes(close, 'Close')

# ---------- backup: references ----------
s = content('o', 'Backup', 'References')
refs = [('Kudriashov et al. 2026', 'A Real-World Benchmark of Monte Carlo-Assisted EKF Odometry for Online Pose Estimation in 2D LiDAR SLAM. Sensors 26(13), 4264'),
        ('Merrick and Nandikolla 2026', 'Evaluating the Impact of Extended Kalman Filter Odometry on the Performance of 2D LiDAR SLAM Algorithms. Sensors 26(17), 5468'),
        ('Ye et al. 2021', 'Mapping While Following: 2D LiDAR SLAM in Indoor Dynamic Environments with a Person Tracker. IEEE ROBIO 2021'),
        ('Salem et al. 2023', 'arXiv preprint 2303.07312 (de-skewing scans from low-rate 2D lidars)'),
        ('Jaimez et al. 2016', 'IEEE ICRA 2016 (rf2o, range-flow planar laser odometry)'),
        ('Macenski and Jambrecic 2021', 'Journal of Open Source Software 6(61) (SLAM Toolbox)'),
        ('Ran et al. 2025', 'Remote Sensing 17(7), 1214 (review of 2D lidar SLAM)')]
card(s, 0.45, 1.25, 9.1, 3.8)
text(s, 0.7, 1.4, 8.6, 3.55, [[(a + '.  ', {'size': 11.5, 'bold': True}), (b, {'size': 11.5, 'light': True})] for a, b in refs], space=7, anchor=MSO_ANCHOR.MIDDLE)
order.append(s)

# ---------- order, page numbers, drop unused template slides ----------
page_numbers()
lst = prs.slides._sldIdLst
by_part = {prs.part.related_part(e.get(qn('r:id'))): e for e in lst}
for e in list(lst):
    lst.remove(e)
for s in order:
    lst.append(by_part[s.part])
for part, e in by_part.items():
    if e.getparent() is None:
        prs.part.drop_rel(e.get(qn('r:id')))
prs.save(OUT)
print('saved', OUT, len(prs.slides), 'slides')
