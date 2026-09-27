"""Cut real Death Note anime footage into the profile's animated pieces.

    python scripts/cinema.py          # from the repo root; needs network the first time

Each piece is edited like a trailer shot: cropped to frame, graded for horror (crushed
blacks, colour drained except the reds, vignette, film grain), then titled with
letterbox bars and anime-style subtitles, and encoded as a GIF with ffmpeg.

Source clips are fetched from Tenor into scripts/scenes/ (not committed). Only the
finished GIFs in assets/ are. The footage belongs to its rights holders; it is used
here as fan tribute on a personal profile.
"""

import math
import random
import shutil
import subprocess
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageSequence

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SCENES = Path(__file__).resolve().parent / "scenes"
FONTS = Path(__file__).resolve().parent / "fonts"

SOURCES = {
    "ryuk-moon": "https://media.tenor.com/tKMTWPmmGaUAAAAC/ryuk-death-note.gif",
    "light-smile": "https://media.tenor.com/F9Yh5L2g3AYAAAAC/light-yagami.gif",
    "ryuk-eyes": "https://media.tenor.com/rW61ogX4gj8AAAAC/ryuk-death-note.gif",
    "light-laugh": "https://media.tenor.com/llfBQe-pZjIAAAAC/joblife-jl.gif",
    "ryuk-red": "https://media.tenor.com/SEy40M8j7k8AAAAC/ryuk-death-note.gif",
    "l-stare": "https://media.tenor.com/DiQoAtvjMzoAAAAC/death-note-l-death-note.gif",
    "ryuk-school": "https://media.tenor.com/fcUrOX_xwEgAAAAC/death-note-anime.gif",
    "light-writing": "https://media.tenor.com/32H8OJbPIlAAAAAC/death-note-light.gif",
    "pen": "https://media.tenor.com/1ybUFYQpNDgAAAAC/death-note-light-yagami.gif",
    "ryuk-tower": "https://media.tenor.com/0S-qY1MlqDAAAAAC/death-note-anime.gif",
}

BLOOD = (224, 48, 58)
PAPER = (239, 230, 216)
BONE = (201, 185, 154)
MUTED = (140, 128, 120)


# ---- sources ---------------------------------------------------------------------------

def fetch() -> None:
    SCENES.mkdir(exist_ok=True)
    for name, url in SOURCES.items():
        target = SCENES / f"{name}.gif"
        if not target.exists():
            print("fetching", name)
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                target.write_bytes(r.read())


@dataclass
class Clip:
    frames: list[Image.Image]
    times: list[float]  # start time of each frame, seconds
    length: float

    def at(self, t: float) -> Image.Image:
        """The frame showing at time t (looping)."""
        t %= self.length
        lo = 0
        for i, start in enumerate(self.times):
            if start <= t:
                lo = i
        return self.frames[lo]


def clip(name: str, start: float = 0.0, end: float | None = None) -> Clip:
    im = Image.open(SCENES / f"{name}.gif")
    frames, times, t = [], [], 0.0
    for frame in ImageSequence.Iterator(im):
        dur = max(frame.info.get("duration", 100), 20) / 1000
        if t + dur > start and (end is None or t < end):
            frames.append(frame.convert("RGB"))
            times.append(max(0.0, t - start))
        t += dur
    length = (min(end, t) if end else t) - start
    return Clip(frames, times, length)


# ---- look ------------------------------------------------------------------------------

def cover(img: Image.Image, w: int, h: int, fx: float = 0.5, fy: float = 0.5, zoom: float = 1.0) -> Image.Image:
    """Scale to fill w x h, cropping around the focus point (fx, fy)."""
    s = max(w / img.width, h / img.height) * zoom
    big = img.resize((max(w, round(img.width * s)), max(h, round(img.height * s))), Image.LANCZOS)
    x = round((big.width - w) * fx)
    y = round((big.height - h) * fy)
    return big.crop((x, y, x + w, y + h))


def _grain(w: int, h: int, n: int = 4, seed: int = 7) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    return [rng.normal(0, 1, (h, w, 1)).astype(np.float32) for _ in range(n)]


_GRAIN: dict[tuple[int, int], list[np.ndarray]] = {}


