"""ASCII art card: tonal, edge-aware glyphs over a cleared background, revealed as if written.

The source is painted in code (apple.py). A tint mask picks which cells are drawn in
the apple's red instead of ink.
"""

from dataclasses import dataclass
from html import escape

import cv2
import numpy as np
from PIL import Image

from theme import MONO, Theme, mix

WIDTH, HEIGHT = 860, 1000
TITLE_H = 48
COLS, ROWS = 110, 74
CELL_W, CELL_H = 6.3, 12.0
FONT_SIZE = 10.5
# Sparse to dense. Bright areas of the source get dense glyphs.
RAMP = " .,:;-=+*#%@"
# Where the source has a strong contour, draw it with a stroke that follows the edge.
EDGE_THRESHOLD = 0.22
EDGE_GLYPHS = ("-", "/", "|", "\\")  # edge runs horizontal, rising, vertical, falling
TONES = 8
ALPHA_CUTOFF = 0.5
BLANK_BELOW = 0.07
REVEAL_SECONDS = 3.2


@dataclass(frozen=True)
class Art:
    image: Image.Image  # LA: luminance becomes density, alpha marks what is drawn
    tint: Image.Image   # L: where to draw in the apple's red
    title: str
    caption: str
    label: str


def _sample(image: Image.Image) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Per character cell: luminance, coverage, edge strength and edge angle."""
    image = image.convert("LA")
    lum = np.array(image.getchannel("L"))
    alpha = np.array(image.getchannel("A")).astype(np.float32) / 255

    # Gradients of the art composited on black, so outer outlines count as edges too.
    matted = (lum.astype(np.float32) / 255) * alpha
    matted = cv2.GaussianBlur(matted, (0, 0), 1.6)
    gx = cv2.Sobel(matted, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(matted, cv2.CV_32F, 0, 1, ksize=3)

    size = (COLS, ROWS)
    area = cv2.INTER_AREA
    cell_gx = cv2.resize(gx, size, interpolation=area)
    cell_gy = cv2.resize(gy, size, interpolation=area)
    strength = np.hypot(cell_gx, cell_gy)
    strength = strength / (np.percentile(strength, 99) or 1)
    # The edge runs perpendicular to the gradient. Screen y points down, hence -gy.
    angle = (np.degrees(np.arctan2(-cell_gy, cell_gx)) + 90) % 180

    lum_grid = cv2.resize(lum, size, interpolation=area).astype(np.float32) / 255
    alpha_grid = cv2.resize(alpha, size, interpolation=area)
    return lum_grid, alpha_grid, strength, angle


def _edge_glyph(angle: float) -> str:
    return EDGE_GLYPHS[int(((angle + 22.5) % 180) // 45)]


Cell = tuple[str, str | None]  # (glyph, fill); fill is None for blank cells


def _cells(art: Art, ink: list[str], red: list[str]) -> list[list[Cell]]:
    """Dense glyphs and strong tones where the art is bright; red where the tint mask says so."""
    lum, alpha, strength, angle = _sample(art.image)
    tint = cv2.resize(np.array(art.tint.convert("L")), (COLS, ROWS), interpolation=cv2.INTER_AREA) / 255
    rows = []
    for y in range(ROWS):
        row: list[Cell] = []
        for x in range(COLS):
            t = float(np.clip(lum[y, x], 0, 1))
            if alpha[y, x] < ALPHA_CUTOFF or t < BLANK_BELOW:
                row.append((" ", None))
                continue
            palette = red if tint[y, x] > 0.5 else ink
            if strength[y, x] > EDGE_THRESHOLD and t < 0.8:
                row.append((_edge_glyph(angle[y, x]), palette[-1]))
                continue
            glyph = RAMP[1 + round(t * (len(RAMP) - 2))]
            row.append((glyph, palette[min(TONES - 1, int(t * TONES))]))
        rows.append(row)
    return rows


def _row_svg(row: list[Cell], y: float, x0: float) -> str:
    """One <text> per row, with a <tspan> per run of one colour to keep the file small."""
    runs: list[tuple[str, str]] = []
    current, fill = "", None
    for glyph, cell_fill in row:
        if cell_fill is not None and fill is not None and cell_fill != fill:
            runs.append((current, fill))
            current = ""
        current += glyph  # spaces join whatever run they sit in
        fill = cell_fill or fill
    runs.append((current, fill or "none"))
    spans = "".join(f'<tspan fill="{f}">{escape(text)}</tspan>' for text, f in runs)
    return (
        f'<text x="{x0:.1f}" y="{y:.1f}" textLength="{COLS * CELL_W:.1f}" '
        f'lengthAdjust="spacing" xml:space="preserve">{spans}</text>'
    )


def render(theme: Theme, art: Art, frame: str) -> str:
    ink = [mix(theme.faint, theme.ink, (i / (TONES - 1)) ** 0.85) for i in range(TONES)]
    red_floor = mix(theme.surface, theme.apple, 0.35)
    red = [mix(red_floor, theme.apple, (i / (TONES - 1)) ** 0.8) for i in range(TONES)]
    cells = _cells(art, ink, red)
    glyph_count = sum(1 for row in cells for glyph, _ in row if glyph != " ")

    art_w, art_h = COLS * CELL_W, ROWS * CELL_H
    x0 = (WIDTH - art_w) / 2
    top = TITLE_H + 22
    rows_svg = "".join(_row_svg(row, top + (i + 0.78) * CELL_H, x0) for i, row in enumerate(cells))
    start, end = top - 60, HEIGHT
    spline = 'calcMode="spline" keySplines="0.45 0 0.25 1" keyTimes="0;1"'

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="{escape(art.label)}">
<defs>
  <!-- A curtain in the card's own colour, soft at its top edge, that slides down off the art
       with a line of red ink at its edge. It rests below the card, so the art stays visible
       wherever SMIL doesn't run. -->
  <linearGradient id="curtain" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{theme.surface}" stop-opacity="0"/><stop offset="0.08" stop-color="{theme.surface}"/>
    <stop offset="1" stop-color="{theme.surface}"/>
  </linearGradient>
</defs>
{frame}
<g font-family="{MONO}" font-size="{FONT_SIZE}">{rows_svg}</g>
<g transform="translate(0 {end})">
  <rect x="4" y="0" width="{WIDTH - 8}" height="{art_h + 90:.1f}" fill="url(#curtain)"/>
  <rect x="40" y="10" width="{WIDTH - 80}" height="1.6" fill="{theme.accent}" opacity="0.8"/>
  <animateTransform attributeName="transform" type="translate" values="0 {start:.1f};0 {end}" dur="{REVEAL_SECONDS}s" fill="freeze" {spline}/>
</g>
<line x1="22" y1="{HEIGHT - 44}" x2="{WIDTH - 22}" y2="{HEIGHT - 44}" stroke="{theme.frame}" stroke-width="1.5" opacity="0.5"/>
<text x="22" y="{HEIGHT - 18}" font-family="{MONO}" font-size="12" fill="{theme.muted}">{escape(art.caption)}</text>
<text x="{WIDTH - 22}" y="{HEIGHT - 18}" font-family="{MONO}" font-size="12" fill="{theme.muted}" text-anchor="end">{glyph_count:,} glyphs</text>
</svg>'''
