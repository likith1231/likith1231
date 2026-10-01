"""The profile's pages, each one showing live data from data.Profile.

Black pages, blood-red accents, and four voices of type: handwriting for anything written
into the note, blackletter for titles, a serif for prose, and mono for labels. All text is
converted to paths (fontpaths.py) so it renders the same on every machine.
"""

import math
from dataclasses import dataclass
from datetime import date
from html import escape

from data import Profile
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


# ---- page: identity -------------------------------------------------------------------

def _mono(f: Fonts, text: str, size: float = 19) -> Shaped:
    return text_path(f.mono, text, size)


def whoami(p: Profile, f: Fonts) -> str:
    """$ whoami: role, stack and proof as key/value groups, then status and a prompt."""
    h = 1000
    groups = (
        (
            ("role", "DevOps · Backend/Full-Stack · Applied AI"),
            ("focus", "AIOps · SRE · RAG systems"),
            ("based", "Bengaluru, India · UTC+5:30"),
            ("edu", "B.E. CSE · APS College of Engg."),
        ),
        (
            ("langs", "Python · TypeScript · JavaScript · Java"),
            ("backend", "FastAPI · Node/Express · Socket.IO"),
            ("frontend", "React · Next.js · Tailwind · Three.js"),
            ("ai", "Claude · Gemini · CrewAI · pgvector"),
            ("infra", "Kubernetes · Terraform · EKS · ArgoCD"),
            ("observe", "Prometheus · Grafana · OTel · Sentry"),
            ("ship", "Docker · GitHub Actions · Vault · k6"),
        ),
        (
            ("activity", f"{p.contributions:,} contributions · {p.current_streak}-day streak"),
            ("proof", "GhostOps: 2 incidents fixed end to end"),
        ),
    )
    body = [
        _frame(HALF, h, "~/WHOAMI", "ZSH", f),
        _at(_mono(f, "$"), PAD, 108, RED) + _at(_mono(f, "whoami"), PAD + 24, 108, INK),
        _written(text_path(f.gothic, "Likith Lochan", 64), PAD, 186, INK, 0.2, 1.8),
    ]
    y, delay = 250, 1.0
    for g, group in enumerate(groups):
        body.append(f'<line x1="{PAD}" y1="{y - 24}" x2="{HALF - PAD}" y2="{y - 24}" stroke="{RULE}" stroke-width="1.5"/>')
        y += 14
        for key, value in group:
            row = _at(_mono(f, key), PAD, y, MUTED) + _at(_mono(f, value), PAD + 150, y, RED if key == "activity" else INK)
            body.append(f"<g>{row}{_appear(delay, 0)}</g>")
            y += 38
            delay += 0.07
        y += 22
    status = _mono(f, "open to DevOps/Cloud · Backend · SDE · AI/ML")
    body.append(
        f'<g><circle cx="{PAD + 6}" cy="{y - 6}" r="6" fill="{RED}"><animate attributeName="opacity" values="1;0.3;1" dur="2.2s" repeatCount="indefinite"/></circle>'
        + _at(status, PAD + 24, y, RED) + f"{_appear(delay, 0)}</g>"
    )
    y += 46
    body.append(
        f"<g>{_at(_mono(f, '$'), PAD, y, RED)}"
        f'<rect x="{PAD + 24}" y="{y - 18}" width="11" height="22" fill="{INK}">'
        '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" repeatCount="indefinite"/></rect>'
        f"{_appear(delay + 0.1, 0)}</g>"
    )
    body.append(_footer(HALF, h, p, f, f"{p.contributions:,} contributions in the last year"))
    return _svg(HALF, h, f"whoami: Likith Lochan, DevOps, Backend/Full-Stack and Applied AI. {p.contributions} contributions in the last year.", "".join(body))


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


# ---- pages: projects, written into the note --------------------------------------------

@dataclass(frozen=True)
class Project:
    name: str
    repo: str
    cause: str
    details: str
    stack: str


