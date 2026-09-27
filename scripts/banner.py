"""The banner: Tokyo in the rain under a blood moon, and Ryuk watching from a rooftop.

Built for realism rather than illustration: the sky and moon are fractal noise shaped
by SVG filters, the city is two depths of silhouettes with fog between them, and Ryuk
is a backlit silhouette with rim light, not a drawing. Everything moves slowly: clouds
drift, rain falls in two layers, lightning flashes now and then, the note tumbles down
through the rain, and his eyes and wings are never quite still.
"""

import math
import random

from fontpaths import text_path
from pages import INK, MUTED, RED, Fonts, _at, _written

W, H = 1280, 540
BAR = 34
MOON = (905, 196, 132)       # cx, cy, r
LEDGE = (1004, 438)          # where Ryuk crouches: x, roof line
SEED = 1123


# ---- sky -------------------------------------------------------------------------------

def _defs() -> str:
    cx, cy, r = MOON
    return f'''
  <clipPath id="frame"><rect width="{W}" height="{H}" rx="8"/></clipPath>
  <clipPath id="moonClip"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#020103"/><stop offset="0.55" stop-color="#0b0406"/><stop offset="1" stop-color="#1f070a"/>
  </linearGradient>
  <radialGradient id="moonBase" cx="0.42" cy="0.38" r="0.7">
    <stop offset="0" stop-color="#f3a07c"/><stop offset="0.45" stop-color="#c8321f"/><stop offset="0.85" stop-color="#6d0b0c"/><stop offset="1" stop-color="#3a0406"/>
  </radialGradient>
  <radialGradient id="haze"><stop offset="0" stop-color="#ff3b22" stop-opacity="0.34"/><stop offset="0.35" stop-color="#a3111a" stop-opacity="0.14"/><stop offset="1" stop-color="#a3111a" stop-opacity="0"/></radialGradient>
  <radialGradient id="vignette" cx="0.55" cy="0.5" r="0.8"><stop offset="0.5" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.7"/></radialGradient>
  <linearGradient id="shade" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#030102" stop-opacity="0.94"/><stop offset="0.36" stop-color="#030102" stop-opacity="0.72"/><stop offset="0.6" stop-color="#030102" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="fog" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#2a0d10" stop-opacity="0"/><stop offset="0.5" stop-color="#2a0d10" stop-opacity="0.55"/><stop offset="1" stop-color="#2a0d10" stop-opacity="0"/>
  </linearGradient>
  <!-- the moon's surface: mottled maria from low-frequency noise -->
  <filter id="lunar" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.018" numOctaves="5" seed="11" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.12  0 0 0 0 0.01  0 0 0 0 0.02  1.6 0 0 0 -0.62"/>
  </filter>
  <!-- clouds: stretched fractal noise turned into soft, uneven alpha -->
  <filter id="cloudsA" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.0028 0.009" numOctaves="5" seed="4" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.10  0 0 0 0 0.035  0 0 0 0 0.04  2.4 0 0 0 -1.05"/>
  </filter>
  <filter id="cloudsB" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.004 0.014" numOctaves="4" seed="21" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.05  0 0 0 0 0.015  0 0 0 0 0.02  2.6 0 0 0 -1.2"/>
  </filter>
  <linearGradient id="fadeV" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.3" stop-color="#fff"/><stop offset="0.7" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="fadeTop" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#fff"/><stop offset="0.6" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
  </linearGradient>
  <mask id="maskA" maskUnits="userSpaceOnUse" x="-2000" y="0" width="6000" height="330"><rect x="-2000" y="0" width="6000" height="330" fill="url(#fadeTop)"/></mask>
  <mask id="maskB" maskUnits="userSpaceOnUse" x="-2000" y="110" width="6000" height="240"><rect x="-2000" y="110" width="6000" height="240" fill="url(#fadeV)"/></mask>
  <filter id="far" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation="1.4"/></filter>
  <filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="14"/></filter>
  <filter id="glow" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <!-- backlight: a thin red rim around a silhouette, where the moon gets past its edge -->
  <filter id="rim" x="-20%" y="-20%" width="140%" height="140%">
    <feMorphology in="SourceAlpha" operator="dilate" radius="1.1" result="d"/>
    <feComposite in="d" in2="SourceAlpha" operator="out" result="edge"/>
    <feFlood flood-color="#ff5a36" flood-opacity="0.55"/><feComposite in2="edge" operator="in" result="lit"/>
    <feGaussianBlur in="lit" stdDeviation="0.8" result="litb"/>
    <feMerge><feMergeNode in="litb"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="grain" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="5" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 1  0 0 0 0 0.93  0 0 0 0 0.9  0 0 0 0.075 0"/>
  </filter>
  <pattern id="rainFar" width="60" height="120" patternUnits="userSpaceOnUse" patternTransform="rotate(12)">
    <line x1="10" y1="0" x2="10" y2="16" stroke="#b9a7a4" stroke-width="0.8" stroke-opacity="0.22"/>
    <line x1="40" y1="55" x2="40" y2="70" stroke="#b9a7a4" stroke-width="0.8" stroke-opacity="0.18"/>
    <line x1="25" y1="90" x2="25" y2="104" stroke="#b9a7a4" stroke-width="0.7" stroke-opacity="0.2"/>
  </pattern>
  <pattern id="rainNear" width="110" height="220" patternUnits="userSpaceOnUse" patternTransform="rotate(14)">
    <line x1="18" y1="0" x2="18" y2="34" stroke="#d8c8c4" stroke-width="1.3" stroke-opacity="0.3"/>
    <line x1="74" y1="120" x2="74" y2="150" stroke="#d8c8c4" stroke-width="1.1" stroke-opacity="0.26"/>
  </pattern>'''


