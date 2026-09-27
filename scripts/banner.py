"""The header: a blood moon over a gothic city, and a shinigami who got bored.

Ryuk crouches on the cathedral tower with an apple, his silhouette against the moon.
A black notebook falls out of the sky, crows cross the moon, feathers drift down and
embers rise. The name is written in, stroke by stroke, the way names go into the note.

Original vector art, not frames from the show. Motion stays slow so the banner reads
as still at a glance and alive if you keep looking.
"""

import math
import random
import re
from dataclasses import dataclass

from fontpaths import FontRef, Shaped, text_path, vertical_path

W, H = 1280, 440
SEED = 41

MOON = (930, 150, 104)   # cx, cy, r
TOWER = (930, 290, 118)  # cx, ledge y, width: where Ryuk crouches
SKY = ("#040203", "#0c0405", "#220709")
FAR = "#0f0708"
NEAR = "#050303"
BLOOD = "#e0303a"
EMBER = "#ff5a3c"
PAPER = "#efe6d8"
BONE = "#c9b99a"
WINDOW = "#d9a441"


@dataclass(frozen=True)
class Fonts:
    gothic: FontRef
    serif: FontRef
    serif_bold: FontRef
    italic: FontRef
    sans: FontRef
    sans_medium: FontRef
    mono: FontRef
    brush: FontRef


# ---- sky -------------------------------------------------------------------------------

def _stars(rng: random.Random) -> str:
    cx, cy, r = MOON
    out = []
    for i in range(80):
        x, y = rng.uniform(20, W - 20), rng.uniform(12, 280)
        if (x - cx) ** 2 + (y - cy) ** 2 < (r + 60) ** 2:
            continue  # lost in the moon's glare
        size = rng.choice((0.6, 0.8, 0.8, 1.0, 1.3))
        base = rng.uniform(0.2, 0.7)
        twinkle = ""
        if i % 6 == 0:
            dur = rng.uniform(4, 9)
            twinkle = (
                f'<animate attributeName="opacity" values="{base:.2f};{base * 0.2:.2f};{base:.2f}" '
                f'dur="{dur:.1f}s" begin="-{rng.uniform(0, dur):.1f}s" repeatCount="indefinite"/>'
            )
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{size}" fill="#f1dcd4" opacity="{base:.2f}">{twinkle}</circle>')
    return "".join(out)


def _moon() -> str:
    """A blood moon: copper face, darker limb, and a halo that breathes."""
    cx, cy, r = MOON
    craters = [(-36, -30, 24, 0.10), (32, 16, 32, 0.08), (-10, 50, 17, 0.08), (46, -42, 13, 0.07), (-56, 26, 11, 0.06)]
    marks = "".join(
        f'<circle cx="{cx + dx}" cy="{cy + dy}" r="{cr}" fill="#5a0f10" opacity="{o}"/>' for dx, dy, cr, o in craters
    )
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{r * 2.8:.0f}" fill="url(#halo)">'
        '<animate attributeName="opacity" values="0.75;1;0.75" dur="9s" repeatCount="indefinite"/></circle>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#moonFace)"/>{marks}'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#moonShade)"/>'
    )


def _clouds(rng: random.Random) -> str:
    """Thin bands of dark cloud dragged slowly across the moon."""
    out = []
    for cy, width, dur, opacity in ((118, 520, 140, 0.55), (206, 640, 180, 0.45), (62, 420, 210, 0.35)):
        cx = rng.uniform(760, 1040)
        puffs = "".join(
            f'<ellipse cx="{cx + rng.uniform(-width / 2, width / 2):.0f}" cy="{cy + rng.uniform(-5, 5):.0f}" '
            f'rx="{rng.uniform(70, 140):.0f}" ry="{rng.uniform(6, 12):.0f}"/>'
            for _ in range(6)
        )
        out.append(
            f'<g fill="#1a0707" opacity="{opacity}" filter="url(#cloud)">{puffs}'
            f'<animateTransform attributeName="transform" type="translate" values="-280 0;280 0;-280 0" '
            f'dur="{dur}s" begin="-{rng.uniform(0, dur):.0f}s" repeatCount="indefinite"/></g>'
        )
    return "".join(out)


