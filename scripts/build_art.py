#!/usr/bin/env python3
"""Build the SVG artwork used by README.md.

Writes assets/covers/hand-walker.svg. Display type is outlined from Google
Fonts subsets so the image looks the same on every system.

Requires fontTools and network access:

    pip install fonttools
    python3 scripts/build_art.py
"""

import io
import random
import re
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def num(v):
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


class Face:
    """A Google Fonts subset that can turn text into SVG path data."""

    def __init__(self, family, text):
        css = urlopen(
            f"https://fonts.googleapis.com/css2?family={family}&text={quote(text)}"
        ).read().decode()
        url = re.search(r"url\((\S+?)\)", css).group(1)
        self.font = TTFont(io.BytesIO(urlopen(url).read()))
        self.glyphs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.upm = self.font["head"].unitsPerEm

    def advance(self, ch, size):
        return self.glyphs[self.cmap[ord(ch)]].width * size / self.upm

    def glyph(self, ch, size, x, baseline):
        s = size / self.upm
        pen = SVGPathPen(self.glyphs, ntos=num)
        self.glyphs[self.cmap[ord(ch)]].draw(TransformPen(pen, (s, 0, 0, -s, x, baseline)))
        return pen.getCommands()

    def width(self, text, size, tracking=0):
        return sum(self.advance(ch, size) for ch in text) + tracking * (len(text) - 1)

    def line(self, text, size, x, baseline, tracking=0):
        parts = []
        for ch in text:
            parts.append(self.glyph(ch, size, x, baseline))
            x += self.advance(ch, size) + tracking
        return " ".join(p for p in parts if p)

    def column(self, text, size, cx, top, gap=0):
        """Vertical CJK text: one em box per character, centred on cx."""
        parts = []
        for ch in text:
            parts.append(self.glyph(ch, size, cx - self.advance(ch, size) / 2, top + 0.88 * size))
            top += size + gap
        return " ".join(parts)


def gradient(gid, stops, x2=0, y2=1):
    rows = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
    return f'<linearGradient id="{gid}" x1="0" y1="0" x2="{x2}" y2="{y2}">{rows}</linearGradient>'


# ---------------------------------------------------------------------------
# Cover for 《手行者》: a school corridor at dusk. The title stands upright on
# the wall and hangs upside down in the window glass.


def hand_walker_cover(serif, byline):
    w, h = 960, 540
    rng = random.Random(11)
    el = [
        f'<rect width="{w}" height="{h}" fill="#2A2D49"/>',
        '<rect y="392" width="960" height="80" fill="#1D3932"/>',
        '<rect y="389" width="960" height="4" fill="#2D5146"/>',
        '<rect y="470" width="960" height="70" fill="#3A3A46"/>',
        '<rect y="470" width="960" height="3" fill="#2A2A33"/>',
    ]
    chips = "".join(
        f'<circle cx="{num(rng.uniform(0, w))}" cy="{num(rng.uniform(476, h))}" '
        f'r="{num(rng.uniform(0.8, 2.2))}" fill="{rng.choice(["#6B6B78", "#8A8576", "#55625C", "#9C8F7A"])}"/>'
        for _ in range(260)
    )
    el.append(f"<g>{chips}</g>")

    # Window: two tall casements; the title hangs upside down in the right one.
    fx, fy, fw, fh, frame = 500, 56, 380, 316, 12
    gx, gy, gw, gh = fx + frame, fy + frame, fw - 2 * frame, fh - 2 * frame
    pane_cx = gx + gw * 3 / 4 + 2.5
    ghost = serif.column("手行者", 76, pane_cx, gy + (gh - (3 * 76 + 2 * 8)) / 2, 8)
    el.append(
        f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" fill="#151831"/>'
        f'<rect x="{gx}" y="{gy}" width="{gw}" height="{gh}" fill="url(#glass)"/>'
        f'<path d="{ghost}" fill="#FFFFFF" opacity="0.22" '
        f'transform="rotate(180 {num(pane_cx)} {num(gy + gh / 2)})"/>'
        f'<rect x="{gx + gw / 2 - 5}" y="{gy}" width="10" height="{gh}" fill="#151831"/>'
        f'<rect x="{fx - 10}" y="{fy + fh}" width="{fw + 20}" height="8" fill="#3B3F60"/>'
    )

    # Title and byline.
    el.append(f'<path d="{serif.column("手行者", 100, 206, 58, 10)}" fill="#F2EADB"/>')
    by_x = 206 - byline.width("Kimi K2.7 著", 24) / 2
    el.append(f'<path d="{byline.line("Kimi K2.7 著", 24, by_x, 438)}" fill="#BFD8CC"/>')

    defs = gradient("glass", [(0, "#34336A"), (0.55, "#A9637A"), (1, "#EFA585")])
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" '
        f'aria-label="手行者 by Kimi K2.7"><defs>{defs}</defs>{"".join(el)}</svg>\n'
    )


def main():
    serif = Face("Noto+Serif+SC:wght@900", "手行者")
    byline = Face("Noto+Serif+SC:wght@600", "Kimi K2.7 著")
    (ASSETS / "covers").mkdir(parents=True, exist_ok=True)
    (ASSETS / "covers" / "hand-walker.svg").write_text(hand_walker_cover(serif, byline), encoding="utf-8")


if __name__ == "__main__":
    main()
