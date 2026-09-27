"""The header, drawn as a manga page: four slanted panels with screentone and speed lines.

  1. The name, under concentration lines, written in stroke by stroke like a name
     going into the note.
  2. Ryuk in close-up against a red moon: spiked hair, yellow eyes, the grin, and his
     line from the first episode in a vertical speech balloon.
  3. L's calling card: the Old English "L" glowing on a monitor in a dark room.
  4. The Death Note falling out of the shinigami realm, speed lines rushing past it.

Original vector art, not frames from the show. Motion stays slow so the page reads as
still at a glance and alive if you keep looking.
"""

import math
import random
from dataclasses import dataclass

from fontpaths import FontRef, Shaped, text_path, vertical_path

W, H = 1280, 440
SEED = 13
GUTTER = 12

INK = "#050405"
BLOOD = "#e0303a"
EMBER = "#ff5a3c"
PAPER = "#efe6d8"
BONE = "#d9cfbf"
SKIN = ("#aab2bf", "#7d8694", "#4c5360")  # Ryuk: lit, mid, cel shadow


@dataclass(frozen=True)
class Fonts:
    gothic: FontRef
    old_english: FontRef
    serif: FontRef
    serif_bold: FontRef
    italic: FontRef
    sans: FontRef
    sans_medium: FontRef
    mono: FontRef
    brush: FontRef


# ---- panel layout ----------------------------------------------------------------------

def _split_x(y: float) -> float:
    """The slanted gutter between the name panel and the right-hand panels."""
    return 676 - 60 * y / H


def _split_y(x: float) -> float:
    """The gutter between the top-right panel and the two below it, falling to the right."""
    return 250 - 22 * (x - 640) / 640


def _split_v(y: float) -> float:
    """The gutter between the two bottom panels, leaning the other way."""
    return 964 - 24 * (y - 240) / 200


def _panels() -> dict[str, list[tuple[float, float]]]:
    g = GUTTER / 2
    left = lambda y: _split_x(y) + GUTTER
    top_l, top_r = _split_y(left(240)) - g, _split_y(W) - g
    low_l, low_m, low_r = _split_y(left(262)) + g, _split_y(_split_v(250)) + g, _split_y(W) + g
    return {
        "name": [(0, 0), (_split_x(0), 0), (_split_x(H), H), (0, H)],
        "ryuk": [(left(0), 0), (W, 0), (W, top_r), (left(top_l), top_l)],
        "l": [(left(low_l), low_l), (_split_v(low_m) - g, low_m), (_split_v(H) - g, H), (left(H), H)],
        "note": [(_split_v(low_m) + g, low_m), (W, low_r), (W, H), (_split_v(H) + g, H)],
    }


def _points(poly) -> str:
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in poly)


# ---- shared manga texture --------------------------------------------------------------

def _speed_lines(rng: random.Random, cx: float, cy: float, inner: float, outer: float,
                 count: int, fill: str, opacity: float) -> str:
    """Concentration lines: thin wedges pointing in at a focus, flickering like a held frame."""
    out = []
    for i in range(count):
        a = i / count * math.tau + rng.uniform(-0.03, 0.03)
        r0 = inner * rng.uniform(0.85, 1.4)
        spread = rng.uniform(0.004, 0.014)
        p = [
            (cx + math.cos(a) * r0, cy + math.sin(a) * r0),
            (cx + math.cos(a - spread) * outer, cy + math.sin(a - spread) * outer),
            (cx + math.cos(a + spread) * outer, cy + math.sin(a + spread) * outer),
        ]
        out.append(f'<polygon points="{_points(p)}" opacity="{rng.uniform(0.25, 1):.2f}"/>')
    return (
        f'<g fill="{fill}" opacity="{opacity}">{"".join(out)}'
        f'<animate attributeName="opacity" values="{opacity};{opacity * 0.55:.3f};{opacity};{opacity * 0.8:.3f};{opacity}" '
        'dur="0.9s" repeatCount="indefinite"/></g>'
    )


