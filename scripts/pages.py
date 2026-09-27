"""The profile's pages, each one showing live data from data.Profile.

Black pages, blood-red accents, and four voices of type: handwriting for anything written
into the note, blackletter for titles, a serif for prose, and mono for labels. All text is
converted to paths (fontpaths.py) so it renders the same on every machine.
"""

import math
from dataclasses import dataclass
from datetime import date
from html import escape

from data import Profile, Repo
from fontpaths import FontRef, Shaped, fit_path, text_path

PAGE = "#0e0b0b"
EDGE = "#2a2020"
RULE = "#221a1a"
INK = "#ece4d6"
MUTED = "#8a7f76"
FAINT = "#3b302e"
RED = "#d4202c"
DEEP = "#7c1119"

HALF, WIDE = 860, 1740
PAD = 44


@dataclass(frozen=True)
class Fonts:
    hand: FontRef       # handwriting: names and numbers written into the note
    gothic: FontRef     # titles
    old_english: FontRef  # L's letter
    serif: FontRef
    serif_bold: FontRef
    italic: FontRef
    mono: FontRef
    brush: FontRef      # Japanese


# ---- primitives ------------------------------------------------------------------------

def _svg(w: float, h: float, label: str, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}" '
        f'role="img" aria-label="{escape(label)}"><defs>'
        '<filter id="paper" x="0" y="0" width="100%" height="100%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="3" result="n"/>'
        '<feColorMatrix in="n" type="matrix" values="0 0 0 0 1  0 0 0 0 0.95  0 0 0 0 0.9  0 0 0 0.045 0"/></filter>'
        f'</defs>{body}</svg>'
    )


def _at(shape: Shaped, x: float, baseline: float, fill: str, extra: str = "", children: str = "") -> str:
    head = f'<path transform="translate({x:.1f} {baseline - shape.ascent:.1f})" d="{shape.d}" fill="{fill}"{extra}'
    return f"{head}>{children}</path>" if children else f"{head}/>"


def _written(shape: Shaped, x: float, baseline: float, fill: str, begin: float, dur: float) -> str:
    """Traced as if by pen, then filled. At rest it is simply filled, so a viewer that
    doesn't run SVG animation still sees it."""
    total = begin + dur + 0.4
    k = lambda t: f"{t / total:.3f}"
    return _at(
        shape, x, baseline, fill,
        f' stroke="{fill}" stroke-width="0.7" pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="0"',
        f'<animate attributeName="stroke-dashoffset" values="1;1;0" keyTimes="0;{k(begin)};{k(begin + dur)}" dur="{total:.2f}s" fill="freeze"/>'
        f'<animate attributeName="fill-opacity" values="0;0;1" keyTimes="0;{k(begin + dur * 0.75)};1" dur="{total:.2f}s" fill="freeze"/>',
    )


def _appear(delay: float, dy: float = 6) -> str:
    """Hidden until `delay`, then eased in; visible at rest for renderers without SMIL."""
    dur = delay + 0.6
    kt = f"0;{delay / dur:.3f};1"
    return (
        f'<animate attributeName="opacity" values="0;0;1" keyTimes="{kt}" dur="{dur:.2f}s" fill="freeze"/>'
        f'<animateTransform attributeName="transform" type="translate" values="0 {dy};0 {dy};0 0" keyTimes="{kt}" dur="{dur:.2f}s" fill="freeze"/>'
    )


def _frame(w: float, h: float, left: str, right: str, f: Fonts) -> str:
    """The page: black paper with a little grain, a hairline edge, and a label row."""
    l = text_path(f.mono, left, 13, tracking=0.22)
    r = text_path(f.mono, right, 13, tracking=0.22)
    return (
        f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="6" fill="{PAGE}" stroke="{EDGE}" stroke-width="2"/>'
        f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="6" filter="url(#paper)"/>'
        f'<rect x="{PAD}" y="30" width="7" height="7" fill="{RED}"/>'
        + _at(l, PAD + 18, 38, MUTED) + _at(r, w - PAD - r.width, 38, MUTED)
        + f'<line x1="{PAD}" y1="58" x2="{w - PAD}" y2="58" stroke="{RULE}" stroke-width="1.5"/>'
    )


def _footer(w: float, h: float, p: Profile, f: Fonts, right: str = "") -> str:
    left = f"updated {p.today:%d %b %Y}".replace(" 0", " ") if p.live else "preview data"
    a = text_path(f.mono, left, 12, tracking=0.1)
    out = f'<line x1="{PAD}" y1="{h - 46}" x2="{w - PAD}" y2="{h - 46}" stroke="{RULE}" stroke-width="1.5"/>' + _at(a, PAD, h - 20, FAINT if p.live else RED)
    if right:
        b = text_path(f.mono, right, 12, tracking=0.1)
        out += _at(b, w - PAD - b.width, h - 20, FAINT)
    return out