def _crows() -> str:
    """Three crows crossing the moon, wings beating."""
    up = "M-9 0 Q-5 -6 0 0 Q5 -6 9 0 Q5 -2 0 1 Q-5 -2 -9 0 Z"
    down = "M-9 -1 Q-5 3 0 0 Q5 3 9 -1 Q5 5 0 2 Q-5 5 -9 -1 Z"
    out = []
    for y, scale, dur, begin, beat in ((96, 1.1, 24, 0, 0.55), (122, 0.8, 24, 1.3, 0.48), (76, 0.65, 24, 2.1, 0.6)):
        out.append(
            f'<g><animateTransform attributeName="transform" type="translate" values="1340 {y};-60 {y - 30}" '
            f'dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/>'
            f'<path d="{up}" transform="scale({scale})" fill="#060203">'
            f'<animate attributeName="d" values="{up};{down};{up}" dur="{beat}s" repeatCount="indefinite"/></path></g>'
        )
    return "".join(out)


# ---- city ------------------------------------------------------------------------------

def _building(x: float, w: float, top: float, style: str) -> str:
    """One gothic silhouette: flat, pinnacled, spired, or gabled."""
    body = f'<rect x="{x:.0f}" y="{top:.0f}" width="{w + 1:.0f}" height="{H - top:.0f}"/>'
    if style == "pinnacle":
        peaks = "".join(
            f'<path d="M{px - 4:.1f} {top:.0f} L{px:.1f} {top - 20:.0f} L{px + 4:.1f} {top:.0f} Z"/>'
            for px in (x + 5, x + w / 2, x + w - 5)
        )
        return body + peaks
    if style == "spire":
        mid = x + w / 2
        return body + (
            f'<rect x="{x + w * 0.25:.0f}" y="{top - 22:.0f}" width="{w * 0.5:.0f}" height="23"/>'
            f'<path d="M{mid - w * 0.16:.1f} {top - 22:.0f} L{mid:.1f} {top - 88:.0f} L{mid + w * 0.16:.1f} {top - 22:.0f} Z"/>'
        )
    if style == "gable":
        pitch = min(26.0, w * 0.3)
        return f'<path d="M{x:.0f} {H} L{x:.0f} {top + pitch:.0f} L{x + w / 2:.0f} {top:.0f} L{x + w:.0f} {top + pitch:.0f} L{x + w:.0f} {H} Z"/>'
    return body


def _skyline(rng: random.Random) -> str:
    """Two layers of roofs. The left stays low so it never crowds the name."""
    far, near, windows = [], [], []
    tx, ty, tw = TOWER
    x = 0.0
    while x < W:
        w = rng.uniform(40, 96)
        top = rng.uniform(380, 404) if x < 600 else rng.uniform(300, 356)
        far.append(_building(x, w, top, rng.choice(("flat", "pinnacle", "spire", "gable", "flat"))))
        for _ in range(rng.randint(0, 3) if x > 600 else rng.randint(0, 1)):
            wx, wy = x + rng.uniform(6, w - 10), top + rng.uniform(14, 60)
            if wy < H - 12:
                windows.append(
                    f'<rect x="{wx:.0f}" y="{wy:.0f}" width="3" height="7" rx="1.5" fill="{WINDOW}" '
                    f'opacity="{rng.uniform(0.25, 0.7):.2f}"/>'
                )
        x += w
    x = 0.0
    while x < W:
        w = rng.uniform(70, 150)
        if not (tx - tw / 2 - 20 < x + w and x < tx + tw / 2 + 20):
            near.append(_building(x, w, rng.uniform(406, 422), rng.choice(("flat", "gable", "pinnacle"))))
        x += w
    # One window in the tower's shadow goes dark and comes back, slowly.
    windows.append(
        f'<rect x="1112" y="342" width="3" height="7" rx="1.5" fill="{WINDOW}" opacity="0.7">'
        '<animate attributeName="opacity" values="0.7;0.1;0.7" dur="12s" repeatCount="indefinite"/></rect>'
    )
    return f'<g fill="{FAR}">{"".join(far)}</g>{"".join(windows)}<g fill="{NEAR}">{"".join(near)}</g>'