# ---- panel 1: the name -----------------------------------------------------------------

def _placed(shape: Shaped, x: float, y: float, fill: str, opacity: float = 1.0) -> str:
    return f'<path transform="translate({x:.1f} {y:.1f})" d="{shape.d}" fill="{fill}" opacity="{opacity}"/>'


def _on_baseline(shape: Shaped, x: float, baseline: float, fill: str) -> str:
    return _placed(shape, x, baseline - shape.ascent, fill)


def _written(shape: Shaped, x: float, baseline: float, fill: str, begin: float, dur: float) -> str:
    """Traced in ink, then filled. At rest it is simply filled, so a renderer that skips
    SMIL still shows the name."""
    total = begin + dur + 0.6
    at = lambda t: f"{t / total:.3f}"
    return (
        f'<path transform="translate({x:.1f} {baseline - shape.ascent:.1f})" d="{shape.d}" fill="{fill}" '
        f'stroke="{fill}" stroke-width="0.9" pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="0">'
        f'<animate attributeName="stroke-dashoffset" values="1;1;0" keyTimes="0;{at(begin)};{at(begin + dur)}" dur="{total:.2f}s" fill="freeze"/>'
        f'<animate attributeName="fill-opacity" values="0;0;1" keyTimes="0;{at(begin + dur * 0.8)};1" dur="{total:.2f}s" fill="freeze"/>'
        '</path>'
    )


def _name_panel(fonts: Fonts, rng: random.Random) -> str:
    x = 64
    label = text_path(fonts.mono, "APS COLLEGE OF ENGINEERING  ·  B.E. CSE", 12.5, tracking=0.26)
    name = text_path(fonts.gothic, "Likith Lochan", 90)
    role = text_path(fonts.sans_medium, "DevOps  ·  Backend/Full-Stack  ·  Applied AI", 22)
    focus = text_path(fonts.sans, "Kubernetes, Terraform, AIOps and RAG", 20)
    motto = text_path(fonts.italic, "“The incident whose name is written here shall be resolved.”", 21)
    open_to = text_path(fonts.mono, "OPEN TO  ·  DEVOPS/CLOUD  ·  BACKEND  ·  SDE  ·  AI-ML", 11.5, tracking=0.2)
    bleed = (
        f'<g opacity="0">{_on_baseline(name, x + 3, 192 + 1.5, BLOOD)}'
        '<animate attributeName="opacity" values="0;0;0.75;0;0.5;0" keyTimes="0;0.82;0.84;0.87;0.89;1" dur="11s" begin="5s" repeatCount="indefinite"/></g>'
    )
    return "".join((
        '<rect width="700" height="440" fill="url(#nameBg)"/>',
        _speed_lines(rng, 250, 170, 250, 900, 150, "#ffffff", 0.07),
        '<rect y="250" width="700" height="190" fill="url(#toneRed)" mask="url(#fadeUp)"/>',
        _on_baseline(label, x, 90, "#8b7e78"),
        bleed,
        _written(name, x, 192, PAPER, 0.4, 2.8),
        f'<rect x="{x}" y="214" width="120" height="3" fill="{BLOOD}">'
        '<animate attributeName="width" values="0;0;120" keyTimes="0;0.6;1" dur="3.6s" fill="freeze"/></rect>',
        _on_baseline(role, x, 258, PAPER),
        _on_baseline(focus, x, 290, BONE),
        _on_baseline(motto, x, 338, "#a39689"),
        _on_baseline(open_to, x, 390, BLOOD),
    ))


# ---- panel 2: Ryuk ---------------------------------------------------------------------

