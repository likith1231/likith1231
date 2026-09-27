"""The banner: a cinematic poster with the name set on it.

    python scripts/poster.py                          # typographic poster, no artwork
    python scripts/poster.py --backdrop art.jpg       # bake an anime key visual behind it
    python scripts/poster.py --backdrop art.jpg --focus 0.7   # 0 = keep the left, 1 = the right

The backdrop is graded (crushed blacks, colour drained except the reds, vignette) and
embedded inside assets/banner.svg, so no separate image file is kept. Motion is slow on
purpose: a push-in over 24 seconds, a faint red flicker, embers drifting up.
"""

import argparse
import base64
import io
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import load_fonts  # noqa: E402
from fontpaths import text_path  # noqa: E402
from pages import INK, MUTED, RED, _at, _written  # noqa: E402

W, H = 1280, 520
BAR = 34
ASSET = Path(__file__).resolve().parent.parent / "assets" / "banner.svg"


def grade(path: Path, focus: float) -> str:
    """Crop to the banner (with room for the push-in), grade it, return a JPEG data URI."""
    img = Image.open(path).convert("RGB")
    tw, th = int(W * 1.08), int(H * 1.08)
    s = max(tw / img.width, th / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    x = round((img.width - tw) * focus)
    y = round((img.height - th) / 2)
    img = img.crop((x, y, x + tw, y + th))
    a = np.asarray(img).astype(np.float32) / 255
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    red = np.clip((r - np.maximum(g, b)) * 3.2, 0, 1)[..., None]
    x_ = lum[..., None] + (a - lum[..., None]) * (0.2 + 1.1 * red)
    x_ = np.clip((x_ - 0.06) / 0.9, 0, 1)
    x_ = x_ * x_ * (3 - 2 * x_) * 0.7 + x_ * 0.3
    x_ = x_ + ((1 - lum[..., None]) ** 2) * np.array([0.05, -0.012, -0.008], np.float32)
    hh, ww = lum.shape
    yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)
    v = 1 - 0.5 * (((xx / ww - 0.55) / 0.6) ** 2 + ((yy / hh - 0.5) / 0.75) ** 2)
    x_ = x_ * np.clip(v, 0.3, 1)[..., None]
    out = Image.fromarray((np.clip(x_, 0, 1) * 255).astype(np.uint8))
    buf = io.BytesIO()
    out.save(buf, "JPEG", quality=84, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def embers(rng: random.Random) -> str:
    out = []
    for _ in range(26):
        x, y = rng.uniform(420, W - 20), rng.uniform(H - 140, H - BAR)
        rise, drift, dur = rng.uniform(140, 300), rng.uniform(-40, 40), rng.uniform(9, 16)
        begin = -rng.uniform(0, dur)
        out.append(
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rng.choice((0.9, 1.3, 1.7))}" fill="#ff5a3c" opacity="0">'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;{drift:.0f} {-rise:.0f}" dur="{dur:.1f}s" begin="{begin:.1f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0;0.85;0" dur="{dur:.1f}s" begin="{begin:.1f}s" repeatCount="indefinite"/></circle>'
        )
    return f'<g filter="url(#glow)">{"".join(out)}</g>'


def render(backdrop: str | None) -> str:
    f = load_fonts()
    rng = random.Random(9)
    if backdrop:
        art = (
            f'<image href="{backdrop}" x="{-W * 0.04:.0f}" y="{-H * 0.04:.0f}" width="{W * 1.08:.0f}" height="{H * 1.08:.0f}" preserveAspectRatio="xMidYMid slice">'
            f'<animateTransform attributeName="transform" type="scale" values="1;1.045;1" dur="24s" repeatCount="indefinite" '
            f'calcMode="spline" keyTimes="0;0.5;1" keySplines="0.45 0 0.55 1;0.45 0 0.55 1" additive="sum"/></image>'
        )
    else:
        letter = text_path(f.old_english, "L", 620)
        art = (
            f'<circle cx="930" cy="250" r="330" fill="url(#moon)"/>'
            + _at(letter, 1010 - letter.width / 2, 610, INK, ' opacity="0.06"')
        )
    label = text_path(f.mono, "APS COLLEGE OF ENGINEERING  ·  B.E. CSE", 14, tracking=0.3)
    name = text_path(f.gothic, "Likith Lochan", 112)
    role = text_path(f.serif_bold, "DevOps  ·  Backend/Full-Stack  ·  Applied AI", 32)
    quote = text_path(f.italic, "“The incident whose name is written here shall be resolved.”", 27)
    top_l = text_path(f.mono, "DEATH NOTE", 13, tracking=0.4)
    top_r = text_path(f.mono, "EP.01  ·  REBIRTH", 13, tracking=0.3)
    kanji = text_path(f.brush, "新生", 18)
    x = 64
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Likith Lochan. DevOps, Backend/Full-Stack, Applied AI. A Death Note poster.">
<defs>
  <clipPath id="frame"><rect width="{W}" height="{H}" rx="8"/></clipPath>
  <linearGradient id="shade" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#050303" stop-opacity="0.96"/><stop offset="0.42" stop-color="#050303" stop-opacity="0.78"/>
    <stop offset="0.72" stop-color="#050303" stop-opacity="0.1"/><stop offset="1" stop-color="#050303" stop-opacity="0"/>
  </linearGradient>
  <radialGradient id="moon" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#8e1119" stop-opacity="0.55"/><stop offset="1" stop-color="#8e1119" stop-opacity="0"/></radialGradient>
  <filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <filter id="grain" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="5" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 1  0 0 0 0 0.92  0 0 0 0 0.88  0 0 0 0.07 0"/>
  </filter>
</defs>
<g clip-path="url(#frame)">
  <rect width="{W}" height="{H}" fill="#070404"/>
  {art}
  <rect width="{W}" height="{H}" fill="#b0101a" opacity="0">
    <animate attributeName="opacity" values="0;0;0.14;0;0.08;0;0" keyTimes="0;0.7;0.72;0.75;0.77;0.8;1" dur="9s" repeatCount="indefinite"/>
  </rect>
  <rect width="{W}" height="{H}" fill="url(#shade)"/>
  {embers(rng)}
  <rect width="{W}" height="{H}" filter="url(#grain)"/>
  {_at(label, x, 150, MUTED)}
  {_written(name, x, 266, INK, 0.3, 2.6)}
  <rect x="{x}" y="296" width="150" height="3" fill="{RED}"/>
  {_at(role, x, 352, INK)}
  {_at(quote, x, 400, MUTED)}
  <rect width="{W}" height="{BAR}" fill="#000"/><rect y="{H - BAR}" width="{W}" height="{BAR}" fill="#000"/>
  {_at(top_l, 24, 22, MUTED)}
  {_at(top_r, W - 24 - top_r.width, 22, MUTED)}
  {_at(kanji, W - 24 - top_r.width - 12 - kanji.width, 25, RED)}
</g>
</svg>'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backdrop", type=Path)
    parser.add_argument("--focus", type=float, default=0.65)
    args = parser.parse_args()
    backdrop = grade(args.backdrop, args.focus) if args.backdrop else None
    ASSET.parent.mkdir(exist_ok=True)
    ASSET.write_text(render(backdrop), encoding="utf-8")
    print(f"wrote {ASSET} ({ASSET.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
