"""The profile's pages, each one showing live data from data.Profile.

Drawn in GitHub's own colours, once for its light theme and once for its dark one, so the
pages sit inside the profile as if GitHub had drawn them. One blue-to-purple gradient marks
what should catch the eye, and there are two voices of type: Inter for everything people read and JetBrains
Mono for labels. All text is converted to paths (fontpaths.py) so it renders the same
on every machine.
"""

import math
from dataclasses import dataclass
from datetime import timedelta
from html import escape

from data import USER, Profile
from fontpaths import FontRef, Shaped, fit_path, text_path

# GitHub's Primer palette: canvas, borders, text, accents and the contribution greens.
THEMES = {
    "light": dict(
        PAGE="#ffffff", TILE="#f6f8fa", EDGE="#d1d9e0", RULE="#e6eaef", INK="#1f2328", MUTED="#59636e", FAINT="#818b98",
        ACCENT="#0969da", ACCENT2="#8250df", GREEN="#1a7f37", GLOW=0.05,
        HEAT=("#eff2f5", "#aceebb", "#4ac26b", "#2da44e", "#116329"),
    ),
    "dark": dict(
        PAGE="#0d1117", TILE="#151b23", EDGE="#3d444d", RULE="#262c36", INK="#f0f6fc", MUTED="#9198a1", FAINT="#656c76",
        ACCENT="#4493f8", ACCENT2="#ab7df8", GREEN="#3fb950", GLOW=0.09,
        HEAT=("#151b23", "#033a16", "#196c2e", "#2ea043", "#56d364"),
    ),
}
AURORA = "url(#aurora)"


def set_theme(name: str) -> None:
    """Point the colour names below at one of GitHub's themes."""
    globals().update(THEMES[name])


set_theme("light")

HALF, WIDE = 860, 1740
PAD = 44


@dataclass(frozen=True)
class Fonts:
    display: FontRef    # names and big numbers
    bold: FontRef       # headings
    sans: FontRef       # prose
    mono: FontRef       # labels


# ---- primitives ------------------------------------------------------------------------

def _svg(w: float, h: float, label: str, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}" '
        f'role="img" aria-label="{escape(label)}"><defs>'
        f'<linearGradient id="aurora" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{ACCENT}"/><stop offset="1" stop-color="{ACCENT2}"/></linearGradient>'
        f'<radialGradient id="glow"><stop offset="0" stop-color="{ACCENT}" stop-opacity="{GLOW}"/>'
        f'<stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/></radialGradient>'
        f'<clipPath id="card"><rect x="1" y="1" width="{w - 2:.0f}" height="{h - 2:.0f}" rx="18"/></clipPath>'
        f'</defs>{body}</svg>'
    )


def _at(shape: Shaped, x: float, baseline: float, fill: str, extra: str = "", children: str = "") -> str:
    head = f'<path transform="translate({x:.1f} {baseline - shape.ascent:.1f})" d="{shape.d}" fill="{fill}"{extra}'
    return f"{head}>{children}</path>" if children else f"{head}/>"


def _appear(delay: float, dy: float = 6) -> str:
    """Hidden until `delay`, then eased in; visible at rest for renderers without SMIL."""
    dur = delay + 0.6
    kt = f"0;{delay / dur:.3f};1"
    return (
        f'<animate attributeName="opacity" values="0;0;1" keyTimes="{kt}" dur="{dur:.2f}s" fill="freeze"/>'
        f'<animateTransform attributeName="transform" type="translate" values="0 {dy};0 {dy};0 0" keyTimes="{kt}" dur="{dur:.2f}s" fill="freeze"/>'
    )


def _card(w: float, h: float, glow: tuple[float, float] | None = None) -> str:
    """A dark rounded card, a gradient hairline along its top, and a soft glow in one corner."""
    gx, gy = glow if glow else (w - 80, 0)
    return (
        f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="18" fill="{PAGE}" stroke="{EDGE}" stroke-width="2"/>'
        f'<g clip-path="url(#card)"><ellipse cx="{gx}" cy="{gy}" rx="{min(w, 900) * 0.55:.0f}" ry="260" fill="url(#glow)"/>'
        f'<rect x="0" y="0" width="{w}" height="3" fill="{AURORA}" opacity="0.9"/></g>'
    )


