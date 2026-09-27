"""The cards, drawn as manga panels: the suspect file (whoami), the note's rules, chapter
title headers and the contact tags. Thick panel borders, screentone and speed lines;
in light mode they are ink on paper, like a printed page."""

import math
import random
from html import escape

from banner import Fonts
from content import EPIGRAPH, RULES, STATUS, WHOAMI
from fontpaths import Shaped, fit_path, text_path
from theme import MONO, Theme

CARD_W = 860
PAD = 40
BAR_H = 46
# Cards are drawn at 860 wide and shown at about half that, so text is sized for 2x.
ROW_SIZE = 19
APPLE = (
    "M0 -5 C-3 -8.5 -8.5 -6.5 -8.5 -0.5 C-8.5 5.5 -4.5 9.5 -1.5 8.4 C-0.6 8 0.6 8 1.5 8.4 "
    "C4.5 9.5 8.5 5.5 8.5 -0.5 C8.5 -6.5 3 -8.5 0 -5 Z"
)


def emblem(theme: Theme, cx: float, cy: float, scale: float = 0.62, leaf: str | None = None) -> str:
    """Ryuk's apple, small."""
    leaf = leaf or theme.muted
    return (
        f'<g transform="translate({cx} {cy}) scale({scale})">'
        f'<path d="{APPLE}" fill="{theme.apple}"/>'
        f'<path d="M0 -5 Q0.4 -9 2.4 -10.5" fill="none" stroke="{leaf}" stroke-width="1.4" stroke-linecap="round"/>'
        f'<path d="M1.4 -8.4 C4 -11.5 8 -10.5 8.5 -9 C6 -7.5 3.5 -7.2 1.4 -8.4 Z" fill="{leaf}"/>'
        '</g>'
    )


def _path(shape: Shaped, x: float, baseline: float, fill: str, attrs: str = "", children: str = "") -> str:
    head = f'<path transform="translate({x:.1f} {baseline - shape.ascent:.1f})" d="{shape.d}" fill="{fill}"{attrs}'
    return f"{head}>{children}</path>" if children else f"{head}/>"


def _text(x: float, y: float, body: str, fill: str, size: float = 15, family: str = MONO,
          anchor: str = "start", extra: str = "") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" fill="{fill}" '
        f'text-anchor="{anchor}" xml:space="preserve"{extra}>{body}</text>'
    )


def _svg(width: float, height: float, label: str, body: str, defs: str = "") -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" role="img" aria-label="{escape(label)}">'
        f'<defs>{defs}</defs>{body}</svg>'
    )


def _fade_in(delay: float, dx: float = -6) -> str:
    """Held hidden until `delay`, then eased in. Starts at 0s and keeps the element's resting
    state visible, so a renderer that skips SMIL still shows everything."""
    dur = delay + 0.5
    hold = f"0;{delay / dur:.3f};1"
    return (
        f'<animate attributeName="opacity" values="0;0;1" keyTimes="{hold}" dur="{dur:.2f}s" fill="freeze"/>'
        f'<animateTransform attributeName="transform" type="translate" values="{dx} 0;{dx} 0;0 0" keyTimes="{hold}" '
        f'dur="{dur:.2f}s" fill="freeze"/>'
    )


def _written(shape: Shaped, x: float, baseline: float, fill: str, begin: float, dur: float) -> str:
    """Traced in ink and then filled, like a name going into the note. Filled at rest."""
    total = begin + dur + 0.5
    at = lambda t: f"{t / total:.3f}"
    return _path(
        shape, x, baseline, fill,
        f' stroke="{fill}" stroke-width="0.8" pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="0"',
        f'<animate attributeName="stroke-dashoffset" values="1;1;0" keyTimes="0;{at(begin)};{at(begin + dur)}" dur="{total:.2f}s" fill="freeze"/>'
        f'<animate attributeName="fill-opacity" values="0;0;1" keyTimes="0;{at(begin + dur * 0.8)};1" dur="{total:.2f}s" fill="freeze"/>',
    )


# ---- manga texture ---------------------------------------------------------------------

def tone_defs(theme: Theme, key: str, cx: float, cy: float, r: float, x: float, y: float, w: float, h: float) -> str:
    """A screentone patch: dots that fade out from (cx, cy) over radius r."""
    return (
        f'<pattern id="dots-{key}" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        f'<circle cx="3.5" cy="3.5" r="1.5" fill="{theme.tone}"/></pattern>'
        f'<radialGradient id="fade-{key}" gradientUnits="userSpaceOnUse" cx="{cx}" cy="{cy}" r="{r}">'
        '<stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
        f'<mask id="mask-{key}" maskUnits="userSpaceOnUse" x="{x}" y="{y}" width="{w}" height="{h}">'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#fade-{key})"/></mask>'
    )