def _hair(rng: random.Random) -> str:
    """A crown of long, uneven spikes around the head, the way the anime draws it."""
    points = []
    n = 50
    for i in range(n + 1):
        a = math.radians(158 + 224 * i / n)
        if i % 2:
            r = rng.uniform(112, 160) if 0.12 < i / n < 0.88 else rng.uniform(84, 108)
            a += rng.uniform(-0.05, 0.05)
        else:
            r = rng.uniform(48, 56)
        points.append((r * math.cos(a) * 1.08, -50 + r * math.sin(a)))
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in points) + " Z"


def _q(x: float, end_y: float, mid_y: float) -> float:
    """The y of the grin's curve at x: a quadratic through (-52, end_y), (0, mid_y), (52, end_y)."""
    return end_y + (mid_y - end_y) * (1 - (x / 52) ** 2)


def _ryuk(rng: random.Random) -> str:
    face = "M-50 -44 C-58 6 -44 58 -14 80 C-6 86 6 86 14 80 C44 58 58 6 50 -44 Z"
    # Hard cel shadow: the hair's shadow across the brow and the unlit left cheek.
    shadow = (
        "M-52 -44 L52 -44 L50 -18 L38 -26 L30 -12 L18 -24 L8 -8 L-4 -22 L-16 -6 L-26 -22 L-36 -8 L-46 -20 L-52 -2 Z "
        "M-52 -2 C-56 30 -42 62 -14 80 C-22 60 -30 40 -32 12 Z"
    )
    eyes = []
    for x in (-24, 24):
        eyes.append(
            f'<ellipse cx="{x}" cy="2" rx="21" ry="17" fill="#0b0c10"/>'
            f'<g filter="url(#glow)"><circle cx="{x}" cy="2" r="14" fill="url(#eyeYellow)"/>'
            f'<circle cx="{x}" cy="2" r="6.5" fill="none" stroke="{BLOOD}" stroke-width="2.2"/>'
            f'<circle cx="{x}" cy="2" r="2.2" fill="{INK}"/></g>'
            # Blink: a lid of shadow drops over the eye now and then.
            f'<rect x="{x - 16}" y="-15" width="32" height="0" fill="{SKIN[2]}">'
            '<animate attributeName="height" values="0;0;32;0;0" keyTimes="0;0.9;0.93;0.96;1" dur="8s" repeatCount="indefinite"/></rect>'
        )
    upper = "M-52 26 Q-26 50 0 50 Q26 50 52 26"
    mouth = upper + " Q24 76 0 76 Q-24 76 -52 26 Z"
    teeth_top = "".join(
        f'<path d="M{x - 3.2:.1f} {_q(x, 26, 50):.1f} L{x:.1f} {_q(x, 26, 50) + 9:.1f} L{x + 3.2:.1f} {_q(x, 26, 50):.1f} Z"/>'
        for x in range(-44, 45, 7)
    )
    teeth_bottom = "".join(
        f'<path d="M{x - 3.2:.1f} {_q(x, 26, 76):.1f} L{x:.1f} {_q(x, 26, 76) - 9:.1f} L{x + 3.2:.1f} {_q(x, 26, 76):.1f} Z"/>'
        for x in range(-40, 41, 7)
    )
    collar = "M-120 170 L-96 104 L-84 132 L-66 96 L-54 128 L-34 100 L-20 118 L0 108 L20 118 L34 100 L54 128 L66 96 L84 132 L96 104 L120 170 Z"
    return f'''
<g transform="translate(1084 124) scale(1.08)">
  <path d="{collar}" fill="{INK}" stroke="{EMBER}" stroke-opacity="0.4" stroke-width="1.2"/>
  <path d="M-24 78 L-20 110 L20 110 L24 78 Z" fill="{SKIN[2]}"/>
  <path d="{face}" fill="url(#skin)" stroke="{INK}" stroke-width="3"/>
  <path d="{shadow}" fill="{SKIN[2]}" opacity="0.9"/>
  <path d="M-8 20 L0 30 L8 20" fill="none" stroke="{INK}" stroke-width="1.6" opacity="0.6"/>
  {"".join(eyes)}
  <path d="{mouth}" fill="#2a0508" stroke="#10131b" stroke-width="4" stroke-linejoin="round"/>
  <g fill="{PAPER}">{teeth_top}{teeth_bottom}</g>
  <path d="{upper}" fill="none" stroke="#10131b" stroke-width="3.2"/>
  <path d="{_hair(rng)}" fill="{INK}" stroke="{EMBER}" stroke-opacity="0.35" stroke-width="1"/>
  <animateTransform attributeName="transform" type="translate" additive="sum" values="0 0;0 -3;0 0" dur="5s" repeatCount="indefinite"/>
</g>'''


