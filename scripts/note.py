"""Paint the Death Note, as the source for the ASCII card.

The notebook stands tall and a little crooked, its worn black cover titled DEATH NOTE in
gothic capitals. Blood runs down from the letters, four claw gashes cut across the lower
cover, bony shinigami fingers hook over its top edge, and two red eyes watch from the
dark above. Blood is the only colour.

Returns (image, tint): an LA image whose alpha marks what is drawn and whose luminance
becomes glyph density, and an L mask marking the parts drawn in red.
"""

import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SIZE = (600, 776)
SS = 2
SEED = 666

NOTE = (304, 452, 400, 560, -4)  # cx, cy, width, height, degrees


def _layer() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("L", (SIZE[0] * SS, SIZE[1] * SS), 0)
    return image, ImageDraw.Draw(image)


def _to_note(x: float, y: float) -> tuple[float, float]:
    """A point in the cover's own frame (origin at its centre) to canvas pixels."""
    cx, cy, _, _, deg = NOTE
    a = math.radians(deg)
    return ((cx + x * math.cos(a) - y * math.sin(a)) * SS, (cy + x * math.sin(a) + y * math.cos(a)) * SS)


def _rect(w: float, h: float, dx: float = 0, dy: float = 0) -> list[tuple[float, float]]:
    return [_to_note(dx + x, dy + y) for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]


def _paint(lum, alpha, tint, layer: Image.Image, value: float, red: bool = False, threshold: int = 0) -> None:
    m = np.array(layer) > threshold
    lum[m], alpha[m], tint[m] = value, 1, 1 if red else 0


def _cover(lum, alpha, tint, rng: random.Random) -> None:
    _, _, w, h, _ = NOTE
    pages, draw = _layer()
    draw.polygon(_rect(w - 8, h, 10, 10), fill=255)
    _paint(lum, alpha, tint, pages, 170)

    cover, draw = _layer()
    draw.polygon(_rect(w, h), fill=255)
    _paint(lum, alpha, tint, cover, 22)

    frame, draw = _layer()
    draw.polygon(_rect(w - 34, h - 34), outline=255, width=5 * SS)
    _paint(lum, alpha, tint, frame, 150)
    spine, draw = _layer()
    draw.polygon(_rect(26, h, -w / 2 + 13), fill=255)
    _paint(lum, alpha, tint, spine, 28)


def _title(lum, alpha, tint, font_path: str) -> list[tuple[float, float]]:
    """DEATH over NOTE in heavy serif capitals, big enough to survive being turned into characters.
    Returns the points along the letters' feet where blood starts to run."""
    font = ImageFont.truetype(font_path, 150 * SS)
    try:
        font.set_variation_by_axes([700])
    except OSError:
        pass
    feet = []
    for word, dy in (("DEATH", -150), ("NOTE", 14)):
        text = Image.new("L", (1200 * SS, 300 * SS), 0)
        ImageDraw.Draw(text).text((20 * SS, 20 * SS), word, font=font, fill=255)
        text = text.crop(text.getbbox())
        # Tall and condensed, like the title on the real cover, and big enough per letter
        # to survive being turned into characters.
        target_w = (350 if word == "DEATH" else 290) * SS
        text = text.resize((target_w, 150 * SS), Image.LANCZOS)
        text = text.rotate(-NOTE[4], expand=True, resample=Image.BICUBIC)
        layer = Image.new("L", (SIZE[0] * SS, SIZE[1] * SS), 0)
        cx, cy = _to_note(0, dy)
        layer.paste(text, (int(cx - text.width / 2), int(cy - text.height / 2)))
        _paint(lum, alpha, tint, layer, 250, threshold=110)
        # The lowest inked pixel of each column band is where a drip can start.
        arr = np.array(layer) > 110
        cols = np.where(arr.any(axis=0))[0]
        if word == "DEATH":
            continue  # blood only runs from the lower line, so it never crosses a letter
        for c in cols[:: 9 * SS]:
            rows = np.where(arr[:, c])[0]
            feet.append((c / SS, rows.max() / SS))
    return feet


def _drips(lum, alpha, tint, feet, rng: random.Random) -> None:
    """Blood running from the letters: thin streaks that swell into a drop at the end."""
    image, draw = _layer()
    for x, y in rng.sample(feet, k=min(14, len(feet))):
        length = rng.uniform(30, 120)
        width = rng.uniform(4, 8)
        draw.line([(x * SS, y * SS), (x * SS, (y + length) * SS)], fill=255, width=int(width * SS))
        r = width * 0.95
        draw.ellipse([(x - r) * SS, (y + length - r) * SS, (x + r) * SS, (y + length + r * 1.4) * SS], fill=255)
    _paint(lum, alpha, tint, image, 205, red=True)