def _frame(w: float, h: float, left: str, right: str, f: Fonts) -> str:
    """The card plus a label row."""
    l = text_path(f.mono, left, 13, tracking=0.22)
    r = text_path(f.mono, right, 13, tracking=0.22)
    return (
        _card(w, h)
        + f'<circle cx="{PAD + 4}" cy="34" r="4.5" fill="{ACCENT}"/>'
        + _at(l, PAD + 18, 39, MUTED) + _at(r, w - PAD - r.width, 39, MUTED)
        + f'<line x1="{PAD}" y1="60" x2="{w - PAD}" y2="60" stroke="{RULE}" stroke-width="1.5"/>'
    )


def _footer(w: float, h: float, p: Profile, f: Fonts, right: str = "") -> str:
    left = f"updated {p.today:%d %b %Y}".replace(" 0", " ") if p.live else "preview data"
    a = text_path(f.mono, left, 12, tracking=0.1)
    out = f'<line x1="{PAD}" y1="{h - 46}" x2="{w - PAD}" y2="{h - 46}" stroke="{RULE}" stroke-width="1.5"/>' + _at(a, PAD, h - 20, FAINT if p.live else ACCENT)
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


def _pills(f: Fonts, items: list[str], x: float, y: float, max_width: float, size: float = 14) -> str:
    """A row of rounded tags, shrunk together until the row fits."""
    while True:
        shapes = [text_path(f.mono, item, size) for item in items]
        gap, pad = 10, size * 0.9
        total = sum(s.width + 2 * pad for s in shapes) + gap * (len(shapes) - 1)
        if total <= max_width or size <= 10:
            break
        size -= 0.5
    h = size * 2.1
    out = []
    for s in shapes:
        w = s.width + 2 * pad
        out.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{h / 2:.1f}" fill="{TILE}" stroke="{EDGE}" stroke-width="1.5"/>'
            + _at(s, x + pad, y + h / 2 + size * 0.36, INK)
        )
        x += w + gap
    return "".join(out)


# ---- section headers -------------------------------------------------------------------

def title_card(number: int, title: str, line: str, f: Fonts) -> str:
    """A section opener: its number, its name, and one line about it."""
    h = 120
    num = text_path(f.mono, f"{number:02d}", 22, tracking=0.1)
    name = text_path(f.display, title, 46, tracking=-0.01)
    note = text_path(f.sans, line, 22)
    x = 40
    body = (
        _card(WIDE, h, (180, h))
        + f'<g>{_at(num, x, 77, AURORA)}{_appear(0.1, 0)}</g>'
        + f'<line x1="{x + num.width + 22}" y1="44" x2="{x + num.width + 22}" y2="80" stroke="{EDGE}" stroke-width="2"/>'
        + f'<g>{_at(name, x + num.width + 44, 78, INK)}{_appear(0.25)}</g>'
        + f'<g>{_at(note, WIDE - x - note.width, 74, MUTED)}{_appear(0.4, 0)}</g>'
    )
    return _svg(WIDE, h, f"{number:02d}: {title}. {line}", body)


# ---- page: identity -------------------------------------------------------------------

def _mono(f: Fonts, text: str, size: float = 19) -> Shaped:
    return text_path(f.mono, text, size)


