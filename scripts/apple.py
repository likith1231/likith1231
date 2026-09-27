"""Paint Ryuk's apple resting on the Death Note, as the source for the ASCII card.

A closed notebook lies at a slight angle, its cover framed and its spine dark. On it sits one apple
with a bite out of it, lit from the upper left, a leaf on its stem, and a quill leans in
from the left. The apple is the only colour.

Returns (image, tint): an LA image whose alpha marks what is drawn and whose luminance
becomes glyph density, and an L mask marking the parts drawn in red.
"""

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SIZE = (600, 776)
SS = 2  # supersample

NOTE = (300, 598, 520, 250, -7)  # cx, cy, width, height, degrees
THICKNESS = 16
APPLE = (322, 356, 136)          # cx, cy, r
BITE = (452, 318, 58)
LIGHT = np.array([-0.55, -0.62, 0.56])


def _layer() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("L", (SIZE[0] * SS, SIZE[1] * SS), 0)
    return image, ImageDraw.Draw(image)


def _rect(cx: float, cy: float, w: float, h: float, degrees: float, inset: float = 0.0) -> list[tuple[float, float]]:
    a = math.radians(degrees)
    ux, uy, vx, vy = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
    hw, hh = w / 2 - inset, h / 2 - inset
    corners = ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))
    return [((cx + x * ux + y * vx) * SS, (cy + x * uy + y * vy) * SS) for x, y in corners]


def _paint(lum, alpha, layer: Image.Image, value) -> np.ndarray:
    m = np.array(layer) > 0
    lum[m] = value if np.isscalar(value) else value[m]
    alpha[m] = 1
    return m


def _notebook(lum, alpha) -> None:
    cx, cy, w, h, deg = NOTE
    # The page block, peeking out below the cover, with fine page lines.
    pages, draw = _layer()
    draw.polygon(_rect(cx + 4, cy + THICKNESS, w - 6, h, deg), fill=255)
    _paint(lum, alpha, pages, 175)
    lines, draw = _layer()
    for k in range(1, 4):
        pts = _rect(cx + 4, cy + k * THICKNESS / 4, w - 6, h, deg)
        draw.line([pts[3], pts[2]], fill=255, width=2 * SS)
    _paint(lum, alpha, lines, 235)

    cover, draw = _layer()
    draw.polygon(_rect(cx, cy, w, h, deg), fill=255)
    _paint(lum, alpha, cover, 92)
    border, draw = _layer()
    draw.polygon(_rect(cx, cy, w, h, deg, 14), outline=255, width=6 * SS)
    _paint(lum, alpha, border, 185)
    spine, draw = _layer()
    a = math.radians(deg)
    draw.polygon(_rect(cx - (w / 2 - 20) * math.cos(a), cy - (w / 2 - 20) * math.sin(a), 40, h, deg), fill=255)
    _paint(lum, alpha, spine, 48)


def _apple(lum, alpha, tint) -> None:
    h, w = lum.shape
    ys, xs = np.mgrid[0:h, 0:w] / SS
    cx, cy, r = APPLE
    # Shadow on the cover first, so the apple paints over it.
    shadow = ((xs - cx - 26) / (r * 1.05)) ** 2 + ((ys - cy - r * 0.98) / (r * 0.26)) ** 2 < 1
    lum[shadow & (alpha > 0)] = 30

    # A little wider than tall, with a dimple at the top where the stem goes in.
    nx, ny = (xs - cx) / (r * 1.06), (ys - cy) / r
    dimple = 0.16 * np.exp(-((xs - cx) ** 2) / (2 * (r * 0.16) ** 2)) * (ny < -0.6)
    inside = nx ** 2 + ny ** 2 < (1 - dimple) ** 2
    bx, by, br = BITE
    d2 = (xs - bx) ** 2 + (ys - by) ** 2
    theta = np.arctan2(ys - by, xs - bx)
    bite = d2 < br ** 2
    scallop = d2 < (br + 6 * np.abs(np.sin(theta * 6))) ** 2  # tooth marks around the rim
    body = inside & ~scallop
    nz = np.sqrt(np.clip(1 - nx ** 2 - ny ** 2, 0, 1))
    shade = np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0, 1)
    spec = np.clip(shade - 0.86, 0, 1) * 6
    value = 118 + 120 * shade ** 1.2 + 60 * spec
    lum[body], alpha[body], tint[body] = np.clip(value[body], 0, 255), 1, 1
    # The bitten flesh: pale and untinted.
    flesh = inside & scallop & ~bite
    lum[flesh], alpha[flesh], tint[flesh] = 228, 1, 0