def _gashes(lum, alpha, tint) -> None:
    """Four claw marks raked across the lower cover, bleeding at their centres."""
    edges, draw = _layer()
    cores, draw_core = _layer()
    for k in range(4):
        x0, y0 = -150 + k * 34, 150 + k * 16
        x1, y1 = x0 + 230, y0 + 70
        pts = [_to_note(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t + 10 * math.sin(t * math.pi)) for t in np.linspace(0, 1, 30)]
        for i in range(len(pts) - 1):
            t = i / (len(pts) - 1)
            width = 2 + 12 * math.sin(math.pi * t)
            draw.line([pts[i], pts[i + 1]], fill=255, width=int((width + 5) * SS))
            draw_core.line([pts[i], pts[i + 1]], fill=255, width=max(1, int(width * SS)))
    _paint(lum, alpha, tint, edges, 235)
    _paint(lum, alpha, tint, cores, 190, red=True)


def _claw(lum, alpha, tint) -> None:
    """Bony fingers hooked over the top edge, tipped with long claws."""
    image, draw = _layer()
    tips, draw_tip = _layer()
    _, _, w, h, _ = NOTE
    for k, (fx, reach) in enumerate(((56, 70), (96, 92), (136, 86), (174, 62))):
        knuckles = [(fx - 16, -h / 2 - 70), (fx - 6, -h / 2 - 24), (fx + 2, -h / 2 + 8), (fx + 6, -h / 2 + reach * 0.6)]
        pts = [_to_note(x, y) for x, y in knuckles]
        draw.line(pts, fill=255, width=15 * SS, joint="curve")
        for p in pts[1:-1]:
            draw.ellipse([p[0] - 10 * SS, p[1] - 9 * SS, p[0] + 10 * SS, p[1] + 9 * SS], fill=255)
        base = _to_note(fx + 6, -h / 2 + reach * 0.6)
        tip = _to_note(fx + 14, -h / 2 + reach)
        side = _to_note(fx - 2, -h / 2 + reach * 0.6)
        draw_tip.polygon([base, tip, side], fill=255)
        draw_tip.polygon([_to_note(fx + 10, -h / 2 + reach * 0.6), tip, base], fill=255)
    _paint(lum, alpha, tint, image, 175)
    _paint(lum, alpha, tint, tips, 250)


def _eyes(lum, alpha, tint) -> None:
    """Two red eyes in the dark above, watching whoever holds the note."""
    image, draw = _layer()
    for cx, tilt in ((214, 1), (346, -1)):
        cy = 70
        # Narrow and slanted down toward the nose: a glare, not a look.
        pts = [(cx - 52, cy - 10 * tilt), (cx - 10, cy - 20), (cx + 52, cy + 12 * tilt), (cx + 8, cy + 18)]
        if tilt < 0:
            pts = [(2 * cx - x, y) for x, y in pts]
        draw.polygon([(x * SS, y * SS) for x, y in pts], fill=255)
    _paint(lum, alpha, tint, image, 255, red=True)
    pupils, draw = _layer()
    for cx in (214, 346):
        draw.ellipse([(cx - 5) * SS, 54 * SS, (cx + 5) * SS, 88 * SS], fill=255)
    m = np.array(pupils) > 0
    lum[m], alpha[m] = 0, 0


def render(title_font_path: str) -> tuple[Image.Image, Image.Image]:
    rng = random.Random(SEED)
    shape = (SIZE[1] * SS, SIZE[0] * SS)
    lum = np.zeros(shape, np.float32)
    alpha = np.zeros(shape, np.float32)
    tint = np.zeros(shape, np.float32)
    _cover(lum, alpha, tint, rng)
    feet = _title(lum, alpha, tint, title_font_path)
    _drips(lum, alpha, tint, feet, rng)
    _gashes(lum, alpha, tint)
    _claw(lum, alpha, tint)
    _eyes(lum, alpha, tint)

    def image(a: np.ndarray, scale: float) -> Image.Image:
        return Image.fromarray(np.clip(a * scale, 0, 255).astype(np.uint8)).resize(SIZE, Image.LANCZOS)

    la = Image.merge("LA", (image(lum, 1), image(alpha, 255)))
    return la.filter(ImageFilter.SMOOTH), image(tint, 255)


def arrays(title_font_path: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """The same painting as (lum, alpha, tint) float arrays, for ascii_card.render."""
    la, tint = render(title_font_path)
    to = lambda im: np.asarray(im).astype(np.float32) / 255
    return to(la.getchannel("L")), to(la.getchannel("A")), to(tint)
