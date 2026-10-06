#!/usr/bin/env python3
"""Build the SVG artwork used by README.md.

Writes assets/covers/hand-walker.svg, a self-contained 960×540 cover with
procedural corridor artwork. Type is outlined from Google Fonts subsets;
viewing the generated SVG requires no external images or fonts.

Requires fontTools and network access:

    pip install fonttools
    python3 scripts/build_art.py
"""

import io
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

    def line(self, text, size, x, baseline, tracking=0):
        parts = []
        for ch in text:
            parts.append(self.glyph(ch, size, x, baseline))
            x += self.advance(ch, size) + tracking
        return " ".join(p for p in parts if p)


def gradient(gid, stops, x2=0, y2=1):
    rows = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
    return f'<linearGradient id="{gid}" x1="0" y1="0" x2="{x2}" y2="{y2}">{rows}</linearGradient>'


# Cover for 《手行者》: a corridor seen from close to the floor, with an
# inverted figure in the glass. Typography stays separate from the perspective.


def hand_walker_cover(serif, byline):
    w, h = 960, 540
    defs = "".join([
        gradient("wall", [(0, "#263C3C"), (1, "#52625B")], 1, 0),
        gradient("floor", [(0, "#687168"), (1, "#202E30")]),
        gradient("glass", [(0, "#647F83"), (0.6, "#B7B397"), (1, "#EDC891")]),
        gradient("light", [(0, "#E2BA84"), (1, "#9B9675")]),
        '<linearGradient id="shade" x2="1" y2="0">'
        '<stop stop-color="#101F24"/><stop offset="0.34" stop-color="#101F24"/>'
        '<stop offset="0.49" stop-color="#101F24" stop-opacity="0.9"/>'
        '<stop offset="0.68" stop-color="#101F24" stop-opacity="0.12"/>'
        '<stop offset="1" stop-color="#101F24" stop-opacity="0"/></linearGradient>',
        '<radialGradient id="edge"><stop offset="0.45" stop-color="#08161A" stop-opacity="0"/>'
        '<stop offset="1" stop-color="#08161A" stop-opacity="0.26"/></radialGradient>',
        '<filter id="grain" x="0" y="0" width="100%" height="100%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.72" numOctaves="3" stitchTiles="stitch"/>'
        '<feColorMatrix type="saturate" values="0"/></filter>',
        '<filter id="reflection"><feGaussianBlur stdDeviation="0.6"/></filter>',
        '<path id="handprint" d="M-7 23 L6 23 C7 16 10 12 11 7 L19 -3 '
        'C22 -7 18 -10 15 -6 L10 -1 L11 -21 C11 -26 6 -26 6 -21 L5 -10 '
        'L4 -30 C4 -35 -1 -35 -1 -30 L-1 -11 L-4 -27 C-5 -32 -10 -31 -9 -26 '
        'L-7 -8 L-12 -18 C-14 -22 -18 -20 -16 -16 L-12 0 C-13 10 -9 15 -7 23 Z"/>',
    ])
    el = [
        '<rect width="960" height="540" fill="#15272B"/>',
        # All architectural edges recede towards (650, 232).
        '<path d="M220 -80 H1060 L732 170 H564 Z" fill="#293C3C"/>',
        '<path d="M220 -80 L564 170 V294 L220 540 H0 V0 Z" fill="#344848"/>',
        '<path d="M564 170 H732 V294 H564 Z" fill="#718078"/>',
        '<path d="M1060 -80 L732 170 V294 L1060 540 Z" fill="url(#wall)"/>',
        '<path d="M220 540 L564 294 H732 L1060 540 Z" fill="url(#floor)"/>',
        # A distant classroom door, not a second focal point.
        '<path d="M594 209 H626 V294 H594 Z" fill="#344B4B"/>',
        '<path d="M598 213 H622 V252 H598 Z" fill="#8A9A88"/>',
        '<path d="M644 199 H692 V266 H644 Z" fill="#4D6460"/>',
        '<path d="M648 203 H688 V262 H648 Z" fill="#A4AB8E"/>',
        '<path d="M667 203 V262 M648 229 H688" stroke="#4D6460" stroke-width="3"/>',
        '<path d="M732 279 L1060 466 M564 279 L220 466" stroke="#1B3032" stroke-width="4"/>',
        '<path d="M732 294 L1060 540 M564 294 L220 540" stroke="#14282B" stroke-width="3"/>',
    ]

    def project(x, near_y):
        return 232 + (near_y - 232) * (x - 650) / 410

    # Tall windows and their oblique pools of light share the same perspective.
    for x0, x1 in [(736, 755), (770, 804), (824, 877), (903, 985)]:
        top0, top1 = project(x0, -22), project(x1, -22)
        bottom0, bottom1 = project(x0, 380), project(x1, 380)
        t0, t1 = (x0 - 650) / 410, (x1 - 650) / 410
        floor0, floor1 = project(x0, 540), project(x1, 540)
        el.extend([
            f'<path d="M{x0} {num(floor0)} L{x1} {num(floor1)} '
            f'L{num(x1 - 220 * t1)} {num(floor1 + 124 * t1)} '
            f'L{num(x0 - 220 * t0)} {num(floor0 + 124 * t0)} Z" '
            'fill="url(#light)" opacity="0.8"/>',
            f'<path d="M{x0} {num(top0)} L{x1} {num(top1)} '
            f'V{num(bottom1)} L{x0} {num(bottom0)} Z" '
            'fill="url(#glass)" stroke="#172E32" stroke-width="7"/>',
            f'<path d="M{x0} {num(project(x0, 125))} L{x1} {num(project(x1, 125))}" '
            'stroke="#243C3D" stroke-width="4"/>',
            f'<path d="M{x0 - 3} {num(bottom0 + 6)} L{x1 + 2} {num(bottom1 + 6)}" '
            'stroke="#8B977F" stroke-width="3"/>',
        ])

    # Only the glass contains a figure; the corridor itself is empty.
    el.append(
        '<g fill="#213A3D" opacity="0.4" filter="url(#reflection)" '
        'transform="translate(934 214) rotate(180)">'
        '<path d="M-7 -44 C-12 -46 -12 -56 -9 -61 L-11 -64 L-6 -63 L-5 -66 '
        'L-1 -64 C7 -68 13 -60 10 -53 L8 -45 L3 -42 V-35 H-5 V-42 Z"/>'
        '<path d="M-10 -36 Q0 -39 12 -35 L16 -12 L10 8 L9 48 L1 49 '
        'L-2 13 L-6 49 L-14 48 L-11 6 L-13 -15 Z"/>'
        '<path d="M-9 -35 L-17 -53 L-19 -78 L-24 -83 L-23 -87 L-14 -83 '
        'L-10 -57 L-3 -40 Z M10 -35 L20 -51 L23 -78 L29 -83 L27 -87 '
        'L17 -82 L13 -56 L4 -40 Z"/>'
        '<path d="M-10 -33 L6 -7" fill="none" stroke="#A1AB93" stroke-width="2" opacity="0.4"/>'
        '</g>'
    )

    # Wet palm marks replace footprints, echoing the opening chapter.
    for x, y, scale, angle in [(646, 493, 1.05, -22), (700, 450, -0.8, 12),
                                (665, 411, 0.6, -16), (700, 380, -0.43, 16),
                                (675, 351, 0.3, -12), (687, 328, -0.2, 10)]:
        el.append(
            f'<use href="#handprint" transform="translate({x} {y}) rotate({angle}) '
            f'scale({scale} {num(abs(scale) * 0.58)})" fill="#94A398" opacity="0.47"/>'
        )

    el.extend([
        '<rect width="960" height="540" fill="url(#edge)"/>',
        '<rect width="960" height="540" fill="url(#shade)"/>',
        '<rect width="960" height="540" filter="url(#grain)" opacity="0.055"/>',
        # The title remains legible when the cover is reduced to a README card.
        '<path d="M62 99 H99" stroke="#C68C68" stroke-width="3"/>',
        f'<path d="{byline.line("HAND WALKER", 17, 62, 139, 4)}" fill="#A6B9B4"/>',
        f'<path d="{serif.line("手行者", 112, 54, 278, 5)}" fill="#F2E9D8"/>',
        f'<path d="{byline.line("Kimi K2.7 著", 22, 62, 334)}" fill="#A6B9B4"/>',
    ])
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" '
        'aria-labelledby="title description">\n'
        '<title id="title">手行者 — Kimi K2.7 著</title>\n'
        '<desc id="description">An empty school corridor in slanting evening light. '
        'Palm prints cross the floor, and an upside-down figure appears only in the window.</desc>\n'
        f'<defs>{defs}</defs>\n' + "\n".join(el) + '\n</svg>\n'
    )


def main():
    serif = Face("Noto+Serif+SC:wght@700", "手行者")
    byline = Face("Noto+Serif+SC:wght@400", "HAND WALKERKimi K2.7 著")
    (ASSETS / "covers").mkdir(parents=True, exist_ok=True)
    (ASSETS / "covers" / "hand-walker.svg").write_text(hand_walker_cover(serif, byline), encoding="utf-8")


if __name__ == "__main__":
    main()