def _speech(fonts: Fonts) -> str:
    """Ryuk's line from the first episode, set vertically in a manga balloon."""
    size = 25
    right = vertical_path(fonts.brush, "人間って", size, gap=0.1)
    left = vertical_path(fonts.brush, "面白！！", size, gap=0.1)
    cx, cy = 752, 104
    col_gap = 8
    top = cy - right.height / 2
    english = text_path(fonts.italic, "“Humans are so interesting.”  — Ryuk", 16)
    balloon = (
        f'<path d="M{cx + 44} {cy + 44} L{cx + 118} {cy + 64} L{cx + 30} {cy + 70} Z" fill="{PAPER}" stroke="{INK}" stroke-width="2.5" stroke-linejoin="round"/>'
        f'<ellipse cx="{cx}" cy="{cy}" rx="58" ry="84" fill="{PAPER}" stroke="{INK}" stroke-width="2.5"/>'
    )
    total, begin = 3.0, 2.2
    at = lambda t: f"{t / total:.3f}"
    # Pops in once, overshooting a little, then stays. Resting state is the full balloon.
    pop = (
        f'<animateTransform attributeName="transform" type="scale" additive="sum" values="0;0;1.08;1" '
        f'keyTimes="0;{at(begin)};{at(begin + 0.25)};1" dur="{total}s" fill="freeze"/>'
    )
    return (
        f'<g transform="translate({cx} {cy})"><g>{pop}<g transform="translate({-cx} {-cy})">'
        f'{balloon}'
        f'<g transform="translate({cx + col_gap / 2:.1f} {top:.1f})" fill="{INK}">{right.d}</g>'
        f'<g transform="translate({cx - col_gap / 2 - size:.1f} {top:.1f})" fill="{BLOOD}">{left.d}</g>'
        f'</g></g></g>'
        + _on_baseline(english, 682, 228, BONE)
    )


def _ryuk_panel(fonts: Fonts, rng: random.Random) -> str:
    return "".join((
        '<rect x="600" width="700" height="260" fill="#0b0304"/>',
        '<circle cx="1150" cy="92" r="250" fill="url(#halo)"/>',
        '<circle cx="1150" cy="92" r="128" fill="url(#moon)"/>',
        '<circle cx="1150" cy="92" r="128" fill="url(#toneDark)" opacity="0.8"/>',
        _speed_lines(rng, 1086, 120, 150, 700, 90, "#000000", 0.9),
        _ryuk(rng),
        _speech(fonts),
    ))


# ---- panel 3: L ------------------------------------------------------------------------

