"""The banner: a name, a role and a line, lit by a slow aurora.

Four soft pastel blobs of lavender, pink, peach and sky drift behind a faint dot grid, and the name
carries the same gradient, sliding through it. Nothing else competes with the type.
"""

from fontpaths import text_path
from pages import GREEN, INK, MUTED, ORANGE, PINK, VIOLET, Fonts, _appear, _at

W, H = 1280, 460


def _defs() -> str:
    blobs = "".join(
        f'<radialGradient id="b{i}"><stop offset="0" stop-color="{c}" stop-opacity="{o}"/><stop offset="1" stop-color="{c}" stop-opacity="0"/></radialGradient>'
        for i, (c, o) in enumerate((("#c4b5fd", 0.9), ("#f9a8d4", 0.85), ("#fdba74", 0.75), ("#93c5fd", 0.6)))
    )
    return f'''
  <clipPath id="frame"><rect width="{W}" height="{H}" rx="20"/></clipPath>
  {blobs}
  <linearGradient id="name" x1="0" y1="0" x2="1" y2="0" spreadMethod="reflect">
    <stop offset="0" stop-color="{VIOLET}"/><stop offset="0.5" stop-color="{PINK}"/><stop offset="1" stop-color="{ORANGE}"/>
    <animateTransform attributeName="gradientTransform" type="translate" values="0 0;-1 0;0 0" dur="10s" repeatCount="indefinite"/>
  </linearGradient>
  <linearGradient id="rule" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{VIOLET}"/><stop offset="0.55" stop-color="{PINK}"/><stop offset="1" stop-color="{ORANGE}"/>
  </linearGradient>
  <pattern id="dots" width="28" height="28" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.2" fill="#1c1633" fill-opacity="0.07"/></pattern>
  <linearGradient id="fade" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0.2"/><stop offset="1" stop-color="#fff" stop-opacity="1"/></linearGradient>
  <mask id="dotMask"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask>
  <filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="40"/></filter>'''


def _aurora() -> str:
    """Three blobs, each drifting on its own slow loop."""
    blobs = (
        (0, 980, 120, 340, 220, "0 0;-90 50;30 -20;0 0", 19),
        (1, 1150, 360, 300, 200, "0 0;-120 -40;-40 30;0 0", 23),
        (2, 760, 420, 280, 160, "0 0;80 -60;120 10;0 0", 29),
        (3, 560, 40, 260, 140, "0 0;60 30;-40 20;0 0", 31),
    )
    return "".join(
        f'<g filter="url(#soft)"><ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="url(#b{i})">'
        f'<animateTransform attributeName="transform" type="translate" values="{path}" dur="{dur}s" repeatCount="indefinite"/></ellipse></g>'
        for i, cx, cy, rx, ry, path, dur in blobs
    )


def _type(f: Fonts) -> str:
    x = 72
    label = text_path(f.mono, "BENGALURU, INDIA  ·  B.E. CSE, APS COLLEGE OF ENGINEERING", 14, tracking=0.25)
    name = text_path(f.display, "Likith Lochan", 124, tracking=-0.035)
    role = text_path(f.bold, "DevOps  ·  Full-Stack  ·  Applied AI", 36, tracking=-0.01)
    line = text_path(f.sans, "I build systems that ship, scale and fix themselves.", 25)
    status = text_path(f.mono, "OPEN TO DevOps/Cloud · SDE · AI/ML", 14, tracking=0.12)
    pill_w = status.width + 64
    return (
        f'<g>{_at(label, x, 104, MUTED)}{_appear(0.1, 0)}</g>'
        f'<g>{_at(name, x - 4, 236, "url(#name)")}{_appear(0.25, 14)}</g>'
        f'<g><rect x="{x}" y="266" width="120" height="4" rx="2" fill="url(#rule)"/>{_appear(0.5, 0)}</g>'
        f'<g>{_at(role, x, 326, INK)}{_appear(0.6)}</g>'
        f'<g>{_at(line, x, 368, MUTED)}{_appear(0.75)}</g>'
        f'<g><rect x="{W - 72 - pill_w:.1f}" y="66" width="{pill_w:.1f}" height="40" rx="20" fill="#ffffff" fill-opacity="0.85" stroke="{GREEN}" stroke-opacity="0.5" stroke-width="1.5"/>'
        f'<circle cx="{W - 72 - pill_w + 24:.1f}" cy="86" r="5" fill="{GREEN}"><animate attributeName="opacity" values="1;0.35;1" dur="2.2s" repeatCount="indefinite"/></circle>'
        + _at(status, W - 72 - pill_w + 40, 91, INK) + f"{_appear(0.9, 0)}</g>"
    )


def render(f: Fonts) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Likith Lochan. DevOps, Full-Stack, Applied AI. I build systems that ship, scale and fix themselves.">
<defs>{_defs()}</defs>
<g clip-path="url(#frame)">
  <rect width="{W}" height="{H}" fill="#fcfbff"/>
  {_aurora()}
  <rect width="{W}" height="{H}" fill="url(#dots)" mask="url(#dotMask)"/>
  {_type(f)}
</g>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="19" fill="none" stroke="#e9e4f7" stroke-width="2"/>
</svg>'''
