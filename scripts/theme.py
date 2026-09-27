"""One palette per GitHub theme. The notebook: black cover, parchment pages, and red ink."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    name: str
    page: str      # GitHub's own background, so cards sit flush
    surface: str   # card fill: the notebook's cover (dark) or its page (light)
    border: str
    ink: str       # primary text
    muted: str     # labels, secondary text
    faint: str     # rules, ruled lines, the sparsest ASCII tone
    accent: str    # blood red: prompts, metrics, highlights
    bone: str      # parchment, the second voice in diagrams
    live: str      # "still breathing" dot
    apple: str     # Ryuk's apple


DARK = Theme(
    name="dark",
    page="#0d1117",
    surface="#0a0909",
    border="#231d1d",
    ink="#ece6da",
    muted="#8a817a",
    faint="#2c2524",
    accent="#e0303a",
    bone="#c9b99a",
    live="#e0303a",
    apple="#ff3b3f",
)

LIGHT = Theme(
    name="light",
    page="#ffffff",
    surface="#fbf8f1",
    border="#e7dfd0",
    ink="#161312",
    muted="#6e645b",
    faint="#e2d9c8",
    accent="#b0141d",
    bone="#8a7550",
    live="#b0141d",
    apple="#c8161f",
)

THEMES = (DARK, LIGHT)

MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"


def mix(a: str, b: str, t: float) -> str:
    """Blend two hex colours; t=0 gives a, t=1 gives b."""
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb))