def _tower() -> str:
    """The cathedral tower Ryuk sits on: parapet, corner pinnacles, and a clock that keeps time."""
    cx, ledge, w = TOWER
    left, right = cx - w / 2, cx + w / 2
    body = (
        f'<rect x="{left}" y="{ledge}" width="{w}" height="{H - ledge}"/>'
        f'<rect x="{left - 8}" y="{ledge - 6}" width="{w + 16}" height="8"/>'
        + "".join(
            f'<rect x="{px - 7}" y="{ledge - 30}" width="14" height="26"/>'
            f'<path d="M{px - 7} {ledge - 30} L{px} {ledge - 58} L{px + 7} {ledge - 30} Z"/>'
            for px in (left - 1, right + 1)
        )
        + f'<path d="M{cx - 22} {H} L{cx - 22} {ledge + 110} A22 22 0 0 1 {cx + 22} {ledge + 110} L{cx + 22} {H} Z" fill="#0c0606"/>'
    )
    clock_y = ledge + 52
    clock = (
        f'<circle cx="{cx}" cy="{clock_y}" r="23" fill="#140a09" stroke="{BONE}" stroke-opacity="0.35" stroke-width="1.5"/>'
        + "".join(
            f'<line x1="{cx + 18 * math.cos(a * math.pi / 6):.1f}" y1="{clock_y + 18 * math.sin(a * math.pi / 6):.1f}" '
            f'x2="{cx + 21 * math.cos(a * math.pi / 6):.1f}" y2="{clock_y + 21 * math.sin(a * math.pi / 6):.1f}" '
            f'stroke="{BONE}" stroke-opacity="0.45" stroke-width="1.2"/>'
            for a in range(12)
        )
        + f'<line x1="{cx}" y1="{clock_y}" x2="{cx}" y2="{clock_y - 11}" stroke="{BONE}" stroke-opacity="0.6" stroke-width="2" stroke-linecap="round">'
        f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {clock_y}" to="360 {cx} {clock_y}" dur="720s" repeatCount="indefinite"/></line>'
        + f'<line x1="{cx}" y1="{clock_y}" x2="{cx}" y2="{clock_y - 17}" stroke="{BLOOD}" stroke-opacity="0.85" stroke-width="1.3" stroke-linecap="round">'
        f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {clock_y}" to="360 {cx} {clock_y}" dur="60s" repeatCount="indefinite"/></line>'
        + f'<circle cx="{cx}" cy="{clock_y}" r="2" fill="{BONE}"/>'
    )
    return f'<g fill="{NEAR}">{body}</g>{clock}'


# ---- Ryuk ------------------------------------------------------------------------------

def _hair() -> str:
    """Spiky crown around a long face: alternating radii, smooth jaw underneath."""
    points = []
    spikes = 15
    for i in range(spikes * 2 + 1):
        a = math.radians(160 + 220 * i / (spikes * 2))
        r = 13 if i % 2 == 0 else (27 if 3 < i < spikes * 2 - 3 else 21)
        points.append((r * math.cos(a), -101 + r * math.sin(a) * 0.95))
    path = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in points)
    return path + " Q12 -84 0 -80 Q-12 -84 -12.2 -96.5 Z"