def horror(img: Image.Image, i: int, strength: float = 1.0, red_keep: float = 1.25, grain: float = 0.035) -> Image.Image:
    """Crushed blacks, colour drained except the reds, a red cast in the shadows, vignette, grain."""
    a = np.asarray(img).astype(np.float32) / 255
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    redness = np.clip((r - np.maximum(g, b)) * 3.2, 0, 1)[..., None]
    sat = 0.22 + (red_keep - 0.22) * redness
    x = lum[..., None] + (a - lum[..., None]) * sat
    x = np.clip((x - 0.05) / 0.92, 0, 1)
    x = x * x * (3 - 2 * x) * 0.65 + x * 0.35  # S-curve
    shadow = (1 - lum[..., None]) ** 2
    x = x + shadow * np.array([0.06, -0.015, -0.01], np.float32) * strength
    h, w = lum.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    v = 1 - 0.55 * (((xx / w - 0.5) / 0.62) ** 2 + ((yy / h - 0.5) / 0.7) ** 2)
    x = x * np.clip(v, 0.25, 1)[..., None]
    grains = _GRAIN.setdefault((w, h), _grain(w, h))
    x = x + grains[i % len(grains)] * grain
    return Image.fromarray((np.clip(x, 0, 1) * 255).astype(np.uint8))


def cctv(img: Image.Image, i: int) -> Image.Image:
    """Security-camera footage: grey-green, soft, noisy, with scanlines."""
    a = np.asarray(img.filter(ImageFilter.GaussianBlur(0.6))).astype(np.float32) / 255
    lum = (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2])[..., None]
    x = np.clip((lum - 0.04) * 1.25, 0, 1) * np.array([0.86, 1.0, 0.9], np.float32)
    h, w = x.shape[:2]
    grains = _GRAIN.setdefault((w, h), _grain(w, h))
    x = x + grains[i % len(grains)] * 0.05
    x[::3] *= 0.78  # scanlines
    return Image.fromarray((np.clip(x, 0, 1) * 255).astype(np.uint8))


# ---- type ------------------------------------------------------------------------------

def font(name: str, size: int, weight: float | None = None) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(FONTS / name), size)
    if weight is not None:
        try:
            f.set_variation_by_axes([weight])
        except OSError:
            pass
    return f