def _l_panel(fonts: Fonts) -> str:
    letter = text_path(fonts.old_english, "L", 130)
    sx, sy, sw, sh = 690, 282, 236, 140
    lx = sx + (sw - letter.width) / 2
    ly = sy + (sh - letter.ascent * 0.72) / 2
    flicker = '<animate attributeName="opacity" values="1;0.9;1;1;0.72;1;1" keyTimes="0;0.02;0.04;0.6;0.62;0.64;1" dur="6s" repeatCount="indefinite"/>'
    return f'''
<rect x="600" y="220" width="400" height="240" fill="#050607"/>
<ellipse cx="{sx + sw / 2}" cy="{sy + sh / 2}" rx="210" ry="120" fill="url(#screenGlow)">{flicker}</ellipse>
<rect x="{sx - 10}" y="{sy - 10}" width="{sw + 20}" height="{sh + 30}" rx="8" fill="#101216" stroke="#2b2f36"/>
<g>{flicker}
  <rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="3" fill="url(#screen)"/>
  <path transform="translate({lx:.1f} {ly - letter.ascent * 0.28:.1f})" d="{letter.d}" fill="#0a0a0a"/>
  <rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" fill="url(#scan)"/>
</g>
<rect x="{sx}" y="{sy}" width="{sw}" height="6" fill="#ffffff" opacity="0.18">
  <animate attributeName="y" values="{sy};{sy + sh - 6}" dur="3.5s" repeatCount="indefinite"/>
</rect>'''


# ---- panel 4: the note falls -----------------------------------------------------------

def _note_panel(fonts: Fonts, rng: random.Random) -> str:
    lines = []
    for _ in range(34):
        x = rng.uniform(960, 1280)
        length = rng.uniform(40, 140)
        dur = rng.uniform(0.5, 1.1)
        lines.append(
            f'<rect x="{x:.0f}" y="0" width="{rng.choice((1, 1, 1.5, 2))}" height="{length:.0f}" fill="#ffffff" opacity="{rng.uniform(0.08, 0.3):.2f}">'
            f'<animate attributeName="y" values="460;{220 - length:.0f}" dur="{dur:.2f}s" begin="-{rng.uniform(0, dur):.2f}s" repeatCount="indefinite"/></rect>'
        )
    title = text_path(fonts.gothic, "DEATH NOTE", 12.5, tracking=0.04)
    cover = (
        '<rect x="-38" y="-52" width="76" height="104" rx="3" fill="#0a0808" stroke="#8b7d74" stroke-width="1.4"/>'
        f'<rect x="38" y="-49" width="5" height="100" fill="{BONE}"/>'
        '<rect x="-38" y="-52" width="8" height="104" fill="#1c1515"/>'
        f'<path transform="translate({-title.width / 2 + 3:.1f} {-30 - title.ascent:.1f})" d="{title.d}" fill="{PAPER}"/>'
        '<rect x="-26" y="-22" width="58" height="0.8" fill="#8b7d74"/>'
    )
    return f'''
<rect x="940" y="220" width="360" height="240" fill="url(#noteBg)"/>
<rect x="940" y="220" width="360" height="240" fill="url(#toneDark)" opacity="0.5"/>
<g>{"".join(lines)}</g>
<g transform="translate(1122 336)">
  <g>{cover}
    <animateTransform attributeName="transform" type="rotate" values="-14;-6;-18;-14" dur="3.2s" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.4;0.75;1" keySplines="0.45 0 0.55 1;0.45 0 0.55 1;0.45 0 0.55 1"/>
    <animateTransform attributeName="transform" type="translate" additive="sum" values="0 -4;0 4;0 -4" dur="1.6s" repeatCount="indefinite"/>
  </g>
</g>'''


# ---- assembly --------------------------------------------------------------------------

def _embers(rng: random.Random) -> str:
    out = []
    for _ in range(18):
        x, y = rng.uniform(20, 640), rng.uniform(360, 440)
        rise, drift = rng.uniform(80, 200), rng.uniform(-30, 30)
        dur = rng.uniform(8, 15)
        begin = -rng.uniform(0, dur)
        out.append(
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rng.choice((0.9, 1.2, 1.6))}" fill="{EMBER}" opacity="0">'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;{drift:.0f} {-rise:.0f}" dur="{dur:.1f}s" begin="{begin:.1f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0;0.8;0" dur="{dur:.1f}s" begin="{begin:.1f}s" repeatCount="indefinite"/></circle>'
        )
    return f'<g filter="url(#glow)">{"".join(out)}</g>'