def _wrap(font: FontRef, text: str, size: float, width: float, lines: int) -> list[str]:
    words, out, cur = text.split(), [], ""
    for word in words:
        test = f"{cur} {word}".strip()
        if text_path(font, test, size).width <= width:
            cur = test
        else:
            out.append(cur)
            cur = word
            if len(out) == lines:
                break
    if len(out) < lines and cur:
        out.append(cur)
    if len(out) == lines and len(" ".join(out)) < len(text):
        while out[-1] and text_path(font, out[-1] + "…", size).width > width:
            out[-1] = out[-1].rsplit(" ", 1)[0]
        out[-1] += "…"
    return out


def _ago(p: Profile, d: date) -> str:
    n = (p.today - d).days
    return "today" if n <= 0 else "yesterday" if n == 1 else f"{n} days ago"


# ---- episode title cards ---------------------------------------------------------------

def title_card(number: int, kanji: str, english: str, note: str, f: Fonts) -> str:
    """A section opener in the manner of the anime's episode titles."""
    h = 124
    ep = text_path(f.mono, f"EPISODE {number:02d}", 14, tracking=0.35)
    kj = text_path(f.brush, kanji, 64)
    en = text_path(f.serif_bold, english.upper(), 40, tracking=0.2)
    nt = text_path(f.italic, note, 24)
    x = 34
    body = (
        f'<rect x="1" y="1" width="{WIDE - 2}" height="{h - 2}" rx="6" fill="#070505" stroke="{EDGE}" stroke-width="2"/>'
        f'<rect x="1" y="1" width="8" height="{h - 2}" fill="{RED}"/>'
        f'<g>{_at(ep, x, 44, RED)}{_appear(0.1, 0)}</g>'
        f'<g>{_at(kj, x, 104, INK)}{_appear(0.25)}</g>'
        f'<g>{_at(en, x + kj.width + 28, 96, INK)}{_appear(0.4)}</g>'
        f'<line x1="{x + kj.width + 28}" y1="106" x2="{x + kj.width + 28 + en.width}" y2="106" stroke="{DEEP}" stroke-width="2"/>'
        + _at(nt, WIDE - PAD - nt.width, 84, MUTED)
    )
    return _svg(WIDE, h, f"Episode {number}: {kanji}, {english}", body)


# ---- page: identity --------------------------------------------------------------------

def identity(p: Profile, f: Fonts) -> str:
    h = 900
    name = text_path(f.hand, "Likith Lochan", 104)
    rows = [
        ("CONTRIBUTIONS", f"{p.contributions:,}", "in the last year"),
        ("CURRENT STREAK", str(p.current_streak), "day" if p.current_streak == 1 else "days"),
        ("LONGEST STREAK", str(p.longest_streak), "days, this year"),
        ("PUBLIC REPOS", str(p.repo_count), "written so far"),
        ("STARS", str(p.stars), "across them"),
        ("WRITING SINCE", str(p.since), "on GitHub"),
    ]
    body = [
        _frame(HALF, h, "DEATH NOTE  ·  PAGE 01", "IDENTITY", f),
        _written(name, PAD, 186, INK, 0.2, 2.2),
        f'<rect x="{PAD}" y="210" width="130" height="3" fill="{RED}"/>',
        _at(text_path(f.serif_bold, "DevOps · Backend/Full-Stack · Applied AI", 30), PAD, 262, INK),
        _at(text_path(f.italic, "CS undergraduate, APS College of Engineering", 26), PAD, 298, MUTED),
    ]
    y = 380
    for i, (label, value, unit) in enumerate(rows):
        lab = text_path(f.mono, label, 13, tracking=0.2)
        val = text_path(f.hand, value, 58)
        un = text_path(f.italic, unit, 24)
        row = (
            f'<line x1="{PAD}" y1="{y + 14}" x2="{HALF - PAD}" y2="{y + 14}" stroke="{RULE}" stroke-width="1.5"/>'
            + _at(lab, PAD, y - 6, MUTED) + _at(val, 300, y + 4, RED if i == 0 else INK) + _at(un, 300 + val.width + 16, y, MUTED)
        )
        body.append(f"<g>{row}{_appear(1.6 + i * 0.12)}</g>")
        y += 70
    body.append(_footer(HALF, h, p, f, "github.com/likith1231"))
    return _svg(HALF, h, f"Likith Lochan: {p.contributions} contributions in the last year, current streak {p.current_streak} days", "".join(body))


# ---- page: L's deduction ---------------------------------------------------------------