def _moon() -> str:
    cx, cy, r = MOON
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{r * 3.2:.0f}" fill="url(#haze)">'
        '<animate attributeName="opacity" values="0.85;1;0.85" dur="10s" repeatCount="indefinite"/></circle>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#moonBase)"/>'
        f'<g clip-path="url(#moonClip)"><rect x="{cx - r}" y="{cy - r}" width="{2 * r}" height="{2 * r}" filter="url(#lunar)"/></g>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#ff7a52" stroke-opacity="0.25" stroke-width="3" filter="url(#glow)"/>'
    )


def _clouds() -> str:
    """Two decks drifting at different speeds; the lower one crosses the moon."""
    return (
        f'<g opacity="0.95" mask="url(#maskA)"><g><rect x="-{W}" y="0" width="{W * 3}" height="330" filter="url(#cloudsA)"/>'
        f'<animateTransform attributeName="transform" type="translate" values="0 0;{W} 0" dur="240s" repeatCount="indefinite"/></g></g>'
        f'<g opacity="0.9" mask="url(#maskB)"><g><rect x="-{W}" y="110" width="{W * 3}" height="240" filter="url(#cloudsB)"/>'
        f'<animateTransform attributeName="transform" type="translate" values="0 0;{W} 0" dur="140s" repeatCount="indefinite"/></g></g>'
    )


def _lightning(rng: random.Random) -> str:
    """Rare: the sky whitens twice and a forked bolt stands behind the far towers."""
    x, y = 470.0, 20.0
    pts = [(x, y)]
    while y < 380:
        x += rng.uniform(-22, 22)
        y += rng.uniform(18, 34)
        pts.append((x, y))
    fork = [pts[5]]
    fx, fy = pts[5]
    for _ in range(5):
        fx += rng.uniform(4, 24)
        fy += rng.uniform(16, 28)
        fork.append((fx, fy))
    bolt = "M" + " L".join(f"{a:.0f} {b:.0f}" for a, b in pts)
    branch = "M" + " L".join(f"{a:.0f} {b:.0f}" for a, b in fork)
    kt = "0;0.78;0.785;0.8;0.81;0.83;1"
    return (
        f'<rect width="{W}" height="{H}" fill="#e8dff5" opacity="0">'
        f'<animate attributeName="opacity" values="0;0;0.22;0.04;0.16;0;0" keyTimes="{kt}" dur="13s" repeatCount="indefinite"/></rect>'
        f'<g opacity="0" filter="url(#glow)"><path d="{bolt}" fill="none" stroke="#f4eeff" stroke-width="2.2"/>'
        f'<path d="{branch}" fill="none" stroke="#f4eeff" stroke-width="1.2"/>'
        f'<animate attributeName="opacity" values="0;0;1;0.2;0.9;0;0" keyTimes="{kt}" dur="13s" repeatCount="indefinite"/></g>'
    )