def glow_text(base: Image.Image, xy, text: str, f, fill, glow=(0, 0, 0), radius: int = 6, anchor: str = "la",
              stroke: int = 0) -> None:
    """Text with a soft dark halo so it reads over footage."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text(xy, text, font=f, fill=glow + (255,), anchor=anchor, stroke_width=stroke + 3, stroke_fill=glow + (255,))
    base.alpha_composite(layer.filter(ImageFilter.GaussianBlur(radius)))
    d2 = ImageDraw.Draw(base)
    d2.text(xy, text, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0))


def subtitle(base: Image.Image, cx: float, y: float, text: str, size: int = 22, alpha: float = 1.0) -> None:
    """Anime-style subtitle: white, black outline, centred."""
    if alpha <= 0:
        return
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((cx, y), text, font=font("FamiljenGrotesk[wght].ttf", size, 560), fill=(255, 255, 255, 255),
                               anchor="ms", stroke_width=3, stroke_fill=(0, 0, 0, 255))
    if alpha < 1:
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha)))
    base.alpha_composite(layer)


def letterbox(base: Image.Image, bar: int, left: str, right: str, kanji: str = "") -> None:
    d = ImageDraw.Draw(base)
    w, h = base.size
    d.rectangle((0, 0, w, bar), fill=(0, 0, 0, 255))
    d.rectangle((0, h - bar, w, h), fill=(0, 0, 0, 255))
    mono = font("JetBrainsMono[wght].ttf", 11, 500)
    d.text((14, bar / 2), left, font=mono, fill=MUTED, anchor="lm")
    x = w - 14
    d.text((x, bar / 2), right, font=mono, fill=MUTED, anchor="rm")
    if kanji:
        tw = d.textlength(right, font=mono)
        d.text((x - tw - 8, bar / 2 + 1), kanji, font=font("YujiBoku-Regular.ttf", 13), fill=BLOOD, anchor="rm")


def fade_edge(w: int, h: int, x0: int, x1: int) -> Image.Image:
    """An alpha mask: opaque from x1 rightwards, fading to clear at x0."""
    ramp = np.clip((np.arange(w, dtype=np.float32) - x0) / max(1, x1 - x0), 0, 1) ** 1.6
    return Image.fromarray((np.tile(ramp, (h, 1)) * 255).astype(np.uint8))


# ---- encoding --------------------------------------------------------------------------

def encode(frames: list[Image.Image], fps: float, out: Path, colors: int = 192, dither: str = "sierra2_4a") -> None:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    with tempfile.TemporaryDirectory() as tmp:
        for i, f in enumerate(frames):
            f.convert("RGB").save(f"{tmp}/f{i:04d}.png")
        graph = (
            f"[0:v]split[a][b];[a]palettegen=max_colors={colors}:stats_mode=full[p];"
            f"[b][p]paletteuse=dither={dither}:diff_mode=rectangle"
        )
        subprocess.run(
            [ffmpeg, "-v", "error", "-y", "-framerate", str(fps), "-i", f"{tmp}/f%04d.png",
             "-filter_complex", graph, "-loop", "0", str(out)],
            check=True,
        )
    print(f"{out.name}: {len(frames)} frames, {out.stat().st_size / 1e6:.1f} MB")


def timeline(shots: list[tuple[Clip, float]], fps: float) -> list[tuple[int, Clip, float, float]]:
    """(shot index, clip, time within shot, shot progress 0..1) for every output frame."""
    out = []
    for k, (c, dur) in enumerate(shots):
        n = round(dur * fps)
        for j in range(n):
            out.append((k, c, j / fps, j / max(1, n - 1)))
    return out


# ---- the pieces ------------------------------------------------------------------------

def hero() -> None:
    """The banner: a trailer cut behind the name."""
    W, H, fps, bar = 1000, 400, 12, 26
    scene_x = 330
    shots = [
        (clip("ryuk-moon"), 1.6),
        (clip("light-smile"), 2.4),
        (clip("ryuk-eyes"), 1.6),
        (clip("light-laugh", 2.6, 5.4), 2.6),
        (clip("ryuk-red"), 1.8),
    ]
    subs = {1: "I will become the god of the new world.", 3: "I win."}
    focus = {0: (0.5, 0.5), 1: (0.62, 0.5), 2: (0.5, 0.45), 3: (0.55, 0.5), 4: (0.5, 0.5)}
    mask = fade_edge(W - scene_x, H, 0, 190)
    gothic = font("GrenzeGotisch[wght].ttf", 70, 640)
    frames = []
    for i, (k, c, t, p) in enumerate(timeline(shots, fps)):
        base = Image.new("RGBA", (W, H), (5, 3, 4, 255))
        shot = horror(cover(c.at(t), W - scene_x, H, *focus[k], zoom=1.0 + 0.04 * p), i)
        # a quick flash on each cut, and a fade to black at the end of the loop
        if p < 0.12 and k > 0:
            shot = Image.blend(shot, Image.new("RGB", shot.size, (255, 235, 230)), 0.55 * (1 - p / 0.12))
        if k == len(shots) - 1 and p > 0.75:
            shot = Image.blend(shot, Image.new("RGB", shot.size, (0, 0, 0)), (p - 0.75) / 0.25)
        base.paste(shot, (scene_x, 0), mask)
        if k in subs:
            subtitle(base, scene_x + (W - scene_x) / 2 + 40, H - bar - 16, subs[k], 21, min(1, p * 6, (1 - p) * 6))
        x = 40
        glow_text(base, (x, 92), "APS COLLEGE OF ENGINEERING  ·  B.E. CSE", font("JetBrainsMono[wght].ttf", 12, 500), MUTED)
        glow_text(base, (x, 112), "Likith Lochan", gothic, PAPER, radius=10)
        ImageDraw.Draw(base).rectangle((x, 204, x + 110, 206), fill=BLOOD)
        glow_text(base, (x, 222), "DevOps · Backend/Full-Stack · Applied AI", font("FamiljenGrotesk[wght].ttf", 21, 560), PAPER)
        glow_text(base, (x, 252), "Kubernetes, Terraform, AIOps and RAG", font("FamiljenGrotesk[wght].ttf", 18, 400), BONE)
        glow_text(base, (x, 290), "“The incident whose name is written here", font("CormorantGaramond-Italic[wght].ttf", 20, 500), (170, 158, 146))
        glow_text(base, (x, 314), "shall be resolved.”", font("CormorantGaramond-Italic[wght].ttf", 20, 500), (170, 158, 146))
        glow_text(base, (x, 344), "OPEN TO  ·  DEVOPS/CLOUD  ·  BACKEND  ·  SDE  ·  AI-ML", font("JetBrainsMono[wght].ttf", 10, 600), BLOOD)
        letterbox(base, bar, "DEATH NOTE", "EP.01  REBIRTH", "新生")
        frames.append(base)
    encode(frames, fps, ASSETS / "hero.gif", colors=200)


def surveillance() -> None:
    """Two security feeds, sized to sit beside the whoami card."""
    W, H, fps = 860, 1000, 10
    feed_h = 440
    stare, school = clip("l-stare"), clip("ryuk-school")
    n = round(5.2 * fps)
    mono = font("JetBrainsMono[wght].ttf", 15, 600)
    small = font("JetBrainsMono[wght].ttf", 13, 500)
    frames = []
    for i in range(n):
        t = i / fps
        base = Image.new("RGBA", (W, H), (8, 8, 8, 255))
        d = ImageDraw.Draw(base)
        d.rectangle((0, 0, W, 54), fill=(16, 16, 16))
        d.text((24, 27), "KIRA INVESTIGATION  ·  LIVE SURVEILLANCE", font=mono, fill=(200, 200, 190), anchor="lm")
        d.text((W - 24, 27), "2 FEEDS", font=small, fill=MUTED, anchor="rm")
        for k, (c, label, ts0, fy) in enumerate(((stare, "CAM 01  ·  TASK FORCE HQ", 22 * 3600 + 14 * 60 + 7, 0.4),
                                                 (school, "CAM 02  ·  DAIKOKU PRIVATE ACADEMY", 15 * 3600 + 32 * 60 + 51, 0.45))):
            y0 = 74 + k * (feed_h + 26)
            feed = cctv(cover(c.at(t), W - 48, feed_h, 0.5, fy), i + k)
            base.paste(feed, (24, y0))
            d.rectangle((24, y0, W - 24, y0 + feed_h), outline=(60, 60, 60), width=2)
            if (i // 5) % 2 == 0:
                d.ellipse((42, y0 + 20, 56, y0 + 34), fill=BLOOD)
            d.text((64, y0 + 27), "REC", font=mono, fill=(235, 235, 225), anchor="lm")
            d.text((W - 42, y0 + 27), label, font=small, fill=(235, 235, 225), anchor="rm")
            secs = ts0 + int(t)
            stamp = f"2026-09-27  {secs // 3600 % 24:02d}:{secs // 60 % 60:02d}:{secs % 60:02d}"
            d.text((42, y0 + feed_h - 22), stamp, font=small, fill=(235, 235, 225), anchor="lm")
            if k == 1:
                warn = (i // 3) % 2 == 0
                d.rectangle((W - 330, y0 + feed_h - 44, W - 42, y0 + feed_h - 12), fill=BLOOD if warn else (60, 8, 12))
                d.text((W - 186, y0 + feed_h - 28), "SIGNAL ANOMALY DETECTED", font=small, fill=(255, 240, 235), anchor="mm")
        d.text((24, H - 26), "subject: LIKITH LOCHAN  ·  status: under observation", font=small, fill=MUTED, anchor="lm")
        frames.append(base)
    encode(frames, fps, ASSETS / "surveillance.gif", colors=96, dither="bayer:bayer_scale=3")


def the_note() -> None:
    """Light writing in the note, cut with the pen, and his line."""
    W, H, fps, bar = 1000, 300, 12, 24
    shots = [(clip("light-writing", 0, 2.4), 2.4), (clip("pen", 0.4, 3.4), 3.0)]
    frames = []
    for i, (k, c, t, p) in enumerate(timeline(shots, fps)):
        base = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        shot = horror(cover(c.at(t), W, H, 0.5, 0.45, zoom=1.0 + 0.05 * p), i, red_keep=1.4)
        if p < 0.1 and k > 0:
            shot = Image.blend(shot, Image.new("RGB", shot.size, (255, 235, 230)), 0.5 * (1 - p / 0.1))
        base.paste(shot, (0, 0))
        if k == 1:
            subtitle(base, W / 2, H - bar - 14, "I am justice.", 24, min(1, p * 5, (1 - p) * 5))
        letterbox(base, bar, "DEATH NOTE", "HOW TO USE IT", "掟")
        frames.append(base)
    encode(frames, fps, ASSETS / "the-note.gif", colors=160)


def outro() -> None:
    """Ryuk on the tower in the wind, and his line."""
    W, H, fps, bar = 1000, 300, 10, 24
    c = clip("ryuk-tower")
    n = round(c.length * 2 * fps)
    frames = []
    for i in range(n):
        t = i / fps
        p = (t % c.length) / c.length
        base = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        shot = horror(cover(c.at(t), W, H, 0.5, 0.35), i, red_keep=1.1, grain=0.03)
        base.paste(shot, (0, 0))
        subtitle(base, W / 2, H - bar - 14, "Humans are so interesting.", 22, 1.0)
        letterbox(base, bar, "DEATH NOTE", "RYUK", "死神")
        frames.append(base)
    encode(frames, fps, ASSETS / "outro.gif", colors=160)


def main() -> None:
    fetch()
    ASSETS.mkdir(exist_ok=True)
    hero()
    surveillance()
    the_note()
    outro()


if __name__ == "__main__":
    main()