def deduction(p: Profile, f: Fonts) -> str:
    """L's line from the series, answered with real activity from the last 30 days."""
    h = 900
    pct = round(100 * p.active30 / 30)
    days = p.last30
    top = max(days) or 1
    letter = text_path(f.old_english, "L", 560)
    number = text_path(f.gothic, f"{pct}%", 230)
    body = [
        _frame(HALF, h, "L  ·  DEDUCTION", "LAST 30 DAYS", f),
        _at(letter, HALF - letter.width - 10, 700, INK, ' opacity="0.05"'),
        _at(text_path(f.italic, "“The probability that", 40), PAD, 150, INK),
        _at(text_path(f.italic, "likith1231 is Kira is…”", 40), PAD, 198, INK),
        f'<g>{_at(number, PAD - 6, 440, RED)}{_appear(0.6, 12)}</g>',
    ]
    # One bar per day, tallest on the busiest day; empty days leave a faint tick.
    x0, base, span, bw = PAD, 690, HALF - 2 * PAD, (HALF - 2 * PAD) / 30
    for i, n in enumerate(days):
        x = x0 + i * bw + 3
        if n:
            bh = 20 + 170 * n / top
            delay = 1.0 + i * 0.03
            body.append(
                f'<rect x="{x:.1f}" y="{base - bh:.1f}" width="{bw - 6:.1f}" height="{bh:.1f}" fill="{RED}" opacity="{0.45 + 0.55 * n / top:.2f}">'
                f'<animate attributeName="height" values="0;0;{bh:.1f}" keyTimes="0;{delay / (delay + 0.5):.3f};1" dur="{delay + 0.5:.2f}s" fill="freeze"/>'
                f'<animate attributeName="y" values="{base};{base};{base - bh:.1f}" keyTimes="0;{delay / (delay + 0.5):.3f};1" dur="{delay + 0.5:.2f}s" fill="freeze"/></rect>'
            )
        else:
            body.append(f'<rect x="{x:.1f}" y="{base - 3}" width="{bw - 6:.1f}" height="3" fill="{FAINT}"/>')
    body.append(f'<line x1="{PAD}" y1="{base + 1}" x2="{HALF - PAD}" y2="{base + 1}" stroke="{EDGE}" stroke-width="1.5"/>')
    body.append(_at(text_path(f.mono, "30 DAYS AGO", 12, tracking=0.2), PAD, base + 30, FAINT))
    t = text_path(f.mono, "TODAY", 12, tracking=0.2)
    body.append(_at(t, HALF - PAD - t.width, base + 30, FAINT))
    cap = text_path(f.serif, f"Active on {p.active30} of the last 30 days. The deduction stands.", 26)
    body.append(_at(cap, PAD, base + 88, MUTED))
    body.append(_footer(HALF, h, p, f, "based on the contribution calendar"))
    return _svg(HALF, h, f"The probability that likith1231 is Kira is {pct} percent: active on {p.active30} of the last 30 days", "".join(body))


# ---- page: languages -------------------------------------------------------------------

def names(p: Profile, f: Fonts) -> str:
    """Top languages across public repos, written in like names, each with its share."""
    h = 470
    langs = p.languages[:6]
    top = langs[0][2] if langs else 1
    col_w = (WIDE - 2 * PAD - 60) / 2
    body = [
        _frame(WIDE, h, "DEATH NOTE  ·  PAGE 02", "BY SHARE OF CODE, ACROSS PUBLIC REPOS", f),
        _at(text_path(f.gothic, "Names written in this note", 50), PAD, 124, INK),
    ]
    for i, (lang, color, share) in enumerate(langs):
        col, row = divmod(i, 3)
        x = PAD + col * (col_w + 60)
        y = 220 + row * 84
        num = text_path(f.gothic, ["I", "II", "III", "IV", "V", "VI"][i], 34)
        nm = fit_path(f.hand, lang, 58, 300)
        pc = text_path(f.mono, f"{share * 100:.1f}%", 18, tracking=0.05)
        bar_x = x + 70 + 320
        bar_w = (col_w - 70 - 320 - pc.width - 24) * share / top
        delay = 0.8 + i * 0.15
        body.append(
            _at(num, x, y + 6, RED) + _written(nm, x + 70, y + 10, INK, 0.3 + i * 0.15, 1.0)
            + f'<line x1="{bar_x:.1f}" y1="{y - 4}" x2="{bar_x + bar_w:.1f}" y2="{y - 4}" stroke="{RED}" stroke-width="4" stroke-linecap="round" '
            f'pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="0">'
            f'<animate attributeName="stroke-dashoffset" values="1;1;0" keyTimes="0;{delay / (delay + 0.8):.3f};1" dur="{delay + 0.8:.2f}s" fill="freeze"/></line>'
            + _at(pc, bar_x + bar_w + 18, y + 2, MUTED)
            + f'<line x1="{x}" y1="{y + 26}" x2="{x + col_w}" y2="{y + 26}" stroke="{RULE}" stroke-width="1.5"/>'
        )
    body.append(_footer(WIDE, h, p, f, f"{len(p.languages)} languages in all"))
    label = ", ".join(f"{n} {s * 100:.0f}%" for n, _, s in langs)
    return _svg(WIDE, h, f"Top languages: {label}", "".join(body))