def tone(key: str, x: float, y: float, w: float, h: float) -> str:
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#dots-{key})" mask="url(#mask-{key})"/>'


def _streaks(theme: Theme, rng: random.Random, x0: float, x1: float, y0: float, y1: float, count: int) -> str:
    """Horizontal speed lines racing right to left, the way a manga shows motion."""
    out = []
    for _ in range(count):
        y = rng.uniform(y0, y1)
        length = rng.uniform(60, 260)
        dur = rng.uniform(0.7, 1.8)
        out.append(
            f'<rect x="0" y="{y:.1f}" width="{length:.0f}" height="{rng.choice((1, 1, 1.5, 2))}" fill="{theme.streak}" '
            f'opacity="{rng.uniform(0.25, 0.8):.2f}">'
            f'<animate attributeName="x" values="{x1:.0f};{x0 - length:.0f}" dur="{dur:.2f}s" begin="-{rng.uniform(0, dur):.2f}s" repeatCount="indefinite"/></rect>'
        )
    return "".join(out)


def _splatter(theme: Theme, rng: random.Random, cx: float, cy: float, spread: float) -> str:
    """A spray of blood: one blot, satellites around it, a couple of runs downward."""
    out = [f'<circle cx="{cx}" cy="{cy}" r="{spread * 0.16:.1f}" fill="{theme.accent}"/>']
    for _ in range(22):
        d = rng.uniform(0.2, 1) * spread
        a = rng.uniform(0, math.tau)
        out.append(
            f'<circle cx="{cx + d * math.cos(a):.1f}" cy="{cy + d * math.sin(a) * 0.7:.1f}" '
            f'r="{rng.uniform(1, 4.5) * (1.2 - d / spread):.1f}" fill="{theme.accent}"/>'
        )
    for dx in (-8, 6):
        run = rng.uniform(20, 48)
        out.append(
            f'<path d="M{cx + dx - 2.5} {cy} L{cx + dx - 1.5} {cy + run} Q{cx + dx} {cy + run + 6} {cx + dx + 1.5} {cy + run} '
            f'L{cx + dx + 2.5} {cy} Z" fill="{theme.accent}"/>'
        )
    return f'<g opacity="0.9">{"".join(out)}</g>'


def panel(theme: Theme, width: float, height: float, left: str, right: str) -> str:
    """A manga panel: square-cut, thick border, with an ink title strip across the top."""
    return (
        f'<rect x="2" y="2" width="{width - 4}" height="{height - 4}" rx="3" fill="{theme.surface}" '
        f'stroke="{theme.frame}" stroke-width="4"/>'
        f'<rect x="2" y="2" width="{width - 4}" height="{BAR_H}" fill="{theme.frame}"/>'
        + emblem(theme, 26, 25, 0.9, theme.surface)
        + _text(46, 31, left, theme.surface, 14, extra=' font-weight="700" letter-spacing="1.5"')
        + _text(width - 22, 31, escape(right), theme.surface, 13, anchor="end", extra=' letter-spacing="1.5"')
    )


# ---- whoami, as a Task Force suspect file ----------------------------------------------

def _rows(theme: Theme, top: float) -> tuple[list[str], float, float]:
    """The key/value groups, each row fading in after the last. Returns (svg, next y, next delay)."""
    body, y, delay = [], top, 1.2
    for group_index, group in enumerate(WHOAMI):
        body.append(f'<line x1="{PAD}" y1="{y - 22:.0f}" x2="{CARD_W - PAD}" y2="{y - 22:.0f}" stroke="{theme.frame}" stroke-width="1.5" stroke-dasharray="6 5" opacity="0.5"/>')
        y += 14
        for key, value in group:
            row = _text(PAD, y, escape(key.upper()), theme.accent, 15, extra=' letter-spacing="2"') + _text(PAD + 150, y, escape(value), theme.ink, ROW_SIZE)
            body.append(f'<g>{row}{_fade_in(delay)}</g>')
            y += 37
            delay += 0.07
        if group_index < len(WHOAMI) - 1:
            y += 20
    return body, y, delay


