"""The terminal cards: whoami, the notebook's pages (projects), its rules, headers and links."""

from html import escape

from banner import Fonts
from content import HOST, RULES, STATUS, WHOAMI, Project
from fontpaths import Shaped, fit_path, text_path
from theme import MONO, SANS, Theme

CARD_W = 860
PAD = 40
MONO_ADVANCE = 0.6  # JetBrains Mono / Menlo advance width, in ems
# Cards are drawn at 860 wide and shown at about half that, so text is sized for 2x.
ROW_SIZE = 19
APPLE = (
    "M0 -5 C-3 -8.5 -8.5 -6.5 -8.5 -0.5 C-8.5 5.5 -4.5 9.5 -1.5 8.4 C-0.6 8 0.6 8 1.5 8.4 "
    "C4.5 9.5 8.5 5.5 8.5 -0.5 C8.5 -6.5 3 -8.5 0 -5 Z"
)


def emblem(theme: Theme, cx: float, cy: float, scale: float = 0.62) -> str:
    """Ryuk's apple, small: the mark in every card's title bar."""
    return (
        f'<g transform="translate({cx} {cy}) scale({scale})">'
        f'<path d="{APPLE}" fill="{theme.apple}"/>'
        f'<path d="M0 -5 Q0.4 -9 2.4 -10.5" fill="none" stroke="{theme.muted}" stroke-width="1.4" stroke-linecap="round"/>'
        f'<path d="M1.4 -8.4 C4 -11.5 8 -10.5 8.5 -9 C6 -7.5 3.5 -7.2 1.4 -8.4 Z" fill="{theme.muted}"/>'
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


def _svg(width: float, height: float, label: str, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" role="img" aria-label="{escape(label)}">{body}</svg>'
    )


def _chrome(theme: Theme, width: int, height: int, title: str, right: str) -> str:
    return (
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="14" fill="{theme.surface}" stroke="{theme.border}"/>'
        f'<line x1="1" y1="44" x2="{width - 1}" y2="44" stroke="{theme.border}"/>'
        + emblem(theme, 30, 23)
        + _text(46, 27, f'{HOST} <tspan fill="{theme.faint}">·</tspan> {escape(title)}', theme.muted, 12.5)
        + _text(width - 22, 27, escape(right), theme.muted, 12.5, anchor="end")
    )


def _fade_in(delay: float) -> str:
    """Held hidden until `delay`, then eased in. Starts at 0s and keeps the element's resting
    state visible, so a renderer that skips SMIL still shows everything."""
    dur = delay + 0.5
    hold = f"0;{delay / dur:.3f};1"
    return (
        f'<animate attributeName="opacity" values="0;0;1" keyTimes="{hold}" dur="{dur:.2f}s" fill="freeze"/>'
        f'<animateTransform attributeName="transform" type="translate" values="-6 0;-6 0;0 0" keyTimes="{hold}" '
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


# ---- whoami ----------------------------------------------------------------------------

def _rows(theme: Theme, top: float) -> tuple[list[str], float, float]:
    """The key/value groups, each row fading in after the last. Returns (svg, next y, next delay)."""
    body, y, delay = [], top, 1.2
    for group_index, group in enumerate(WHOAMI):
        body.append(f'<line x1="{PAD}" y1="{y - 22:.0f}" x2="{CARD_W - PAD}" y2="{y - 22:.0f}" stroke="{theme.border}"/>')
        y += 14
        for key, value in group:
            row = _text(PAD, y, escape(key), theme.muted, ROW_SIZE) + _text(PAD + 150, y, escape(value), theme.ink, ROW_SIZE)
            body.append(f'<g>{row}{_fade_in(delay)}</g>')
            y += 37
            delay += 0.07
        if group_index < len(WHOAMI) - 1:
            y += 20
    return body, y, delay


def _heartbeat(theme: Theme, x: float, y: float) -> str:
    """A small ECG trace that keeps beating: the status line's pulse."""
    trace = f"M{x} {y} l12 0 l4 -3 l4 3 l4 0 l3 -14 l4 24 l3 -10 l5 0 l4 -4 l4 4 l11 0"
    return (
        f'<path d="{trace}" fill="none" stroke="{theme.faint}" stroke-width="2" stroke-linejoin="round"/>'
        f'<path d="{trace}" fill="none" stroke="{theme.live}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" '
        'pathLength="100" stroke-dasharray="22 78">'
        '<animate attributeName="stroke-dashoffset" values="100;0" dur="1.6s" repeatCount="indefinite"/></path>'
    )


def whoami(theme: Theme, fonts: Fonts, footer_left: str, footer_right: str) -> str:
    height = 1000
    name = text_path(fonts.gothic, "Likith Lochan", 66)
    body = [
        _chrome(theme, CARD_W, height, "~/whoami", "zsh"),
        _text(PAD, 94, f'<tspan fill="{theme.accent}">$</tspan> whoami', theme.ink, ROW_SIZE),
        _written(name, PAD, 166, theme.ink, 0.2, 1.8),
    ]
    rows, y, delay = _rows(theme, 226)
    body.extend(rows)

    y += 16
    status = _heartbeat(theme, PAD, y - 6) + _text(PAD + 92, y, escape(STATUS), theme.live, ROW_SIZE)
    body.append(f'<g>{status}{_fade_in(delay)}</g>')
    prompt_y = y + 44
    dollar = _text(PAD, prompt_y, "$", theme.accent, ROW_SIZE)
    cursor = (
        f'<rect x="{PAD + 22}" y="{prompt_y - 17:.0f}" width="11" height="22" fill="{theme.ink}">'
        '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" repeatCount="indefinite"/></rect>'
    )
    body.append(f'<g>{dollar}{cursor}{_fade_in(delay + 0.1)}</g>')

    body.append(f'<line x1="22" y1="{height - 44}" x2="{CARD_W - 22}" y2="{height - 44}" stroke="{theme.border}"/>')
    body.append(_text(22, height - 18, escape(footer_left), theme.muted, 12))
    body.append(_text(CARD_W - 22, height - 18, escape(footer_right), theme.muted, 12, anchor="end"))
    return _svg(CARD_W, height, "Likith Lochan: DevOps, Backend/Full-Stack and Applied AI", "".join(body))


# ---- the notebook's pages: one per project ---------------------------------------------

def _draw_in(path: str, stroke: str, delay: float, width: float = 1.6) -> str:
    """A stroke that draws itself once, then stays. Drawn at rest, for the same reason as _fade_in."""
    dur = delay + 1.4
    return (
        f'<path d="{path}" fill="none" stroke="{stroke}" stroke-width="{width}" stroke-linecap="round" '
        f'stroke-dasharray="400" stroke-dashoffset="0">'
        f'<animate attributeName="stroke-dashoffset" values="400;400;0" keyTimes="0;{delay / dur:.3f};1" '
        f'dur="{dur:.2f}s" fill="freeze"/></path>'
    )


def _node(x: float, y: float, fill: str, r: float = 5) -> str:
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"/>'


def _diagram(slug: str, theme: Theme) -> str:
    """A small signature drawing per project, about 170 x 90."""
    red, bone, quiet = theme.accent, theme.bone, theme.muted
    if slug == "ghostops":  # alert -> three agents -> sandbox gate -> PR, or abort
        bell = (
            f'<path d="M0 30 Q0 14 11 14 Q22 14 22 30 L25 36 L-3 36 Z" fill="none" stroke="{red}" stroke-width="1.6"/>'
            f'<circle cx="11" cy="40" r="2.4" fill="{red}"><animate attributeName="opacity" values="1;0.2;1" dur="1.2s" repeatCount="indefinite"/></circle>'
        )
        body = bell + _draw_in("M28 30 L44 30", quiet, 0.4, 1.3)
        for i, x in enumerate((52, 76, 100)):
            body += _node(x, 30, bone, 6)
            if i < 2:
                body += _draw_in(f"M{x + 7} 30 L{x + 17} 30", quiet, 0.5 + i * 0.12, 1.3)
        body += _draw_in("M107 30 L118 30", quiet, 0.8, 1.3)
        body += f'<rect x="118" y="16" width="28" height="28" rx="4" fill="none" stroke="{bone}" stroke-width="1.5" stroke-dasharray="4 3"/>'
        body += _draw_in("M146 30 L160 30", red, 1.0) + _node(166, 30, red, 6)
        body += _draw_in("M132 44 L132 66", quiet, 1.1, 1.2)
        body += f'<path d="M127 70 L137 80 M127 80 L137 70" stroke="{quiet}" stroke-width="1.5"/>'
        return body + _text(160, 58, "PR", red, 12, anchor="middle")
    if slug == "aethermed":  # replicas scaling 2 -> 8 under a load curve
        bars = []
        for i, h in enumerate((18, 18, 30, 42, 54, 62, 70, 74)):
            x = 4 + i * 20
            bars.append(
                f'<rect x="{x}" y="{86 - h}" width="12" height="{h}" rx="2" fill="{bone}" opacity="{0.45 + i * 0.06:.2f}">'
                f'<animate attributeName="height" values="0;0;{h}" keyTimes="0;{(0.4 + i * 0.1) / (1.2 + i * 0.1):.3f};1" dur="{1.2 + i * 0.1:.1f}s" fill="freeze"/>'
                f'<animate attributeName="y" values="86;86;{86 - h}" keyTimes="0;{(0.4 + i * 0.1) / (1.2 + i * 0.1):.3f};1" dur="{1.2 + i * 0.1:.1f}s" fill="freeze"/></rect>'
            )
        load = "M0 74 C30 72 44 60 64 44 S104 12 124 10 S156 8 170 6"
        return "".join(bars) + _draw_in(load, red, 0.6, 2) + _node(170, 6, red, 4)
    if slug == "sahayak":  # a chat message fanning out to four tools, into one market
        bubble = (
            f'<rect x="0" y="28" width="44" height="30" rx="8" fill="none" stroke="{bone}" stroke-width="1.6"/>'
            f'<path d="M10 58 L8 68 L20 58" fill="none" stroke="{bone}" stroke-width="1.6" stroke-linejoin="round"/>'
            + "".join(f'<circle cx="{x}" cy="43" r="2.4" fill="{bone}"><animate attributeName="opacity" values="0.2;1;0.2" dur="1.2s" begin="{i * 0.2:.1f}s" repeatCount="indefinite"/></circle>' for i, x in enumerate((13, 22, 31)))
        )
        tools = "".join(
            _draw_in(f"M48 43 C70 43 70 {y} 92 {y}", quiet, 0.5 + i * 0.1, 1.2)
            + f'<rect x="92" y="{y - 6}" width="12" height="12" rx="3" fill="{bone}"/>'
            for i, y in enumerate((10, 32, 54, 76))
        )
        wires = "".join(_draw_in(f"M106 {y} C128 {y} 128 43 146 43", red, 0.9 + i * 0.08, 1.2) for i, y in enumerate((10, 32, 54, 76)))
        return bubble + tools + wires + _node(156, 43, red, 9) + _text(156, 48, "₹", theme.surface, 13, anchor="middle")
    # greencart: a cart, and the two ways out of it
    cart = (
        f'<path d="M0 20 L12 20 L20 58 L58 58 L66 30 L16 30" fill="none" stroke="{bone}" stroke-width="1.8" stroke-linejoin="round"/>'
        f'<circle cx="26" cy="68" r="4" fill="{bone}"/><circle cx="52" cy="68" r="4" fill="{bone}"/>'
    )
    routes = _draw_in("M72 44 C98 44 100 20 124 20", quiet, 0.5, 1.3) + _draw_in("M72 44 C98 44 100 68 124 68", red, 0.6, 1.3)
    coin = f'<circle cx="138" cy="20" r="11" fill="none" stroke="{bone}" stroke-width="1.6"/>' + _text(138, 25, "₹", bone, 13, anchor="middle")
    card = (
        f'<rect x="124" y="56" width="42" height="26" rx="4" fill="none" stroke="{red}" stroke-width="1.6"/>'
        f'<rect x="124" y="62" width="42" height="5" fill="{red}"/>'
    )
    return cart + routes + coin + card


def _chip(x: float, y: float, label: str, theme: Theme) -> tuple[str, float]:
    width = len(label) * 15 * MONO_ADVANCE + 28
    svg = (
        f'<rect x="{x:.1f}" y="{y}" width="{width:.1f}" height="34" rx="17" fill="none" stroke="{theme.border}"/>'
        + _text(x + width / 2, y + 22.5, escape(label), theme.muted, 15, anchor="middle")
    )
    return svg, width


def project(theme: Theme, fonts: Fonts, index: int, p: Project) -> str:
    height = 480
    name = text_path(fonts.gothic, p.name, 54)
    metric = text_path(fonts.serif_bold, p.metric, 68)
    body = [
        f'<rect x="0.5" y="0.5" width="{CARD_W - 1}" height="{height - 1}" rx="14" fill="{theme.surface}" stroke="{theme.border}"/>',
        # A red margin line down the page, like the note's ruled paper.
        f'<line x1="22" y1="18" x2="22" y2="{height - 18}" stroke="{theme.accent}" stroke-opacity="0.35"/>',
        _text(PAD, 48, f"PAGE {index:02d}  ·  {escape(p.kind.upper())}", theme.muted, 14.5, extra=' letter-spacing="1.5"'),
        _text(CARD_W - PAD, 48, "SOURCE ↗", theme.accent, 14.5, anchor="end", extra=' letter-spacing="2"'),
        _written(name, PAD, 118, theme.ink, 0.2, 1.4),
        _text(PAD, 150, escape(p.context), theme.muted, 16),
        f'<g transform="translate({CARD_W - PAD - 172} 72)">{_diagram(p.slug, theme)}</g>',
    ]
    body += [_text(PAD, 198 + i * 31, escape(line), theme.ink, 22, SANS, extra=' opacity="0.86"') for i, line in enumerate(p.lines)]
    body.append(f'<line x1="{PAD}" y1="296" x2="{CARD_W - PAD}" y2="296" stroke="{theme.border}"/>')
    body.append(_path(metric, PAD, 374, theme.accent))
    label_x = PAD + metric.width + 24
    body += [_text(label_x, 342 + i * 27, escape(line), theme.muted, 19, SANS) for i, line in enumerate(p.metric_label)]
    x = PAD
    for label in p.stack:
        chip, width = _chip(x, 408, label, theme)
        body.append(chip)
        x += width + 10
    return _svg(CARD_W, height, f"{p.name}: {p.kind}", "".join(body))


# ---- How to use it, headers, links -----------------------------------------------------

WIDE = 1740


def rules(theme: Theme, fonts: Fonts) -> str:
    """The note's rules page: ruled lines, a red margin, and three rules for how I build."""
    height = 340
    column = (WIDE - 2 * PAD - 70) / 3
    left = PAD + 70
    lines = "".join(
        f'<line x1="14" y1="{y}" x2="{WIDE - 14}" y2="{y}" stroke="{theme.faint}" stroke-opacity="0.7"/>'
        for y in range(108, height - 20, 38)
    )
    title = text_path(fonts.gothic, "How to use it", 50)
    body = [
        f'<rect x="0.5" y="0.5" width="{WIDE - 1}" height="{height - 1}" rx="14" fill="{theme.surface}" stroke="{theme.border}"/>',
        lines,
        f'<line x1="{left - 26}" y1="14" x2="{left - 26}" y2="{height - 14}" stroke="{theme.accent}" stroke-opacity="0.55" stroke-width="1.5"/>',
        _written(title, left, 74, theme.ink, 0.1, 1.6),
        _text(WIDE - PAD, 66, "DEATH NOTE · RULES I – III", theme.muted, 16, anchor="end", extra=' letter-spacing="3"'),
    ]
    for i, (heading_text, *evidence) in enumerate(RULES):
        x = left + i * column + (26 if i else 0)
        numeral = text_path(fonts.gothic, ("I", "II", "III")[i], 54)
        heading = fit_path(fonts.serif_bold, heading_text, 42, column - numeral.width - 60)
        group = (
            _path(numeral, x, 176, theme.accent) + _path(heading, x + numeral.width + 18, 172, theme.ink)
            + "".join(
                _path(text_path(fonts.italic, line, 30), x, 226 + k * 38, theme.muted) for k, line in enumerate(evidence)
            )
        )
        body.append(f'<g>{group}{_fade_in(1.2 + i * 0.35)}</g>')
    return _svg(WIDE, height, "How to use it: " + "; ".join(r[0] for r in RULES), "".join(body))


def header(theme: Theme, command: str) -> str:
    height, size = 70, 26
    prompt = f"{HOST} ~ $ "
    text_end = (len(prompt) + len(command)) * size * MONO_ADVANCE
    caret = (
        f'<rect x="{text_end + 6:.0f}" y="24" width="13" height="26" fill="{theme.accent}">'
        '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" repeatCount="indefinite"/></rect>'
    )
    body = (
        _text(0, 44, f'<tspan fill="{theme.muted}">{HOST}</tspan> <tspan fill="{theme.accent}">~ $</tspan> '
              f'{escape(command)}', theme.ink, size)
        + caret
        + f'<line x1="{text_end + 44:.0f}" y1="36" x2="{WIDE - 70}" y2="36" stroke="{theme.border}"/>'
        + emblem(theme, WIDE - 32, 37, 1.5)
    )
    return _svg(WIDE, height, f"$ {command}", body)


def link_button(theme: Theme, label: str) -> str:
    width, height = 300, 72
    body = (
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="36" fill="{theme.surface}" stroke="{theme.border}"/>'
        + emblem(theme, 40, 37, 1.1)
        + _text(64, 45, escape(label), theme.ink, 21, SANS)
        + _text(width - 32, 45, "↗", theme.accent, 22, SANS, anchor="end")
    )
    return _svg(width, height, label, body)