# ---- city ------------------------------------------------------------------------------

def _tower(x: float, base: float, h: float) -> str:
    """Tokyo Tower in the distance: a tapering lattice with two observation decks."""
    top = base - h
    half = lambda t: 38 * (1 - t) ** 1.6 + 2  # half-width at height fraction t
    left = [(x - half(t), base - h * t) for t in (0, 0.25, 0.5, 0.75, 0.95)]
    right = [(x + half(t), base - h * t) for t in (0.95, 0.75, 0.5, 0.25, 0)]
    body = "M" + " L".join(f"{a:.1f} {b:.1f}" for a, b in left + right) + " Z"
    decks = "".join(
        f'<rect x="{x - half(t) - 4:.1f}" y="{base - h * t - 5:.1f}" width="{2 * half(t) + 8:.1f}" height="7"/>'
        for t in (0.34, 0.62)
    )
    lattice = "".join(
        f'<path d="M{x - half(a):.1f} {base - h * a:.1f} L{x + half(b):.1f} {base - h * b:.1f} M{x + half(a):.1f} {base - h * a:.1f} L{x - half(b):.1f} {base - h * b:.1f}" stroke="#1d0d10" stroke-width="1"/>'
        for a, b in ((0, 0.12), (0.12, 0.24), (0.24, 0.34), (0.38, 0.5), (0.5, 0.62))
    )
    return (
        f'<path d="{body}"/>{decks}{lattice}<rect x="{x - 1}" y="{top - 26}" width="2" height="26"/>'
        f'<circle cx="{x}" cy="{top - 26}" r="2.2" fill="#ff2a2a" filter="url(#glow)">'
        '<animate attributeName="opacity" values="1;0.15;1" dur="2.4s" repeatCount="indefinite"/></circle>'
    )


def _buildings(rng: random.Random, x0: float, x1: float, lo: float, hi: float, windows: float, color: str) -> tuple[str, str]:
    shapes, lights = [], []
    x = x0
    while x < x1:
        w = rng.uniform(28, 78)
        top = rng.uniform(lo, hi)
        shapes.append(f'<rect x="{x:.0f}" y="{top:.0f}" width="{w + 1:.0f}" height="{H - top:.0f}"/>')
        if rng.random() < 0.3:
            shapes.append(f'<rect x="{x + w * 0.3:.0f}" y="{top - rng.uniform(8, 18):.0f}" width="{w * 0.35:.0f}" height="20"/>')
        if rng.random() < 0.25:
            ax = x + rng.uniform(6, w - 6)
            shapes.append(f'<rect x="{ax:.0f}" y="{top - 30:.0f}" width="1.4" height="30"/>')
        for wy in range(int(top) + 8, H - BAR, 11):
            for wx in range(int(x) + 5, int(x + w) - 4, 8):
                if rng.random() < windows:
                    warm = rng.choice(("#e0a45a", "#d98b4a", "#c9c2b0", "#b04a3a"))
                    lights.append(f'<rect x="{wx}" y="{wy}" width="3" height="5" fill="{warm}" opacity="{rng.uniform(0.25, 0.75):.2f}"/>')
        x += w + rng.uniform(0, 6)
    return f'<g fill="{color}">{"".join(shapes)}</g>', "".join(lights)