def _ryuk() -> str:
    """Crouched on the ledge, wings half open, apple held out. Rim-lit by the red moon."""
    cx, ledge, _ = TOWER
    wing_l = (
        "M-12 -80 C-40 -104 -84 -130 -134 -140 L-122 -122 L-140 -114 L-116 -104 L-132 -92 "
        "L-108 -88 L-120 -74 L-94 -74 L-100 -60 L-74 -64 L-76 -50 L-52 -58 L-44 -44 L-16 -56 Z"
    )
    wing_r = _mirror_path(wing_l)
    # Lanky and crouched: built from its left half, mirrored.
    half = [(-7, -86), (-18, -82), (-16, -66), (-12, -50), (-15, -44), (-37, -32), (-31, -5),
            (-41, 0), (-21, 0), (-22, -6), (-24, -26), (-6, -38)]
    outline = half + [(-x, y) for x, y in reversed(half)]
    body = "M" + " L".join(f"{x} {y}" for x, y in outline) + " Z"
    arm_l = "M-16 -80 Q-34 -66 -38 -46 Q-41 -32 -46 -24"
    arm_r = "M16 -80 Q38 -78 43 -93"
    claws_l = "M-46 -24 L-51 -15 M-46 -24 L-46 -13 M-46 -24 L-41 -16"
    belt = (
        '<rect x="-13" y="-50" width="26" height="5" fill="#1c1010"/>'
        + "".join(f'<circle cx="{x}" cy="-47.5" r="1.1" fill="{BONE}" opacity="0.7"/>' for x in (-9, -4.5, 0, 4.5, 9))
        + f'<path d="M-6 -45 Q-2 -34 4 -40" fill="none" stroke="{BONE}" stroke-opacity="0.5" stroke-width="0.9" stroke-dasharray="1.6 1.2"/>'
    )
    rim = f'stroke="{EMBER}" stroke-opacity="0.45" stroke-width="1"'
    flap = lambda sign: (
        f'<animateTransform attributeName="transform" type="rotate" values="0 {sign * 12} -80;{sign * 7} {sign * 12} -80;0 {sign * 12} -80" '
        'dur="6s" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.5;1" keySplines="0.45 0 0.55 1;0.45 0 0.55 1"/>'
    )
    eyes = "".join(
        f'<circle cx="{x}" cy="-101" r="2.6" fill="{EMBER}" filter="url(#glow)">'
        '<animate attributeName="r" values="2.6;2.6;0.3;2.6;2.6" keyTimes="0;0.93;0.955;0.98;1" dur="7s" repeatCount="indefinite"/></circle>'
        for x in (-5, 5)
    )
    grin = (
        f'<path d="M-9 -92 Q0 -85 9 -92" fill="none" stroke="{PAPER}" stroke-width="1.6" stroke-linecap="round"/>'
        + "".join(f'<path d="M{x} {-91.4 + abs(x) * 0.02:.1f} L{x} {-88.6 + abs(x) * 0.12:.1f}" stroke="#050303" stroke-width="0.8"/>' for x in (-5, -2, 1, 4))
    )
    apple = (
        '<g transform="translate(45 -99)">'
        f'<circle r="7.5" fill="url(#appleSkin)" filter="url(#glow)"/>'
        '<circle cx="6.5" cy="-2" r="3.2" fill="#050303"/>'  # the bite
        f'<path d="M0 -7 Q1 -11 3 -12" stroke="{BONE}" stroke-width="1.2" fill="none"/>'
        '<circle cx="-2.6" cy="-2.6" r="1.6" fill="#ffd9d0" opacity="0.7"/>'
        '<animateTransform attributeName="transform" type="translate" additive="sum" values="0 0;0 -2;0 0" dur="4s" repeatCount="indefinite"/>'
        '</g>'
    )
    silhouette = "#030202"
    return f'''
<g transform="translate({cx} {ledge - 6}) scale(1.24)">
  <g fill="{silhouette}" {rim}>
    <path d="{wing_l}">{flap(-1)}</path>
    <path d="{wing_r}">{flap(1)}</path>
    <path d="{body}"/>
    <path d="{_hair()}"/>
  </g>
  {belt}
  <g fill="none" stroke="{silhouette}" stroke-width="6" stroke-linecap="round">
    <path d="{arm_l}"/><path d="{arm_r}"/>
    <path d="{claws_l}" stroke-width="1.6"/>
  </g>
  <path d="{arm_l}" fill="none" stroke="{EMBER}" stroke-opacity="0.2" stroke-width="1"/>
  {eyes}{grin}{apple}
</g>'''


def _mirror_path(d: str) -> str:
    """Mirror an absolute M/L/C path (x y pairs) across x = 0."""
    out, index = [], 0
    for command, value in re.findall(r"([A-Za-z]?)(-?[\d.]+)", d):
        if command:
            index = 0
        n = float(value)
        out.append(f"{command}{-n if index % 2 == 0 else n:g}")
        index += 1
    return " ".join(out) + (" Z" if d.rstrip().endswith("Z") else "")


# ---- motion ----------------------------------------------------------------------------

def _falling_note(fonts: Fonts) -> str:
    """A black notebook tumbling out of the sky, now and then."""
    title = text_path(fonts.gothic, "Death Note", 7.2)
    cover = (
        '<rect x="-17" y="-23" width="34" height="46" rx="2" fill="#0b0707" stroke="#6b5a55" stroke-width="1"/>'
        '<rect x="-17" y="-23" width="4" height="46" fill="#1a1212"/>'
        f'<path transform="translate({-title.width / 2 + 2:.1f} {-8 - title.ascent:.1f})" d="{title.d}" fill="{BONE}"/>'
    )
    return f'''
<g opacity="0">
  <animate attributeName="opacity" values="0;0.95;0.95;0;0" keyTimes="0;0.04;0.5;0.56;1" dur="14s" begin="2s" repeatCount="indefinite"/>
  <g>
    <animateTransform attributeName="transform" type="translate" values="660 -40;748 470;748 470" keyTimes="0;0.56;1" dur="14s" begin="2s" repeatCount="indefinite"/>
    <g>{cover}
      <animateTransform attributeName="transform" type="rotate" values="-20;160;340" keyTimes="0;0.56;1" dur="14s" begin="2s" repeatCount="indefinite"/>
    </g>
  </g>
</g>'''


