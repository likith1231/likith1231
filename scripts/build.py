"""Build every profile asset and the README from content.py.

    python scripts/build.py            # from the repo root

Fonts are fetched from google/fonts on first run (all OFL). With GITHUB_TOKEN set,
the whoami card's footer shows the live contribution count; without it, just the date.
"""

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import ascii_card
import banner
import cards
import note
from content import CLIPS, LINKS, USER
from fontpaths import FontRef
from theme import THEMES

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
FONT_DIR = Path(__file__).resolve().parent / "fonts"

FONT_FILES = {
    "UnifrakturMaguntia-Book.ttf": "ofl/unifrakturmaguntia/UnifrakturMaguntia-Book.ttf",
    "GrenzeGotisch[wght].ttf": "ofl/grenzegotisch/GrenzeGotisch%5Bwght%5D.ttf",
    "CormorantGaramond[wght].ttf": "ofl/cormorantgaramond/CormorantGaramond%5Bwght%5D.ttf",
    "CormorantGaramond-Italic[wght].ttf": "ofl/cormorantgaramond/CormorantGaramond-Italic%5Bwght%5D.ttf",
    "FamiljenGrotesk[wght].ttf": "ofl/familjengrotesk/FamiljenGrotesk%5Bwght%5D.ttf",
    "JetBrainsMono[wght].ttf": "ofl/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf",
    "YujiBoku-Regular.ttf": "ofl/yujiboku/YujiBoku-Regular.ttf",
}
# Section headers, drawn as manga chapter titles: (kanji, English title).
SECTIONS = {
    "whoami": ("正体", "Identity"),
    "rules": ("掟", "The Rules"),
    "activity": ("記録", "The Record"),
    "contact": ("接触", "Contact"),
}
BUTTONS = (("linkedin", "LinkedIn"), ("email", "Email"), ("github", "All repos"))


def ensure_fonts() -> None:
    FONT_DIR.mkdir(exist_ok=True)
    for name, remote in FONT_FILES.items():
        target = FONT_DIR / name
        if not target.exists():
            print(f"fetching {name}")
            urllib.request.urlretrieve(f"https://raw.githubusercontent.com/google/fonts/main/{remote}", target)


def load_fonts() -> banner.Fonts:
    def ref(name: str, *axes: tuple[str, float]) -> FontRef:
        return FontRef(str(FONT_DIR / name), tuple(axes))

    return banner.Fonts(
        gothic=ref("GrenzeGotisch[wght].ttf", ("wght", 640)),
        old_english=ref("UnifrakturMaguntia-Book.ttf"),
        serif=ref("CormorantGaramond[wght].ttf", ("wght", 500)),
        serif_bold=ref("CormorantGaramond[wght].ttf", ("wght", 700)),
        italic=ref("CormorantGaramond-Italic[wght].ttf", ("wght", 500)),
        sans=ref("FamiljenGrotesk[wght].ttf", ("wght", 400)),
        sans_medium=ref("FamiljenGrotesk[wght].ttf", ("wght", 560)),
        mono=ref("JetBrainsMono[wght].ttf", ("wght", 400)),
        brush=ref("YujiBoku-Regular.ttf"),
    )


def contributions_last_year() -> int | None:
    """Total from the contribution calendar, or None without a token or when the API fails."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return None
    query = (
        f'{{ user(login: "{USER}") {{ contributionsCollection '
        f'{{ contributionCalendar {{ totalContributions }} }} }} }}'
    )
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.load(response)
        return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    except (OSError, KeyError, TypeError, ValueError) as error:
        print(f"stats unavailable, keeping the card static: {error}", file=sys.stderr)
        return None


def write(name: str, svg: str) -> None:
    (ASSETS / name).write_text(svg, encoding="utf-8")


def themed(name: str, alt: str, width: str = "100%") -> str:
    """A <picture> that follows the viewer's GitHub theme."""
    return (
        f'<picture><source media="(prefers-color-scheme: dark)" srcset="./assets/{name}-dark.svg">'
        f'<img src="./assets/{name}-light.svg" width="{width}" alt="{alt}"></picture>'
    )


