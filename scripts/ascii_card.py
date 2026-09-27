"""ASCII art card: tonal, edge-aware glyphs, revealed top to bottom, with something wrong in it.

The source is painted in code (ryuk.py). Bright areas get dense glyphs; strong contours
get strokes that follow the edge; the tint mask picks the cells drawn in blood red.
Those red cells pulse, and every few seconds the whole face jolts like a bad signal.
"""

from html import escape

import cv2
import numpy as np

from fontpaths import text_path
from pages import INK, FAINT, HALF, MUTED, PAD, RED, Fonts, _at, _frame, _svg

HEIGHT = 1000
TOP = 76
COLS, ROWS = 110, 74
CELL_W, CELL_H = 6.9, 11.4
FONT_SIZE = 11
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"
RAMP = " .,:;-=+*#%@"
EDGE_THRESHOLD = 0.24
EDGE_GLYPHS = ("-", "/", "|", "\\")
TONES = 8
REVEAL = 3.4


def _mix(a: str, b: str, t: float) -> str:
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb))


def _cells(lum: np.ndarray, alpha: np.ndarray, tint: np.ndarray):
    """Per cell: (glyph, tone index, red?) or None for blank."""
    matted = cv2.GaussianBlur(lum * alpha, (0, 0), 1.6)
    gx = cv2.Sobel(matted, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(matted, cv2.CV_32F, 0, 1, ksize=3)
    size, area = (COLS, ROWS), cv2.INTER_AREA
    cgx, cgy = cv2.resize(gx, size, interpolation=area), cv2.resize(gy, size, interpolation=area)
    strength = np.hypot(cgx, cgy)
    strength /= np.percentile(strength, 99) or 1
    angle = (np.degrees(np.arctan2(-cgy, cgx)) + 90) % 180
    l = cv2.resize(lum, size, interpolation=area)
    a = cv2.resize(alpha, size, interpolation=area)
    t = cv2.resize(tint, size, interpolation=area)
    rows = []
    for y in range(ROWS):
        row = []
        for x in range(COLS):
            v = float(np.clip(l[y, x], 0, 1))
            if a[y, x] < 0.5 or v < 0.06:
                row.append(None)
                continue
            red = t[y, x] > 0.45
            if strength[y, x] > EDGE_THRESHOLD and v < 0.8:
                row.append((EDGE_GLYPHS[int(((angle[y, x] + 22.5) % 180) // 45)], TONES - 1, red))
            else:
                row.append((RAMP[1 + round(v * (len(RAMP) - 2))], min(TONES - 1, int(v * TONES)), red))
        rows.append(row)
    return rows


def _row(cells, y: float, x0: float, ink: list[str], want_red: bool) -> str:
    """One <text> per row for the ink glyphs or the red glyphs; the other kind is left as spaces."""
    runs, cur, fill = [], "", None
    for cell in cells:
        if cell is None or cell[2] != want_red:
            cur += " "
            continue
        glyph, tone, _ = cell
        colour = RED if want_red else ink[tone]
        if fill is not None and colour != fill:
            runs.append((cur, fill))
            cur = ""
        cur += glyph
        fill = colour
    if not cur.strip() and not runs:
        return ""
    runs.append((cur, fill or "none"))
    spans = "".join(f'<tspan fill="{f}">{escape(s)}</tspan>' for s, f in runs)
    return (
        f'<text x="{x0:.1f}" y="{y:.1f}" textLength="{COLS * CELL_W:.1f}" lengthAdjust="spacing" '
        f'xml:space="preserve">{spans}</text>'
    )


def _countdown(f: Fonts, y: float) -> str:
    """Rule: death by heart attack, forty seconds after the name is written. A timer counts
    40 down to 0, one second at a time, then the card flashes DEAD, and it starts again."""
    total = 44
    frames = []
    for n in range(41):
        label = text_path(f.mono, f"00:{40 - n:02d}", 30, tracking=0.12)
        frames.append(
            f'<g opacity="{1 if n == 0 else 0}">' + _at(label, (HALF - label.width) / 2, y, RED if n > 30 else INK)
            + f'<animate attributeName="opacity" calcMode="discrete" values="0;1;0" keyTimes="0;{n / total:.4f};{(n + 1) / total:.4f}" dur="{total}s" repeatCount="indefinite"/></g>'
        )
    dead = text_path(f.gothic, "DEAD", 44, tracking=0.2)
    frames.append(
        '<g opacity="0">' + _at(dead, (HALF - dead.width) / 2, y + 6, RED)
        + f'<animate attributeName="opacity" calcMode="discrete" values="0;1;0;1;0;1" keyTimes="0;{41 / total:.4f};{41.5 / total:.4f};{42 / total:.4f};{42.5 / total:.4f};{43 / total:.4f}" dur="{total}s" repeatCount="indefinite"/></g>'
        f'<rect x="4" y="60" width="{HALF - 8}" height="{HEIGHT - 110}" fill="{RED}" opacity="0">'
        f'<animate attributeName="opacity" calcMode="discrete" values="0;0.18;0;0.12;0" keyTimes="0;{41 / total:.4f};{41.3 / total:.4f};{42 / total:.4f};{42.3 / total:.4f}" dur="{total}s" repeatCount="indefinite"/></rect>'
    )
    note = text_path(f.mono, "HEART ATTACK IN", 12, tracking=0.35)
    return _at(note, (HALF - note.width) / 2, y - 42, MUTED) + "".join(frames)


def render(f: Fonts, lum: np.ndarray, alpha: np.ndarray, tint: np.ndarray, title: str, caption: str,
           label: str, countdown: bool = False) -> str:
    ink = [_mix(FAINT, INK, (i / (TONES - 1)) ** 0.85) for i in range(TONES)]
    cells = _cells(lum, alpha, tint)
    glyphs = sum(1 for row in cells for c in row if c)
    x0 = (HALF - COLS * CELL_W) / 2
    ys = [TOP + 16 + (i + 0.8) * CELL_H for i in range(ROWS)]
    ink_rows = "".join(_row(r, y, x0, ink, False) for r, y in zip(cells, ys))
    red_rows = "".join(_row(r, y, x0, ink, True) for r, y in zip(cells, ys))
    art_top, art_bottom = TOP, TOP + 16 + ROWS * CELL_H
    caption = text_path(f.mono, caption, 13, tracking=0.08)
    count = text_path(f.mono, f"{glyphs:,} glyphs", 13, tracking=0.08)
    glitch = (
        '<animateTransform attributeName="transform" type="translate" '
        'values="0 0;0 0;-7 0;5 0;0 0;0 0" keyTimes="0;0.86;0.87;0.885;0.9;1" dur="6.5s" repeatCount="indefinite"/>'
        '<animate attributeName="opacity" values="1;1;0.35;1;0.6;1;1" keyTimes="0;0.86;0.87;0.88;0.89;0.9;1" dur="6.5s" repeatCount="indefinite"/>'
    )
    body = (
        _frame(HALF, HEIGHT, title, f"{COLS}×{ROWS}", f)
        + f'<defs><linearGradient id="curtain" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="#0e0b0b" stop-opacity="0"/><stop offset="0.06" stop-color="#0e0b0b"/><stop offset="1" stop-color="#0e0b0b"/></linearGradient></defs>'
        f'<g font-family="{MONO}" font-size="{FONT_SIZE}">{glitch}'
        f'<g>{ink_rows}</g>'
        f'<g>{red_rows}<animate attributeName="opacity" values="1;0.35;1" dur="2.6s" repeatCount="indefinite"/></g></g>'
        f'<g transform="translate(0 {HEIGHT})"><rect x="4" y="0" width="{HALF - 8}" height="{art_bottom - art_top + 90:.0f}" fill="url(#curtain)"/>'
        f'<rect x="{PAD}" y="12" width="{HALF - 2 * PAD}" height="2" fill="{RED}" opacity="0.85"/>'
        f'<animateTransform attributeName="transform" type="translate" values="0 {art_top - 40};0 {HEIGHT}" dur="{REVEAL}s" fill="freeze" '
        'calcMode="spline" keyTimes="0;1" keySplines="0.45 0 0.25 1"/></g>'
        f'<line x1="{PAD}" y1="{HEIGHT - 46}" x2="{HALF - PAD}" y2="{HEIGHT - 46}" stroke="#221a1a" stroke-width="1.5"/>'
        + _at(caption, PAD, HEIGHT - 20, MUTED) + _at(count, HALF - PAD - count.width, HEIGHT - 20, MUTED)
        + (_countdown(f, 150) if countdown else "")
    )
    return _svg(HALF, HEIGHT, label, body)