def _feathers(rng: random.Random) -> str:
    """Black feathers from his wings, rocking as they fall."""
    shape = "M0 -14 C5 -8 5 6 0 14 C-5 6 -5 -8 0 -14 Z M0 -14 L0 18"
    out = []
    for _ in range(7):
        x = rng.uniform(640, 1220)
        dur = rng.uniform(14, 22)
        begin = -rng.uniform(0, dur)
        sway = rng.uniform(18, 40)
        out.append(
            f'<g opacity="0.8"><animateTransform attributeName="transform" type="translate" '
            f'values="{x:.0f} -30;{x + sway:.0f} 150;{x - sway:.0f} 300;{x:.0f} 460" dur="{dur:.1f}s" begin="{begin:.1f}s" repeatCount="indefinite"/>'
            f'<path d="{shape}" fill="#2a1a1a" stroke="#5a2a28" stroke-width="0.6" transform="scale({rng.uniform(0.5, 0.85):.2f})">'
            f'<animateTransform attributeName="transform" type="rotate" additive="sum" values="-35;35;-35" dur="{dur / 3:.1f}s" begin="{begin:.1f}s" repeatCount="indefinite"/>'
            '</path></g>'
        )
    return "".join(out)


def _embers(rng: random.Random) -> str:
    out = []
    for _ in range(30):
        x, y = rng.uniform(560, W - 20), rng.uniform(330, 430)
        rise, drift = rng.uniform(110, 240), rng.uniform(-30, 30)
        dur = rng.uniform(8, 16)
        begin = -rng.uniform(0, dur)
        out.append(
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rng.choice((0.9, 1.2, 1.5, 2.0))}" fill="{EMBER}" opacity="0">'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;{drift:.0f} {-rise:.0f}" '
            f'dur="{dur:.1f}s" begin="{begin:.1f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0;0.9;0" dur="{dur:.1f}s" begin="{begin:.1f}s" repeatCount="indefinite"/>'
            '</circle>'
        )
    return f'<g filter="url(#glow)">{"".join(out)}</g>'


# ---- type ------------------------------------------------------------------------------

def _placed(shape: Shaped, x: float, y: float, fill: str, opacity: float = 1.0) -> str:
    return f'<path transform="translate({x:.1f} {y:.1f})" d="{shape.d}" fill="{fill}" opacity="{opacity}"/>'


def _on_baseline(shape: Shaped, x: float, baseline: float, fill: str) -> str:
    return _placed(shape, x, baseline - shape.ascent, fill)


def _written(shape: Shaped, x: float, baseline: float, fill: str, begin: float, dur: float) -> str:
    """Traced in ink, then filled, like a name going into the note. At rest it is simply filled,
    so a renderer that skips SMIL still shows the name."""
    total = begin + dur + 0.6
    at = lambda t: f"{t / total:.3f}"
    return (
        f'<path transform="translate({x:.1f} {baseline - shape.ascent:.1f})" d="{shape.d}" fill="{fill}" '
        f'stroke="{fill}" stroke-width="0.9" pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="0">'
        f'<animate attributeName="stroke-dashoffset" values="1;1;0" keyTimes="0;{at(begin)};{at(begin + dur)}" dur="{total:.2f}s" fill="freeze"/>'
        f'<animate attributeName="fill-opacity" values="0;0;1" keyTimes="0;{at(begin + dur * 0.8)};1" dur="{total:.2f}s" fill="freeze"/>'
        '</path>'
    )