def scenes(*names: str, width: str = "32%") -> str:
    """A row of anime clips, side by side. They share one line: GitHub breaks on newlines."""
    return " ".join(f'<img src="{CLIPS[n][0]}" width="{width}" alt="{CLIPS[n][1]}">' for n in names)


def readme() -> str:
    buttons = " ".join(
        f'<a href="{LINKS[key]}">{themed(f"link-{key}", label, "200")}</a>' for key, label in BUTTONS
    )
    # The contribution snake, unchanged: rendered by .github/workflows/snake.yml.
    raw = f"https://raw.githubusercontent.com/{USER}/{USER}/output"
    snake = (
        f'<picture>\n  <source media="(prefers-color-scheme: dark)" srcset="{raw}/github-snake-dark.svg" />\n'
        f'  <source media="(prefers-color-scheme: light)" srcset="{raw}/github-snake.svg" />\n'
        f'  <img alt="Snake animation" src="{raw}/github-snake-dark.svg" width="860" />\n</picture>'
    )
    return f"""<!-- Generated by scripts/build.py from scripts/content.py. Edit those, not this file. -->
<div align="center">

<img src="./assets/banner.svg" width="100%" alt="Likith Lochan. DevOps, Backend/Full-Stack, Applied AI. Drawn as a manga page: Ryuk against a red moon, L's letter on a monitor, and the Death Note falling.">

{scenes("ryuk-moon", "light-smile", "ryuk-eyes")}

<br><br>

{themed("header-whoami", "File 01: 正体, Identity")}

{scenes("l-stare", "ryuk-school", width="49%")}

{themed("note", "ASCII art: the Death Note, bleeding, gripped by a shinigami's claw", "49%")} {themed("whoami", "Role, stack, and what I have shipped", "49%")}

<br><br>

{themed("header-rules", "File 02: 掟, The Rules")}

{scenes("light-writing", "pen", width="49%")}

{themed("rules", "How to use it: ship it, then armor it; automate the boring; verify before trusting")}

<br><br>

{themed("header-activity", "File 03: 記録, The Record")}

{scenes("light-laugh", "ryuk-red", width="49%")}

{snake}

<br><br>

{themed("header-contact", "File 04: 接触, Contact")}

{buttons}

<br><br>

<img src="{CLIPS["ryuk-tower"][0]}" width="46%" alt="{CLIPS["ryuk-tower"][1]}">

<sub><i>"Humans are so interesting." — Ryuk</i></sub>

</div>
"""


def main() -> None:
    ensure_fonts()
    fonts = load_fonts()
    ASSETS.mkdir(exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%d %b %Y").lstrip("0")
    total = contributions_last_year()
    footer_right = f"{total:,} contributions in the last year" if total is not None else f"github.com/{USER}"

    write("banner.svg", banner.render(fonts))
    source, tint = note.render(fonts.serif_bold.path)
    art = ascii_card.Art(source, tint, "~/death-note", "dropped from the shinigami realm",
                         "ASCII art: the Death Note, bleeding, gripped by a shinigami's claw")
    for theme in THEMES:
        suffix = f"-{theme.name}.svg"
        frame = cards.panel(theme, ascii_card.WIDTH, ascii_card.HEIGHT, "SHINIGAMI REALM · THE NOTE", f"{ascii_card.COLS}×{ascii_card.ROWS}")
        write("note" + suffix, ascii_card.render(theme, art, frame))
        write("whoami" + suffix, cards.whoami(theme, fonts, f"updated {today}", footer_right))
        write("rules" + suffix, cards.rules(theme, fonts))
        for number, (key, (kanji, english)) in enumerate(SECTIONS.items(), start=1):
            write(f"header-{key}{suffix}", cards.header(theme, fonts, number, len(SECTIONS), kanji, english))
        for key, label in BUTTONS:
            write(f"link-{key}{suffix}", cards.link_button(theme, fonts, label))
    (ROOT / "README.md").write_text(readme(), encoding="utf-8")
    print(f"built {len(list(ASSETS.glob('*.svg')))} svgs and README.md")


if __name__ == "__main__":
    main()