def _city(rng: random.Random) -> str:
    far, far_lights = _buildings(rng, -10, W + 10, 318, 392, 0.05, "#14080b")
    near, near_lights = _buildings(rng, -10, 880, 400, 452, 0.035, "#050203")
    lx, ly = LEDGE
    roof = (
        f'<rect x="880" y="{ly}" width="{W - 880}" height="{H - ly}"/>'
        f'<rect x="{lx - 70}" y="{ly - 6}" width="170" height="7"/>'
        f'<rect x="1150" y="{ly - 58}" width="46" height="58"/><rect x="1146" y="{ly - 64}" width="54" height="8"/>'
        f'<rect x="1210" y="{ly - 120}" width="2" height="120"/><rect x="1196" y="{ly - 96}" width="30" height="2"/>'
    )
    beacon = (
        f'<circle cx="1211" cy="{ly - 122}" r="2.6" fill="#ff2020" filter="url(#glow)">'
        '<animate attributeName="opacity" values="1;1;0.08;0.08" keyTimes="0;0.45;0.5;1" dur="1.8s" repeatCount="indefinite"/></circle>'
    )
    flicker = (
        f'<rect x="1162" y="{ly - 44}" width="4" height="7" fill="#e0a45a" opacity="0.7">'
        '<animate attributeName="opacity" values="0.7;0.7;0.1;0.7;0.7" keyTimes="0;0.6;0.62;0.64;1" dur="7s" repeatCount="indefinite"/></rect>'
    )
    return (
        f'<g filter="url(#far)"><g fill="#14080b">{_tower(610, 400, 250)}</g>{far}{far_lights}</g>'
        f'<rect x="0" y="330" width="{W}" height="120" fill="url(#fog)" filter="url(#soft)">'
        '<animateTransform attributeName="transform" type="translate" values="-40 0;40 0;-40 0" dur="60s" repeatCount="indefinite"/></rect>'
        f'{near}{near_lights}<g fill="#040102">{roof}</g>{beacon}{flicker}'
    )


# ---- Ryuk ------------------------------------------------------------------------------

def _spiky(rng: random.Random, cx: float, cy: float, base: float, spikes: int, lo: float, hi: float,
           start: float, end: float) -> str:
    pts = []
    for i in range(spikes * 2 + 1):
        a = math.radians(start + (end - start) * i / (spikes * 2))
        r = base if i % 2 == 0 else base + rng.uniform(lo, hi)
        a += rng.uniform(-0.04, 0.04) if i % 2 else 0
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + " Z"


def _wing(rng: random.Random, side: int) -> str:
    """A ragged, feathered wing: a bony leading edge and long primaries hanging from it."""
    sx, sy = 18 * side, -208
    tip = (158 * side, -312)
    lead = [(sx, sy), (58 * side, -258), (112 * side, -294), tip]
    feathers = []
    n = 26
    for i in range(n + 1):
        t = i / n
        # along the leading edge, from shoulder to tip
        px = sx + (tip[0] - sx) * t
        py = sy + (tip[1] - sy) * t - 40 * math.sin(math.pi * t)
        length = 46 + 84 * math.sin(math.pi * min(1, t * 1.05)) ** 0.7 + rng.uniform(-10, 10)
        ang = math.radians(90 - side * (8 + 34 * t) + rng.uniform(-4, 4))
        fx, fy = px + length * math.cos(ang), py + length * math.sin(ang)
        feathers.append((fx, fy))
    edge = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in lead)
    trail = " L".join(f"{x:.1f} {y:.1f}" for x, y in reversed(feathers))
    # between each pair of feather tips, cut back up toward the wing so the edge is ragged
    ragged = []
    rev = list(reversed(feathers))
    for i, (x, y) in enumerate(rev):
        ragged.append(f"{x:.1f} {y:.1f}")
        if i < len(rev) - 1:
            nx, ny = rev[i + 1]
            ragged.append(f"{(x + nx) / 2 + side * 3:.1f} {(y + ny) / 2 - rng.uniform(14, 30):.1f}")
    return edge + " L" + " L".join(ragged) + f" L{sx} {sy + 70} Z"