def render(fonts: Fonts) -> str:
    rng = random.Random(SEED)
    panels = _panels()
    clips = "".join(f'<clipPath id="p-{k}"><polygon points="{_points(p)}"/></clipPath>' for k, p in panels.items())
    borders = "".join(
        f'<polygon points="{_points(p)}" fill="none" stroke="{BONE}" stroke-width="2.5" stroke-linejoin="round"/>'
        for p in panels.values()
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Likith Lochan. DevOps, Backend/Full-Stack, Applied AI. A manga page: Ryuk grinning against a red moon saying humans are so interesting, L's gothic letter on a monitor, and the Death Note falling.">
<defs>
  <clipPath id="frame"><rect width="{W}" height="{H}" rx="16"/></clipPath>
  {clips}
  <pattern id="toneRed" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><circle cx="3.5" cy="3.5" r="1.6" fill="{BLOOD}" opacity="0.55"/></pattern>
  <pattern id="toneDark" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><circle cx="3" cy="3" r="1.25" fill="#000"/></pattern>
  <pattern id="scan" width="4" height="3" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" opacity="0.12"/></pattern>
  <linearGradient id="fadeUpG" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0.9"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
  <mask id="fadeUp" maskUnits="userSpaceOnUse" x="0" y="250" width="700" height="190"><rect y="250" width="700" height="190" fill="url(#fadeUpG)"/></mask>
  <radialGradient id="nameBg" cx="0.35" cy="0.4" r="0.8"><stop offset="0" stop-color="#1a0a0b"/><stop offset="1" stop-color="#060304"/></radialGradient>
  <radialGradient id="halo"><stop offset="0" stop-color="#ff3a2e" stop-opacity="0.35"/><stop offset="0.5" stop-color="#8f0f14" stop-opacity="0.12"/><stop offset="1" stop-color="#8f0f14" stop-opacity="0"/></radialGradient>
  <radialGradient id="moon" cx="0.4" cy="0.38" r="0.75"><stop offset="0" stop-color="#ff8a64"/><stop offset="0.5" stop-color="#d0281f"/><stop offset="1" stop-color="#5c0709"/></radialGradient>
  <linearGradient id="skin" x1="0" y1="0" x2="1" y2="0.3"><stop offset="0" stop-color="{SKIN[1]}"/><stop offset="0.55" stop-color="{SKIN[0]}"/><stop offset="1" stop-color="{SKIN[1]}"/></linearGradient>
  <radialGradient id="eyeYellow" cx="0.4" cy="0.4" r="0.7"><stop offset="0" stop-color="#fff6b8"/><stop offset="0.6" stop-color="#f5c928"/><stop offset="1" stop-color="#b8760a"/></radialGradient>
  <radialGradient id="screen" cx="0.5" cy="0.5" r="0.7"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#cfd6de"/></radialGradient>
  <radialGradient id="screenGlow"><stop offset="0" stop-color="#dfe8f5" stop-opacity="0.35"/><stop offset="1" stop-color="#dfe8f5" stop-opacity="0"/></radialGradient>
  <linearGradient id="noteBg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1b0608"/><stop offset="1" stop-color="#050203"/></linearGradient>
  <filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <filter id="grain" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="4" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 1  0 0 0 0 0.9  0 0 0 0 0.85  0 0 0 0.08 0"/>
  </filter>
</defs>
<g clip-path="url(#frame)">
  <rect width="{W}" height="{H}" fill="{INK}"/>
  <g clip-path="url(#p-name)">{_name_panel(fonts, rng)}{_embers(rng)}</g>
  <g clip-path="url(#p-ryuk)">{_ryuk_panel(fonts, rng)}</g>
  <g clip-path="url(#p-l)">{_l_panel(fonts)}</g>
  <g clip-path="url(#p-note)">{_note_panel(fonts, rng)}</g>
  {borders}
  <rect width="{W}" height="{H}" filter="url(#grain)"/>
</g>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="#2a1a1a"/>
</svg>'''