def whoami(p: Profile, f: Fonts) -> str:
    """$ whoami: role, stack and proof as key/value groups, then status and a prompt."""
    h = 1000
    groups = (
        (
            ("role", "DevOps · Full-Stack · Applied AI"),
            ("focus", "AIOps · SRE · RAG systems"),
            ("based", "Bengaluru, India · UTC+5:30"),
            ("edu", "B.E. CSE · APS College of Engg."),
        ),
        (
            ("langs", "Python · React · Java"),
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
        _at(_mono(f, "$"), PAD, 110, ACCENT) + _at(_mono(f, "whoami"), PAD + 24, 110, INK),
        f'<g>{_at(text_path(f.display, "Likith Lochan", 66, tracking=-0.02), PAD, 188, AURORA)}{_appear(0.2)}</g>',
    ]
    y, delay = 252, 0.6
    for group in groups:
        body.append(f'<line x1="{PAD}" y1="{y - 24}" x2="{HALF - PAD}" y2="{y - 24}" stroke="{RULE}" stroke-width="1.5"/>')
        y += 14
        for key, value in group:
            row = _at(_mono(f, key), PAD, y, MUTED) + _at(_mono(f, value), PAD + 150, y, AURORA if key == "activity" else INK)
            body.append(f"<g>{row}{_appear(delay, 0)}</g>")
            y += 38
            delay += 0.06
        y += 22
    status = _mono(f, "open to DevOps/Cloud · SDE · AI/ML")
    body.append(
        f'<g><circle cx="{PAD + 6}" cy="{y - 6}" r="6" fill="{GREEN}"><animate attributeName="opacity" values="1;0.35;1" dur="2.2s" repeatCount="indefinite"/></circle>'
        + _at(status, PAD + 24, y, GREEN) + f"{_appear(delay, 0)}</g>"
    )
    y += 46
    body.append(
        f"<g>{_at(_mono(f, '$'), PAD, y, ACCENT)}"
        f'<rect x="{PAD + 24}" y="{y - 18}" width="11" height="22" fill="{INK}">'
        '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" repeatCount="indefinite"/></rect>'
        f"{_appear(delay + 0.1, 0)}</g>"
    )
    body.append(_footer(HALF, h, p, f, f"{p.contributions:,} contributions in the last year"))
    return _svg(HALF, h, f"whoami: Likith Lochan, DevOps, Full-Stack and Applied AI. {p.contributions} contributions in the last year.", "".join(body))


# ---- page: stats -----------------------------------------------------------------------

def stats(p: Profile, f: Fonts) -> str:
    """The year in numbers: contributions, streaks, a heatmap and the language mix."""
    h = 1000
    inner = HALF - 2 * PAD
    body = [_frame(HALF, h, "~/STATS", "LAST 12 MONTHS", f)]

    big = text_path(f.display, f"{p.contributions:,}", 128, tracking=-0.03)
    body.append(_at(text_path(f.mono, "CONTRIBUTIONS", 13, tracking=0.25), PAD, 112, MUTED))
    body.append(f'<g>{_at(big, PAD - 4, 252, AURORA)}{_appear(0.2)}</g>')
    body.append(_at(text_path(f.sans, f"in the last year  ·  on GitHub since {p.since}", 22), PAD, 296, MUTED))

    tiles = (("CURRENT STREAK", f"{p.current_streak}d"), ("LONGEST STREAK", f"{p.longest_streak}d"), ("PUBLIC REPOS", f"{p.repo_count}"))
    gap = 16
    tw = (inner - 2 * gap) / 3
    for i, (label, value) in enumerate(tiles):
        x = PAD + i * (tw + gap)
        tile = (
            f'<rect x="{x:.1f}" y="334" width="{tw:.1f}" height="128" rx="14" fill="{TILE}" stroke="{EDGE}" stroke-width="1.5"/>'
            + _at(text_path(f.display, value, 54, tracking=-0.02), x + 22, 410, INK)
            + _at(text_path(f.mono, label, 14, tracking=0.15), x + 22, 444, MUTED)
        )
        body.append(f"<g>{tile}{_appear(0.4 + i * 0.1)}</g>")

    # Heatmap: one column per week, Sunday at the top, coloured by quartile of the active days.
    body.append(_at(text_path(f.mono, "EVERY DAY OF THE YEAR", 13, tracking=0.25), PAD, 524, MUTED))
    days = p.days[-364:] if len(p.days) >= 364 else p.days
    offset = (days[0][0].weekday() + 1) % 7
    active = sorted(n for _, n in days if n)
    cuts = [active[int(len(active) * q)] for q in (0.25, 0.5, 0.75)] if active else [1, 2, 3]
    weeks = (len(days) + offset + 6) // 7
    step = inner / weeks
    cell = step * 0.78
    top = 548
    cols: dict[int, list[str]] = {}
    for i, (_, n) in enumerate(days):
        col, row = divmod(i + offset, 7)
        level = 0 if not n else 1 + sum(n > c for c in cuts)
        cols.setdefault(col, []).append(
            f'<rect x="{PAD + col * step:.1f}" y="{top + row * step:.1f}" width="{cell:.1f}" height="{cell:.1f}" rx="2.5" fill="{HEAT[level]}"/>'
        )
    for col, cells in cols.items():
        body.append(f"<g>{''.join(cells)}{_appear(0.6 + col * 0.015, 0)}</g>")
    legend_y = top + 7 * step + 22
    less = text_path(f.mono, "less", 12)
    more = text_path(f.mono, "more", 12)
    lx = HALF - PAD - more.width
    body.append(_at(more, lx, legend_y + 4, FAINT))
    for k in range(4, -1, -1):
        lx -= 18
        body.append(f'<rect x="{lx:.1f}" y="{legend_y - 8:.1f}" width="12" height="12" rx="2.5" fill="{HEAT[k]}"/>')
    body.append(_at(less, lx - 8 - less.width, legend_y + 4, FAINT))

    # Languages, by bytes across all public repos.
    langs = p.languages[:6]
    total = sum(s for *_, s in langs) or 1
    ly = 760
    body.append(_at(text_path(f.mono, "LANGUAGES", 13, tracking=0.25), PAD, ly, MUTED))
    body.append(f'<clipPath id="bar"><rect x="{PAD}" y="{ly + 22}" width="{inner}" height="14" rx="7"/></clipPath><g clip-path="url(#bar)">')
    x = PAD
    for _, color, share in langs:
        w = inner * share / total
        body.append(f'<rect x="{x:.1f}" y="{ly + 22}" width="{w + 0.5:.1f}" height="14" fill="{color}"/>')
        x += w
    body.append("</g>")
    colw = inner / 3
    for i, (name, color, share) in enumerate(langs):
        cx = PAD + (i % 3) * colw
        cy = ly + 76 + (i // 3) * 36
        body.append(
            f'<circle cx="{cx + 6}" cy="{cy - 6}" r="6" fill="{color}"/>'
            + _at(text_path(f.sans, name, 20), cx + 22, cy, INK)
            + _at(text_path(f.mono, f"{share / total:.0%}", 15), cx + 22 + text_path(f.sans, name, 20).width + 10, cy, MUTED)
        )
    body.append(_footer(HALF, h, p, f, f"{p.active30} active days in the last 30"))
    return _svg(HALF, h, f"Stats: {p.contributions} contributions in the last year, current streak {p.current_streak} days, longest {p.longest_streak} days, {p.repo_count} public repos.", "".join(body))


# ---- page: how I work ------------------------------------------------------------------

RULES = (
    ("Ship it, then armor it", "Deploy first; observability and", "guardrails follow within the hour."),
    ("Automate the boring", "CI/CD and agents own the routine.", "The judgment stays with me."),
    ("Verify before trusting", "A model may propose the fix; only a", "passing test or a human approves it."),
)


def rules(p: Profile, f: Fonts) -> str:
    h = 380
    col = (WIDE - 2 * PAD) / 3
    body = [
        _frame(WIDE, h, "PRINCIPLES", "HOW I WORK", f),
        _at(text_path(f.display, "How I work", 50, tracking=-0.02), PAD, 132, INK),
    ]
    for i, (title, *lines) in enumerate(RULES):
        x = PAD + i * col
        num = text_path(f.display, f"0{i + 1}", 50, tracking=-0.02)
        head = fit_path(f.bold, title, 32, col - num.width - 50)
        group = _at(num, x, 226, AURORA) + _at(head, x + num.width + 18, 222, INK)
        group += "".join(_at(text_path(f.sans, line, 23), x, 268 + k * 34, MUTED) for k, line in enumerate(lines))
        if i:
            group += f'<line x1="{x - 24}" y1="176" x2="{x - 24}" y2="{h - 70}" stroke="{RULE}" stroke-width="1.5"/>'
        body.append(f"<g>{group}{_appear(0.3 + i * 0.2)}</g>")
    body.append(_footer(WIDE, h, p, f))
    return _svg(WIDE, h, "How I work: ship it, then armor it; automate the boring; verify before trusting", "".join(body))


# ---- contact ---------------------------------------------------------------------------

def button(label: str, f: Fonts) -> str:
    w, h = 380, 92
    word = text_path(f.bold, label, 28)
    arrow = text_path(f.mono, "↗", 28)
    body = (
        f'<rect x="2" y="2" width="{w - 4}" height="{h - 4}" rx="{(h - 4) / 2}" fill="{PAGE}" stroke="{AURORA}" stroke-width="2.5"/>'
        f'<g clip-path="url(#card)"><ellipse cx="{w / 2}" cy="{h}" rx="{w * 0.5}" ry="60" fill="url(#glow)"/></g>'
        + _at(word, (w - word.width - arrow.width - 14) / 2, 57, INK)
        + _at(arrow, (w + word.width - arrow.width + 14) / 2, 57, AURORA)
    )
    return _svg(w, h, label, body)


# ---- pages: projects -------------------------------------------------------------------

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
    Project("Orbit IDE", "Orbit-IDE", "AI code that only looks right",
            "A browser IDE with a Linux container per project; Claude's edits run in a sandbox and self-repair until tests pass, with live collab over Yjs.",
            "React · Monaco · Express · Docker · Claude API"),
    Project("Project Management", "Project-Management", "Tasks lost between workspaces",
            "Workspaces, projects and tasks with roles, comments, calendar and analytics; Inngest emails assignees and sends due-date reminders.",
            "React · Express · Prisma · Neon · Clerk · Inngest"),
)


def entry(p: Profile, index: int, proj: Project, f: Fonts) -> str:
    """One project: its name, the problem it takes on, when it last moved (live from
    GitHub), what it does, and what it is built with."""
    h = 440
    repo = next((r for r in p.repos if r.name.lower() == proj.repo.lower()), None)
    when = f"{repo.pushed:%d %b %Y}".lstrip("0") if repo else ""
    inner = HALF - 2 * PAD
    name = fit_path(f.display, proj.name, 60, inner, tracking=-0.02)
    body = [
        _frame(HALF, h, f"PROJECT {index:02d}", "OPEN ↗", f),
        f'<g>{_at(name, PAD, 140, AURORA)}{_appear(0.15)}</g>',
        _at(fit_path(f.bold, proj.cause, 26, inner), PAD, 184, INK),
    ]
    mx = PAD
    if repo and repo.language:
        body.append(f'<circle cx="{mx + 6}" cy="{220}" r="6" fill="{repo.color}"/>')
        lang = text_path(f.mono, repo.language, 15)
        body.append(_at(lang, mx + 20, 226, INK))
        mx += 20 + lang.width + 16
    meta = f"updated {when}" if when else f"github.com/{USER}/{proj.repo}"
    body.append(_at(text_path(f.mono, meta, 15), mx, 226, MUTED))
    body.append(f'<line x1="{PAD}" y1="252" x2="{HALF - PAD}" y2="252" stroke="{RULE}" stroke-width="1.5"/>')
    for k, line in enumerate(_wrap(f.sans, proj.details, 21, inner, 3)):
        body.append(_at(text_path(f.sans, line, 21), PAD, 292 + k * 31, MUTED))
    body.append(_pills(f, proj.stack.split(" · "), PAD, h - 70, inner))
    return _svg(HALF, h, f"{proj.name}: {proj.cause}. {proj.details}", "".join(body))
