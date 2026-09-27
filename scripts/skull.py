"""Paint a human skull, as the source for the ASCII card.

The note's first rule, made literal: a cracked skull lit from above, black sockets with
embers burning in them, blood running from both, bared teeth and a hanging jaw. Shaded,
not outlined, so the glyphs read as bone rather than a drawing.

Returns (lum, alpha, tint) as float arrays in 0..1 at SIZE: luminance becomes density,
alpha marks what is drawn, tint marks the parts shown in red.
"""

import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SIZE = (600, 776)
SS = 2
SEED = 40
CX = 300


def _mask(draw_fn, blur: float = 0.0) -> np.ndarray:
    img = Image.new("L", (SIZE[0] * SS, SIZE[1] * SS), 0)
    draw_fn(ImageDraw.Draw(img), lambda pts: [(x * SS, y * SS) for x, y in pts])
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(blur * SS))
    return np.asarray(img).astype(np.float32) / 255


def render() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = random.Random(SEED)
    ys, xs = np.mgrid[0:SIZE[1] * SS, 0:SIZE[0] * SS].astype(np.float32) / SS
    lum = np.zeros_like(xs)
    alpha = np.zeros_like(xs)
    tint = np.zeros_like(xs)
    noise = np.asarray(Image.effect_noise((SIZE[0] * SS, SIZE[1] * SS), 55).filter(ImageFilter.GaussianBlur(1.4))).astype(np.float32) / 255

    # Cranium and face: one outline, broad at the temples, pinched at the cheeks.
    right = [(0, 90), (120, 112), (196, 190), (220, 300), (212, 392), (190, 440), (178, 492), (150, 520), (120, 566), (72, 584), (0, 590)]
    outline = [(CX + x, y) for x, y in right] + [(CX - x, y) for x, y in reversed(right)]
    head = _mask(lambda d, p: d.polygon(p(outline), fill=255), 1.2) > 0.5

    # Jaw, hanging slightly open below the upper teeth.
    jaw_pts = [(CX - 132, 590), (CX - 150, 640), (CX - 120, 712), (CX - 50, 748), (CX + 50, 748), (CX + 120, 712), (CX + 150, 640), (CX + 132, 590)]
    jaw = _mask(lambda d, p: d.polygon(p(jaw_pts), fill=255), 1.2) > 0.5

    # Bone shading: a dome lit from above, cheekbones catching the light.
    nx, ny = (xs - CX) / 215, (ys - 330) / 300
    nz = np.sqrt(np.clip(1 - nx ** 2 - ny ** 2 * 0.6, 0, 1))
    light = np.clip(-0.15 * nx - 0.6 * ny + 0.78 * nz, 0, 1)
    bone = (0.2 + 0.72 * light ** 1.2) * (0.8 + 0.35 * noise)
    for side in (-1, 1):
        bone += 0.18 * np.exp(-(((xs - (CX + side * 150)) / 40) ** 2 + ((ys - 440) / 26) ** 2))
        bone -= 0.35 * np.exp(-(((xs - (CX + side * 170)) / 36) ** 2 + ((ys - 300) / 70) ** 2))  # temples
    bone_jaw = (0.25 + 0.4 * np.clip(1 - (ys - 590) / 170, 0, 1)) * (0.8 + 0.35 * noise)
    for side in (-1, 1):
        bone -= 0.5 * np.exp(-(((xs - (CX + side * 140)) / 34) ** 2 + ((ys - 522) / 30) ** 2))
    edge = np.clip((np.hypot((xs - CX) / 215, (ys - 330) / 260) - 0.75) / 0.3, 0, 1)
    bone *= 1 - 0.6 * edge
    lum[head], alpha[head] = np.clip(bone[head], 0, 1), 1
    lum[jaw], alpha[jaw] = np.clip(bone_jaw[jaw], 0, 1), 1

    # Cracks: dark random walks down from the crown.
    cracks = Image.new("L", (SIZE[0] * SS, SIZE[1] * SS), 0)
    cd = ImageDraw.Draw(cracks)
    for start_x, heading in ((CX + 30, 1.9), (CX - 80, 1.3), (CX + 120, 2.2)):
        x, y, a = start_x, 110.0, heading
        pts = [(x, y)]
        for _ in range(26):
            a += rng.uniform(-0.45, 0.45)
            x += 8 * math.cos(a)
            y += 8 * abs(math.sin(a)) + 2
            pts.append((x, y))
            if rng.random() < 0.12:  # a short branch
                bx, by = x + rng.uniform(-24, 24), y + rng.uniform(10, 26)
                cd.line([(x * SS, y * SS), (bx * SS, by * SS)], fill=255, width=2 * SS)
        cd.line([(px * SS, py * SS) for px, py in pts], fill=255, width=3 * SS, joint="curve")
    crack = (np.asarray(cracks) > 0) & head & (ys < 330)
    lum[crack] = 0.02

    # Sockets: deep and black, with an ember burning at the back of each.
    for side in (-1, 1):
        ex, ey = CX + side * 88, 352
        pts = []
        for i in range(40):
            a = i / 40 * math.tau
            r = 56 + 8 * math.sin(3 * a + side)
            px, py = ex + r * math.cos(a) * 1.08, ey + r * math.sin(a) * 0.9
            if py < ey:  # the brow presses down toward the nose
                py += 0.34 * (px - ex) * side
            pts.append((px, py))
        soft = _mask(lambda d, p: d.polygon(p(pts), fill=255), 9)
        lum *= 1 - 0.85 * soft
        sock = _mask(lambda d, p: d.polygon(p(pts), fill=255), 2) > 0.6
        lum[sock] = 0.0
        ember = np.exp(-(((xs - ex) / 13) ** 2 + ((ys - ey - 4) / 11) ** 2))
        hot = sock & (ember > 0.18)
        lum[hot], tint[hot] = 0.45 + 0.55 * ember[hot], 1
        # blood running from each socket down the cheek
        for k in range(4):
            dx = rng.uniform(-34, 30)
            length = rng.uniform(70, 220)
            w0 = rng.uniform(4, 9)
            wobble = rng.uniform(4, 9)
            width = w0 * (1 - 0.45 * np.clip((ys - ey - 40) / length, 0, 1))
            cx_ = ex + dx + wobble * np.sin((ys - ey) / 23 + k)
            run = (np.abs(xs - cx_) < width) & (ys > ey + 30) & (ys < ey + 40 + length) & (head | jaw)
            end = ey + 40 + length
            drop = ((xs - (ex + dx + wobble * math.sin((end - ey) / 23 + k))) ** 2 + ((ys - end) / 1.3) ** 2) < (w0 * 1.3) ** 2
            lum[run | drop], tint[run | drop] = 0.55 + 0.25 * noise[run | drop], 1

    # Nasal cavity: an inverted heart, black.
    nose_pts = [(CX, 400), (CX - 30, 456), (CX - 22, 486), (CX, 476), (CX + 22, 486), (CX + 30, 456)]
    nose = _mask(lambda d, p: d.polygon(p(nose_pts), fill=255), 1.5) > 0.5
    lum[nose] = 0.0

    # Teeth: upper and lower rows, bared, with dark gaps and a black gape between.
    gape = (ys > 580) & (ys < 612) & (np.abs(xs - CX) < 118) & (head | jaw)
    lum[gape] = 0.0
    for row_top, row_h, rows_y in ((536, 44, 1), (612, 40, -1)):
        x = CX - 112
        while x < CX + 110:
            tw = rng.uniform(15, 21)
            curve = 12 * ((x + tw / 2 - CX) / 112) ** 2
            top = row_top + curve * rows_y
            h = row_h * rng.uniform(0.55, 1.0) * (0.35 if rng.random() < 0.1 else 1)  # a few broken
            tip = top + h if rows_y == 1 else top + row_h - h
            u = (xs - (x + tw / 2)) / (tw / 2 - 1.5)
            rounded = np.sqrt(np.clip(1 - u ** 2, 0, 1)) * 6
            if rows_y == 1:
                tooth = (np.abs(u) < 1) & (ys > top) & (ys < tip + rounded - 6)
            else:
                tooth = (np.abs(u) < 1) & (ys < top + row_h) & (ys > tip - rounded + 6)
            shade = 0.5 + 0.4 * np.clip(1 - np.abs(u), 0, 1)
            lum[tooth] = (shade * (0.85 + 0.2 * noise))[tooth]
            alpha[tooth] = 1
            gap = (np.abs(xs - x) < 1.6) & (ys > top) & (ys < top + row_h)
            lum[gap] = 0.03
            x += tw

    small = lambda a: np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).resize(SIZE, Image.LANCZOS)).astype(np.float32) / 255
    return small(lum), small(alpha), small(tint)