def _ryuk(rng: random.Random) -> str:
    """Standing tall and hunched on the ledge, wings drooping, an apple held up by his head.
    A pure silhouette against the moon: only the rim light, his eyes and the apple show."""
    lx, ly = LEDGE
    hair = _spiky(rng, 0, -246, 17, 19, 20, 50, 0, 360)
    collar = _spiky(rng, 0, -212, 26, 16, 7, 18, 160, 380)
    half = [(-7, -226), (-30, -214), (-27, -184), (-21, -146), (-16, -120), (-24, -104), (-27, -70), (-23, -50),
            (-21, -14), (-19, -5), (-36, 2), (-8, 2), (-8, -6), (-10, -48), (-9, -60), (-4, -96)]
    body = "M" + " L".join(f"{x} {y}" for x, y in half + [(-x, y) for x, y in reversed(half)]) + " Z"
    arm_l = "M-28 -210 C-44 -186 -48 -160 -46 -134 C-44 -112 -48 -96 -52 -84"
    arm_r = "M28 -210 C52 -200 60 -176 54 -160 C50 -148 46 -150 40 -238"
    claws = "M-52 -84 L-58 -72 M-52 -84 L-52 -70 M-52 -84 L-46 -72"
    breathe = lambda side: (
        f'<animateTransform attributeName="transform" type="rotate" values="0 {18 * side} -208;{-5 * side} {18 * side} -208;0 {18 * side} -208" '
        'dur="7s" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.5;1" keySplines="0.45 0 0.55 1;0.45 0 0.55 1"/>'
    )
    eyes = "".join(
        f'<ellipse cx="{x}" cy="-244" rx="3.2" ry="2" transform="rotate({14 * s} {x} -244)" fill="#ffcf5a" filter="url(#glow)">'
        '<animate attributeName="ry" values="2;2;0.2;2;2" keyTimes="0;0.92;0.94;0.96;1" dur="8s" repeatCount="indefinite"/></ellipse>'
        f'<circle cx="{x}" cy="-244" r="1" fill="#b3120f"/>'
        for x, s in ((-7, 1), (7, -1))
    )
    apple = (
        '<g transform="translate(40 -247)"><circle r="8" fill="#7d0a10"/>'
        '<circle cx="-2.6" cy="-2.8" r="2.6" fill="#ff6a50" opacity="0.5"/><path d="M0 -7.5 Q1 -12 3.5 -13" stroke="#040102" stroke-width="1.4" fill="none"/></g>'
    )
    silhouette = "#020102"
    return f'''
<g transform="translate({lx} {ly - 4}) scale(1.0)">
  <g filter="url(#rim)" fill="{silhouette}">
    <path d="{_wing(rng, -1)}">{breathe(-1)}</path>
    <path d="{_wing(rng, 1)}">{breathe(1)}</path>
    <path d="{body}"/>
    <path d="{collar}"/>
    <path d="{hair}"/>
    <g fill="none" stroke="{silhouette}" stroke-linecap="round"><path d="{arm_l}" stroke-width="8"/><path d="{arm_r}" stroke-width="8"/><path d="{claws}" stroke-width="2.2"/></g>
  </g>
  {apple}{eyes}
  <animateTransform attributeName="transform" type="translate" additive="sum" values="0 0;0 -2;0 0" dur="6s" repeatCount="indefinite"/>
</g>'''


# ---- falling things --------------------------------------------------------------------

def _note(f: Fonts) -> str:
    title = text_path(f.gothic, "DEATH NOTE", 7, tracking=0.06)
    cover = (
        '<rect x="-17" y="-24" width="34" height="48" rx="1.5" fill="#070404" stroke="#6b5c56" stroke-width="0.8"/>'
        '<rect x="15" y="-22" width="3" height="45" fill="#bcae98"/>'
        + _at(title, -title.width / 2 + 1, -12, "#d8cdbd")
    )
    return f'''
<g opacity="0">
  <animate attributeName="opacity" values="0;0.95;0.95;0;0" keyTimes="0;0.05;0.52;0.58;1" dur="17s" begin="3s" repeatCount="indefinite"/>
  <g><animateTransform attributeName="transform" type="translate" values="700 -50;760 {H + 40};760 {H + 40}" keyTimes="0;0.58;1" dur="17s" begin="3s" repeatCount="indefinite"/>
    <g>{cover}<animateTransform attributeName="transform" type="rotate" values="-30;160;330" keyTimes="0;0.58;1" dur="17s" begin="3s" repeatCount="indefinite"/></g>
  </g>
</g>'''