def _heartbeat(theme: Theme, x: float, y: float) -> str:
    """A small ECG trace that keeps beating: the subject is, for now, alive."""
    trace = f"M{x} {y} l12 0 l4 -3 l4 3 l4 0 l3 -14 l4 24 l3 -10 l5 0 l4 -4 l4 4 l11 0"
    return (
        f'<path d="{trace}" fill="none" stroke="{theme.faint}" stroke-width="2" stroke-linejoin="round"/>'
        f'<path d="{trace}" fill="none" stroke="{theme.live}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" '
        'pathLength="100" stroke-dasharray="22 78">'
        '<animate attributeName="stroke-dashoffset" values="100;0" dur="1.6s" repeatCount="indefinite"/></path>'
    )


def _stamp(theme: Theme, fonts: Fonts, x: float, y: float) -> str:
    """A red rubber stamp that slams onto the file a moment after it opens."""
    word = text_path(fonts.serif_bold, "UNDER SURVEILLANCE", 24, tracking=0.12)
    w, h = word.width + 36, 48
    total, begin = 2.4, 1.6
    at = lambda t: f"{t / total:.3f}"
    return (
        f'<g transform="translate({x} {y}) rotate(-9)"><g>'
        f'<rect x="{-w / 2:.1f}" y="{-h / 2}" width="{w:.1f}" height="{h}" rx="4" fill="none" stroke="{theme.accent}" stroke-width="3.5"/>'
        f'<rect x="{-w / 2 + 6:.1f}" y="{-h / 2 + 6}" width="{w - 12:.1f}" height="{h - 12}" rx="2" fill="none" stroke="{theme.accent}" stroke-width="1.2"/>'
        + _path(word, -word.width / 2, word.ascent / 2 - 2, theme.accent)
        + f'<animateTransform attributeName="transform" type="scale" values="2.2;2.2;0.94;1" keyTimes="0;{at(begin)};{at(begin + 0.18)};1" dur="{total}s" fill="freeze"/>'
        f'<animate attributeName="opacity" values="0;0;0.92;0.92" keyTimes="0;{at(begin)};{at(begin + 0.12)};1" dur="{total}s" fill="freeze"/>'
        '</g></g>'
    )


def whoami(theme: Theme, fonts: Fonts, footer_left: str, footer_right: str) -> str:
    height = 1000
    name = text_path(fonts.gothic, "Likith Lochan", 70)
    defs = tone_defs(theme, "w", CARD_W, height, 520, 0, 0, CARD_W, height)
    body = [
        panel(theme, CARD_W, height, "KIRA INVESTIGATION TASK FORCE", "SUBJECT FILE No. 1231"),
        tone("w", 4, 50, CARD_W - 8, height - 54),
        _text(PAD, 92, "SUBJECT", theme.muted, 14, extra=' letter-spacing="4"'),
        _written(name, PAD, 168, theme.ink, 0.2, 1.8),
        _stamp(theme, fonts, 640, 110),
    ]
    rows, y, delay = _rows(theme, 228)
    body.extend(rows)

    y += 16
    status = _heartbeat(theme, PAD, y - 6) + _text(PAD + 92, y, escape(STATUS), theme.live, ROW_SIZE)
    body.append(f'<g>{status}{_fade_in(delay)}</g>')

    body.append(f'<line x1="22" y1="{height - 44}" x2="{CARD_W - 22}" y2="{height - 44}" stroke="{theme.frame}" stroke-width="1.5" opacity="0.5"/>')
    body.append(_text(22, height - 18, escape(footer_left), theme.muted, 12))
    body.append(_text(CARD_W - 22, height - 18, escape(footer_right), theme.muted, 12, anchor="end"))
    return _svg(CARD_W, height, "Kira Task Force subject file: Likith Lochan, DevOps, Backend/Full-Stack and Applied AI", "".join(body), defs)


# ---- the note's rules ------------------------------------------------------------------

WIDE = 1740