def _type(fonts: Fonts) -> str:
    x = 84
    label = text_path(fonts.mono, "APS COLLEGE OF ENGINEERING  ·  B.E. CSE", 12.5, tracking=0.26)
    name = text_path(fonts.gothic, "Likith Lochan", 88)
    role = text_path(fonts.sans_medium, "DevOps  ·  Backend/Full-Stack  ·  Applied AI", 22)
    focus = text_path(fonts.sans, "Kubernetes, Terraform, AIOps and RAG", 20)
    motto = text_path(fonts.italic, "“The incident whose name is written here shall be resolved.”", 22)
    open_to = text_path(fonts.mono, "OPEN TO  ·  DEVOPS/CLOUD  ·  BACKEND  ·  SDE  ·  AI-ML", 11.5, tracking=0.2)
    rule_y = 214
    # The red ink bleeding through, briefly, every so often.
    bleed = (
        f'<g opacity="0">{_on_baseline(name, x + 2.5, 190 + 1.5, BLOOD)}'
        '<animate attributeName="opacity" values="0;0;0.7;0;0.45;0" keyTimes="0;0.82;0.84;0.87;0.89;1" dur="11s" begin="5s" repeatCount="indefinite"/></g>'
    )
    return "".join((
        _on_baseline(label, x, 98, "#8b7e78"),
        bleed,
        _written(name, x, 190, PAPER, 0.4, 2.8),
        f'<rect x="{x}" y="{rule_y}" width="120" height="2.5" fill="{BLOOD}">'
        f'<animate attributeName="width" values="0;0;120" keyTimes="0;0.6;1" dur="3.6s" fill="freeze"/></rect>',
        _on_baseline(role, x, 256, PAPER),
        _on_baseline(focus, x, 288, BONE),
        _on_baseline(motto, x, 336, "#a39689"),
        _on_baseline(open_to, x, 384, BLOOD),
    ))


def _calligraphy(fonts: Fonts) -> str:
    column = vertical_path(fonts.brush, "死神の手帳", 34, gap=0.12)
    seal_char = text_path(fonts.brush, "死", 20)
    x, y = 1200, 40
    seal_y = y + column.height + 16
    return (
        f'<g transform="translate({x} {y})" fill="{PAPER}" opacity="0.85">{column.d}</g>'
        f'<rect x="{x + 3}" y="{seal_y:.0f}" width="28" height="28" rx="3" fill="{BLOOD}"/>'
        + _placed(seal_char, x + 3 + (28 - seal_char.width) / 2, seal_y + 3, PAPER)
    )


def render(fonts: Fonts) -> str:
    rng = random.Random(SEED)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Likith Lochan. DevOps, Backend/Full-Stack, Applied AI. A shinigami with an apple crouches on a cathedral tower under a blood moon while a black notebook falls.">
<defs>
  <clipPath id="frame"><rect width="{W}" height="{H}" rx="16"/></clipPath>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{SKY[0]}"/><stop offset="0.6" stop-color="{SKY[1]}"/><stop offset="1" stop-color="{SKY[2]}"/>
  </linearGradient>
  <radialGradient id="halo"><stop offset="0" stop-color="#ff4a3a" stop-opacity="0.30"/><stop offset="0.4" stop-color="#b3161c" stop-opacity="0.10"/><stop offset="1" stop-color="#b3161c" stop-opacity="0"/></radialGradient>
  <radialGradient id="moonFace" cx="0.4" cy="0.38" r="0.72"><stop offset="0" stop-color="#f6c9a8"/><stop offset="0.45" stop-color="#d9603f"/><stop offset="1" stop-color="#8a1b17"/></radialGradient>
  <radialGradient id="moonShade" cx="0.32" cy="0.3" r="0.95"><stop offset="0.5" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#1a0203" stop-opacity="0.6"/></radialGradient>
  <radialGradient id="appleSkin" cx="0.35" cy="0.35" r="0.8"><stop offset="0" stop-color="#ff6a5a"/><stop offset="0.6" stop-color="#d4141d"/><stop offset="1" stop-color="#6d070b"/></radialGradient>
  <radialGradient id="vignette" cx="0.5" cy="0.45" r="0.78"><stop offset="0.55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.55"/></radialGradient>
  <filter id="cloud" x="-30%" y="-300%" width="160%" height="700%"><feGaussianBlur stdDeviation="8"/></filter>
  <filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <filter id="grain" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="4" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 1  0 0 0 0 0.9  0 0 0 0 0.85  0 0 0 0.07 0"/>
  </filter>
</defs>
<g clip-path="url(#frame)">
  <rect width="{W}" height="{H}" fill="url(#sky)"/>
  {_stars(rng)}
  {_moon()}
  {_clouds(rng)}
  {_crows()}
  {_falling_note(fonts)}
  {_skyline(rng)}
  {_tower()}
  {_ryuk()}
  {_feathers(rng)}
  {_embers(rng)}
  <rect width="{W}" height="{H}" fill="url(#vignette)"/>
  <rect width="{W}" height="{H}" filter="url(#grain)"/>
  {_type(fonts)}
  {_calligraphy(fonts)}
</g>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="#2a1a1a"/>
</svg>'''