# ---- pages: recent repositories --------------------------------------------------------

def recent(p: Profile, repo: Repo, index: int, f: Fonts) -> str:
    h = 350
    name = fit_path(f.hand, repo.name, 70, HALF - 2 * PAD)
    desc = _wrap(f.serif, repo.description or "No description yet.", 25, HALF - 2 * PAD, 2)
    body = [
        _frame(HALF, h, f"RECENT PAGE {index:02d}", f"UPDATED {_ago(p, repo.pushed).upper()}", f),
        _written(name, PAD, 146, INK, 0.2, 1.2),
    ]
    body += [_at(text_path(f.serif, line, 25), PAD, 196 + i * 32, MUTED) for i, line in enumerate(desc)]
    y = h - 76
    lang = text_path(f.mono, repo.language or "—", 15, tracking=0.1)
    stars = text_path(f.mono, f"STARS {repo.stars}", 15, tracking=0.1)
    open_ = text_path(f.mono, "OPEN ↗", 15, tracking=0.2)
    body.append(
        f'<circle cx="{PAD + 7}" cy="{y - 5}" r="7" fill="{repo.color}"/>' + _at(lang, PAD + 24, y, INK)
        + _at(stars, PAD + 24 + lang.width + 30, y, MUTED) + _at(open_, HALF - PAD - open_.width, y, RED)
    )
    body.append(_footer(HALF, h, p, f))
    return _svg(HALF, h, f"{repo.name}: {repo.description} ({repo.language}, {repo.stars} stars)", "".join(body))


# ---- page: how to use it ---------------------------------------------------------------

RULES = (
    ("Ship it, then armor it", "Deploy first; observability and", "guardrails follow within the hour."),
    ("Automate the boring", "CI/CD and agents own the routine.", "The judgment stays with me."),
    ("Verify before trusting", "A model may propose the fix; only a", "passing test or a human approves it."),
)


def rules(p: Profile, f: Fonts) -> str:
    h = 400
    col = (WIDE - 2 * PAD) / 3
    epigraph = text_path(f.italic, "“The human whose name is written in this note shall die.”", 30)
    body = [
        _frame(WIDE, h, "DEATH NOTE  ·  HOW TO USE IT", "RULE I, AND MINE", f),
        _at(text_path(f.gothic, "How to use it", 52), PAD, 128, INK),
        _at(epigraph, WIDE - PAD - epigraph.width, 120, RED),
    ]
    for i, (title, *lines) in enumerate(RULES):
        x = PAD + i * col
        num = text_path(f.gothic, ["I", "II", "III"][i], 56)
        head = fit_path(f.serif_bold, title, 40, col - num.width - 50)
        group = _at(num, x, 226, RED) + _at(head, x + num.width + 20, 222, INK)
        group += "".join(_at(text_path(f.italic, line, 28), x, 272 + k * 36, MUTED) for k, line in enumerate(lines))
        if i:
            group += f'<line x1="{x - 24}" y1="176" x2="{x - 24}" y2="{h - 70}" stroke="{RULE}" stroke-width="1.5"/>'
        body.append(f"<g>{group}{_appear(0.5 + i * 0.25)}</g>")
    body.append(_footer(WIDE, h, p, f))
    return _svg(WIDE, h, "How to use it: ship it, then armor it; automate the boring; verify before trusting", "".join(body))


# ---- contact ---------------------------------------------------------------------------

def button(label: str, f: Fonts) -> str:
    w, h = 380, 92
    word = text_path(f.serif_bold, label.upper(), 28, tracking=0.18)
    arrow = text_path(f.mono, "↗", 28)
    body = (
        f'<rect x="1.5" y="1.5" width="{w - 3}" height="{h - 3}" rx="6" fill="{PAGE}" stroke="{EDGE}" stroke-width="2"/>'
        f'<rect x="1.5" y="1.5" width="8" height="{h - 3}" fill="{RED}"/>'
        + _at(word, 40, 57, INK) + _at(arrow, w - 34 - arrow.width, 57, RED)
    )
    return _svg(w, h, label, body)