def _stem_and_leaf(lum, alpha, tint) -> None:
    cx, cy, r = APPLE
    image, draw = _layer()
    top = (cx, cy - r * 0.84)
    stem = [(top[0] + i * 0.6, top[1] - i * 2.2 - 0.02 * i * i) for i in range(28)]
    draw.line([(x * SS, y * SS) for x, y in stem], fill=170, width=9 * SS, joint="curve")
    # A leaf off the stem, tilted to the right, its midrib and veins brighter than its blade.
    lx, ly = stem[16]
    t = np.linspace(0, np.pi, 60)
    length, width = 112, 34
    along = np.array([math.cos(-0.5), math.sin(-0.5)])
    across = np.array([-along[1], along[0]])
    upper = [(lx + along[0] * length * s / np.pi + across[0] * width * np.sin(s),
              ly + along[1] * length * s / np.pi + across[1] * width * np.sin(s)) for s in t]
    lower = [(lx + along[0] * length * s / np.pi - across[0] * width * np.sin(s) * 0.7,
              ly + along[1] * length * s / np.pi - across[1] * width * np.sin(s) * 0.7) for s in t[::-1]]
    draw.polygon([(x * SS, y * SS) for x, y in upper + lower], fill=130)
    draw.line([(lx * SS, ly * SS), ((lx + along[0] * length) * SS, (ly + along[1] * length) * SS)], fill=235, width=3 * SS)
    for k in range(1, 5):
        px, py = lx + along[0] * length * k / 5.5, ly + along[1] * length * k / 5.5
        draw.line([(px * SS, py * SS), ((px + along[0] * 14 + across[0] * 20) * SS, (py + along[1] * 14 + across[1] * 20) * SS)], fill=205, width=2 * SS)
    drawn = np.array(image)
    m = drawn > 0
    lum[m], alpha[m], tint[m] = drawn[m], 1, 0


def _quill(lum, alpha) -> None:
    """A feather quill leaning in from the left, nib down toward the note."""
    image, draw = _layer()
    start, end = np.array([66.0, 96.0]), np.array([196.0, 486.0])
    axis = (end - start) / np.linalg.norm(end - start)
    normal = np.array([-axis[1], axis[0]])
    length = np.linalg.norm(end - start)
    for i in range(0, 170):
        s = i / 170
        p = start + axis * length * s
        vane = 30 * np.sin(np.pi * min(1, s * 1.35)) ** 0.8 * (s < 0.74)
        if vane > 1:
            for side in (1, -0.75):
                q = p + normal * vane * side - axis * 16
                draw.line([(p[0] * SS, p[1] * SS), (q[0] * SS, q[1] * SS)], fill=190 if i % 3 else 120, width=SS)
    draw.line([(start[0] * SS, start[1] * SS), (end[0] * SS, end[1] * SS)], fill=245, width=4 * SS)
    nib = end + axis * 16
    draw.polygon([((end + normal * 4) * SS).tolist(), ((end - normal * 4) * SS).tolist(), (nib * SS).tolist()], fill=255)
    drawn = np.array(image)
    m = drawn > 0
    lum[m], alpha[m] = np.maximum(lum[m], drawn[m]), 1


def render() -> tuple[Image.Image, Image.Image]:
    shape = (SIZE[1] * SS, SIZE[0] * SS)
    lum = np.zeros(shape, np.float32)
    alpha = np.zeros(shape, np.float32)
    tint = np.zeros(shape, np.float32)
    _notebook(lum, alpha)
    _quill(lum, alpha)
    _apple(lum, alpha, tint)
    _stem_and_leaf(lum, alpha, tint)

    def image(a: np.ndarray, scale: float) -> Image.Image:
        return Image.fromarray(np.clip(a * scale, 0, 255).astype(np.uint8)).resize(SIZE, Image.LANCZOS)

    la = Image.merge("LA", (image(lum, 1), image(alpha, 255)))
    return la.filter(ImageFilter.SMOOTH), image(tint, 255)