def rules(theme: Theme, fonts: Fonts) -> str:
    """The note's rules page, with Rule I quoted and three rules for how I build."""
    height = 380
    top = BAR_H + 4
    column = (WIDE - 2 * PAD - 70) / 3
    left = PAD + 70
    rng = random.Random(4)
    lines = "".join(
        f'<line x1="14" y1="{y}" x2="{WIDE - 14}" y2="{y}" stroke="{theme.faint}"/>'
        for y in range(top + 96, height - 20, 38)
    )
    title = text_path(fonts.gothic, "HOW TO USE IT", 52, tracking=0.04)
    epigraph = text_path(fonts.italic, EPIGRAPH, 30)
    defs = tone_defs(theme, "r", WIDE, height, 700, 0, 0, WIDE, height)
    body = [
        panel(theme, WIDE, height, "THE RULES OF THE NOTE", "DEATH NOTE · HOW TO USE IT"),
        tone("r", 4, top, WIDE - 8, height - top - 4),
        lines,
        f'<line x1="{left - 26}" y1="{top}" x2="{left - 26}" y2="{height - 6}" stroke="{theme.accent}" stroke-opacity="0.6" stroke-width="2"/>',
        _written(title, left, top + 66, theme.ink, 0.1, 1.6),
        _path(epigraph, WIDE - PAD - epigraph.width, top + 52, theme.accent),
        _text(WIDE - PAD, top + 80, "RULE I", theme.muted, 13, anchor="end", extra=' letter-spacing="4"'),
        _splatter(theme, rng, WIDE - PAD - epigraph.width - 60, top + 40, 40),
    ]
    for i, (heading_text, *evidence) in enumerate(RULES):
        x = left + i * column + (26 if i else 0)
        numeral = text_path(fonts.gothic, ("I", "II", "III")[i], 54)
        heading = fit_path(fonts.serif_bold, heading_text, 42, column - numeral.width - 60)
        group = (
            _path(numeral, x, top + 166, theme.accent) + _path(heading, x + numeral.width + 18, top + 162, theme.ink)
            + "".join(
                _path(text_path(fonts.italic, line, 30), x, top + 216 + k * 38, theme.muted) for k, line in enumerate(evidence)
            )
        )
        body.append(f'<g>{group}{_fade_in(1.2 + i * 0.35)}</g>')
    return _svg(WIDE, height, "How to use it. Rule I: the human whose name is written in this note shall die. "
                + "; ".join(r[0] for r in RULES), "".join(body), defs)


# ---- chapter title headers -------------------------------------------------------------

def header(theme: Theme, fonts: Fonts, number: int, total: int, kanji: str, english: str) -> str:
    """A manga chapter title: red number block, brush kanji, the English title, speed lines."""
    height = 132
    box = f"M4 14 L{WIDE - 4} 4 L{WIDE - 18} {height - 6} L14 {height - 2} Z"
    rng = random.Random(number)
    num = text_path(fonts.gothic, f"{number:02d}", 64)
    word = text_path(fonts.brush, kanji, 70)
    title = text_path(fonts.serif_bold, english.upper(), 50, tracking=0.14)
    block_w = num.width + 56
    kx = 44 + block_w + 30
    tx = kx + word.width + 34
    body = (
        f'<clipPath id="box"><path d="{box}"/></clipPath>'
        f'<path d="{box}" fill="{theme.surface}"/>'
        f'<g clip-path="url(#box)">{_streaks(theme, rng, 0, WIDE, 18, height - 10, 46)}'
        f'<path d="M26 12 L{26 + block_w} 10 L{12 + block_w} {height} L12 {height} Z" fill="{theme.accent}"/></g>'
        f'<path d="{box}" fill="none" stroke="{theme.frame}" stroke-width="4" stroke-linejoin="round"/>'
        f'<g>{_path(num, 24 + (block_w - num.width) / 2, 92, theme.surface)}{_fade_in(0.1, -20)}</g>'
        f'<g>{_path(word, kx, 100, theme.ink)}{_fade_in(0.3, -20)}</g>'
        f'<g>{_path(title, tx, 88, theme.ink)}{_fade_in(0.45, -20)}</g>'
        + _text(WIDE - 60, 60, f"FILE {number:02d} / {total:02d}", theme.muted, 16, anchor="end", extra=' letter-spacing="4"')
        + _text(WIDE - 60, 88, "DEATH NOTE", theme.accent, 16, anchor="end", extra=' letter-spacing="6"')
    )
    return _svg(WIDE, height, f"File {number:02d}: {kanji} {english}", body)


# ---- contact tags ----------------------------------------------------------------------

def link_button(theme: Theme, fonts: Fonts, label: str) -> str:
    width, height = 320, 80
    shape = f"M10 4 L{width - 4} 4 L{width - 14} {height - 4} L4 {height - 4} Z"
    word = text_path(fonts.serif_bold, label.upper(), 26, tracking=0.12)
    body = (
        f'<path d="{shape}" fill="{theme.surface}" stroke="{theme.frame}" stroke-width="3.5" stroke-linejoin="round"/>'
        f'<path d="M10 4 L62 4 L52 {height - 4} L4 {height - 4} Z" fill="{theme.accent}"/>'
        + emblem(theme, 32, 42, 1.3, theme.surface)
        + _path(word, 80, 52, theme.ink)
        + _text(width - 30, 53, "↗", theme.accent, 26, anchor="end", extra=' font-weight="700"')
    )
    return _svg(width, height, label, body)