def _feathers(rng: random.Random) -> str:
    shape = "M0 -14 C5 -8 5 6 0 14 C-5 6 -5 -8 0 -14 Z"
    out = []
    for _ in range(6):
        x, dur = rng.uniform(760, 1240), rng.uniform(15, 24)
        begin, sway = -rng.uniform(0, dur), rng.uniform(20, 44)
        out.append(
            f'<g><animateTransform attributeName="transform" type="translate" values="{x:.0f} -30;{x + sway:.0f} 180;{x - sway:.0f} 360;{x:.0f} {H + 30}" dur="{dur:.1f}s" begin="{begin:.1f}s" repeatCount="indefinite"/>'
            f'<path d="{shape}" fill="#080405" stroke="#ff5a36" stroke-opacity="0.25" stroke-width="0.6" transform="scale({rng.uniform(0.45, 0.8):.2f})">'
            f'<animateTransform attributeName="transform" type="rotate" additive="sum" values="-40;40;-40" dur="{dur / 3:.1f}s" begin="{begin:.1f}s" repeatCount="indefinite"/></path></g>'
        )
    return "".join(out)


def _rain() -> str:
    return (
        f'<g><rect x="-200" y="-{H}" width="{W + 400}" height="{H * 3}" fill="url(#rainFar)"/>'
        f'<animateTransform attributeName="transform" type="translate" values="0 0;-26 120" dur="0.9s" repeatCount="indefinite"/></g>'
        f'<g><rect x="-200" y="-{H}" width="{W + 400}" height="{H * 3}" fill="url(#rainNear)"/>'
        f'<animateTransform attributeName="transform" type="translate" values="0 0;-55 220" dur="0.55s" repeatCount="indefinite"/></g>'
    )


# ---- type ------------------------------------------------------------------------------

def _type(f: Fonts) -> str:
    x = 64
    label = text_path(f.mono, "APS COLLEGE OF ENGINEERING  ·  B.E. CSE", 14, tracking=0.3)
    name = text_path(f.gothic, "Likith Lochan", 112)
    role = text_path(f.serif_bold, "DevOps  ·  Backend/Full-Stack  ·  Applied AI", 31)
    quote = text_path(f.italic, "“The incident whose name is written here shall be resolved.”", 26)
    top_l = text_path(f.mono, "DEATH NOTE", 13, tracking=0.4)
    top_r = text_path(f.mono, "EP.01  ·  REBIRTH", 13, tracking=0.3)
    kanji = text_path(f.brush, "新生", 18)
    bot = text_path(f.mono, "TOKYO  ·  02:14  ·  RAIN", 12, tracking=0.3)
    return (
        _at(label, x, 160, MUTED) + _written(name, x, 276, INK, 0.3, 2.6)
        + f'<rect x="{x}" y="306" width="150" height="3" fill="{RED}"/>'
        + _at(role, x, 360, INK) + _at(quote, x, 406, MUTED)
        + f'<rect width="{W}" height="{BAR}" fill="#000"/><rect y="{H - BAR}" width="{W}" height="{BAR}" fill="#000"/>'
        + _at(top_l, 24, 22, MUTED) + _at(top_r, W - 24 - top_r.width, 22, MUTED)
        + _at(kanji, W - 24 - top_r.width - 12 - kanji.width, 25, RED)
        + _at(bot, 24, H - 12, "#4a3f3b")
    )


def render(f: Fonts) -> str:
    rng = random.Random(SEED)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Likith Lochan. DevOps, Backend/Full-Stack, Applied AI. Tokyo at night in the rain under a blood moon, Ryuk watching from a rooftop as the Death Note falls.">
<defs>{_defs()}</defs>
<g clip-path="url(#frame)">
  <rect width="{W}" height="{H}" fill="url(#sky)"/>
  {_moon()}
  {_clouds()}
  {_lightning(rng)}
  {_city(rng)}
  {_note(f)}
  {_ryuk(rng)}
  {_feathers(rng)}
  {_rain()}
  <rect width="{W}" height="{H}" fill="url(#vignette)"/>
  <rect width="{W}" height="{H}" fill="url(#shade)"/>
  <rect width="{W}" height="{H}" filter="url(#grain)"/>
  {_type(f)}
</g>
</svg>'''
