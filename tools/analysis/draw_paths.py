"""Draw planner paths over the saved lab map (PIL only)."""
import json

from PIL import Image, ImageDraw

RES, OX, OY = 0.05, -9.964, -3.670             # from 2026-10-31_room2.yaml
SCALE = 6                                       # output px per map cell
X0, X1, Y0, Y1 = -4.0, 4.0, -3.5, 3.5           # window around home (m)
COLS = [(230, 25, 75), (0, 130, 200), (245, 130, 48), (145, 30, 180), (60, 180, 75)]

img = Image.open('/home/robot/maps/2026-10-31_room2.pgm').convert('RGB')
w, h = img.size


def px(x, y):
    return ((x - OX) / RES, h - (y - OY) / RES)  # map metres -> image pixels (y flipped)


(l, t), (r, b) = px(X0, Y1), px(X1, Y0)
crop = img.crop((int(l), int(t), int(r), int(b)))
crop = crop.resize((crop.width * SCALE, crop.height * SCALE), Image.NEAREST)
d = ImageDraw.Draw(crop)


def to_crop(x, y):
    a, c = px(x, y)
    return ((a - int(l)) * SCALE, (c - int(t)) * SCALE)


# 1 m grid
for gx in range(int(X0), int(X1) + 1):
    d.line([to_crop(gx, Y0), to_crop(gx, Y1)], fill=(0, 120, 255), width=1)
    d.text((to_crop(gx, Y0)[0] + 3, crop.height - 14), f'{gx} m', fill=(0, 90, 220))
for gy in range(int(Y0), int(Y1) + 1):
    d.line([to_crop(X0, gy), to_crop(X1, gy)], fill=(0, 120, 255), width=1)
    d.text((3, to_crop(X0, gy)[1] - 12), f'{gy} m', fill=(0, 90, 220))

paths = {k: v for k, v in json.load(open('/tmp/paths.json')).items() if v}
for i, (goal, pts) in enumerate(paths.items()):
    c = COLS[i % len(COLS)]
    d.line([to_crop(*p) for p in pts], fill=c, width=5)
    gx, gy = to_crop(*pts[-1])
    d.ellipse([gx - 9, gy - 9, gx + 9, gy + 9], fill=c, outline=(0, 0, 0))
    d.text((gx + 12, gy - 6), f'({goal})', fill=c)
sx, sy = to_crop(0, 0)
d.rectangle([sx - 11, sy - 11, sx + 11, sy + 11], fill=(0, 220, 0), outline=(0, 0, 0), width=2)
d.text((sx + 14, sy + 8), 'home (0, 0)', fill=(0, 140, 0))
crop.save('/tmp/planner_paths.png')
print('ok', crop.size)