PROJECTS = (
    Project("GhostOps", "ghostops", "Production incidents, patched on their own",
            "Alertmanager fires; three CrewAI agents find the root cause, write a minimal patch, and prove it in a Docker sandbox under OPA before a PR is opened.",
            "CrewAI · Claude API · FastAPI · Kubernetes · OPA"),
    Project("AetherMed", "Aethermed", "Traffic spikes, absorbed by autoscaling",
            "Clinic booking on Next.js, run like production: HPA scales 2 to 8 pods under k6 load, ArgoCD self-heals, Sentry and OTel trace it all.",
            "Terraform · AWS EKS · ArgoCD · k6 · Sentry"),
    Project("Sahayak", "sahayak", "The middlemen between farm and market",
            "Farmers list produce by chatting with a Gemini agent that calls real tools; live mandi prices from Agmarknet, pgvector search, Razorpay checkout.",
            "Next.js · FastAPI · Gemini · pgvector · Razorpay"),
    Project("GreenCart", "greencart", "Empty carts",
            "A MERN grocery store with a separate seller dashboard, Cloudinary product images, JWT cookie auth, and cash-on-delivery or Stripe checkout.",
            "React · Express · MongoDB · Stripe · Tailwind"),
)


def entry(p: Profile, index: int, proj: Project, f: Fonts) -> str:
    """One project as a Death Note entry: the name written in and struck through, then the
    cause of death, the time (its last update, live from GitHub) and the details."""
    h = 440
    repo = next((r for r in p.repos if r.name.lower() == proj.repo.lower()), None)
    when = f"{repo.pushed:%d %b %Y}".lstrip("0") if repo else "—"
    lang = repo.language if repo and repo.language else ""
    name = fit_path(f.gothic, proj.name, 72, HALF - 2 * PAD)
    struck = 0.2 + 1.4 + 0.2
    body = [
        _frame(HALF, h, f"DEATH NOTE  ·  ENTRY {index:02d}", "OPEN ↗", f),
        _written(name, PAD, 152, INK, 0.2, 1.4),
        f'<line x1="{PAD - 6}" y1="{152 - name.ascent * 0.28:.0f}" x2="{PAD + name.width + 8:.0f}" y2="{152 - name.ascent * 0.33:.0f}" '
        f'stroke="{RED}" stroke-width="3" stroke-linecap="round" opacity="0.9" pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="0">'
        f'<animate attributeName="stroke-dashoffset" values="1;1;0" keyTimes="0;{struck / (struck + 0.5):.3f};1" dur="{struck + 0.5:.2f}s" fill="freeze"/></line>',
    ]
    rows = [("CAUSE", text_path(f.serif_bold, proj.cause, 25)),
            ("TIME", text_path(f.serif, f"{when}" + (f"  ·  {lang}" if lang else ""), 25))]
    y = 212
    for label, value in rows:
        body.append(_at(text_path(f.mono, label, 13, tracking=0.25), PAD, y - 4, MUTED) + _at(value, PAD + 130, y, INK if label == "CAUSE" else MUTED))
        body.append(f'<line x1="{PAD}" y1="{y + 14}" x2="{HALF - PAD}" y2="{y + 14}" stroke="{RULE}" stroke-width="1.5"/>')
        y += 46
    body.append(_at(text_path(f.mono, "DETAILS", 13, tracking=0.25), PAD, y - 4, MUTED))
    for k, line in enumerate(_wrap(f.serif, proj.details, 23, HALF - 2 * PAD - 130, 3)):
        body.append(_at(text_path(f.serif, line, 23), PAD + 130, y + k * 30, MUTED))
    stack = fit_path(f.mono, proj.stack, 14, HALF - 2 * PAD)
    body.append(f'<line x1="{PAD}" y1="{h - 46}" x2="{HALF - PAD}" y2="{h - 46}" stroke="{RULE}" stroke-width="1.5"/>' + _at(stack, PAD, h - 20, RED))
    return _svg(HALF, h, f"Death Note entry: {proj.name}. Cause: {proj.cause}. {proj.details}", "".join(body))
