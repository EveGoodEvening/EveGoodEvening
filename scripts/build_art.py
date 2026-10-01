#!/usr/bin/env python3
"""Build the SVG artwork used by README.md.

Writes assets/hero-dusk.svg (light theme), assets/hero-night.svg (dark theme)
and assets/covers/hand-walker.svg. Display type is outlined from Google Fonts
subsets so the images look the same on every system.

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
# Hero: an old neighbourhood as evening falls. Light theme is dusk, dark theme
# is night. Windows come on one by one, then the 晚上好 sign flickers on.

HERO_W, HERO_H = 1200, 400
FLOOR = 30

HERO_THEMES = {
    "dusk": {
        "sky": [(0, "#6E79BF"), (0.5, "#B3A3D3"), (0.82, "#EEB6A3"), (1, "#F6CEAD")],
        "far": "#8B7EAF",
        "near": "#3A3257",
        "tree": "#2F2849",
        "window": "#4A4167",
        "lit": ["#FFC567", "#FFD98C", "#FFB45C"],
        "lit_ratio": 0.22,
        "ink": "#211A43",
        "moon_opacity": 0.55,
        "halo": 0,
        "stars": 0,
        "glow": 0.3,
        "sign_box": "#2A1A30",
        "edge": 0,
    },
    "night": {
        "sky": [(0, "#0D1331"), (0.55, "#1E2250"), (0.85, "#372A58"), (1, "#4A305E")],
        "far": "#191B3F",
        "near": "#0E1128",
        "tree": "#0A0C1F",
        "window": "#1A1E3C",
        "lit": ["#FFC567", "#FFD98C", "#FFB45C", "#FFC567", "#9FC6FF"],
        "lit_ratio": 0.42,
        "ink": "#F2EADB",
        "moon_opacity": 1,
        "halo": 0.07,
        "stars": 34,
        "glow": 0.5,
        "sign_box": "#1A0E1E",
        "edge": 0.08,
    },
}

# (x, width, floors) for the old six-storey blocks in front.
BLOCKS = [(24, 300, 4), (352, 206, 3), (800, 172, 7), (992, 208, 5)]


def hero(theme, serif, italic):
    t = HERO_THEMES[theme]
    rng = random.Random(7)
    el = []

    # Sky, stars, moon.
    el.append(f'<rect width="{HERO_W}" height="{HERO_H}" fill="url(#sky)"/>')
    for _ in range(t["stars"]):
        x, y = rng.uniform(20, 1180), rng.uniform(14, 230)
        if x < 600 and y < 190:  # keep the headline clear
            x += 600
        el.append(
            f'<circle cx="{num(x)}" cy="{num(y)}" r="{num(rng.uniform(0.7, 1.6))}" '
            f'fill="#FFFFFF" opacity="{num(rng.uniform(0.35, 0.9))}"/>'
        )
    el.append(
        f'<g opacity="{t["moon_opacity"]}"><circle cx="1108" cy="74" r="44" fill="#FFF3D6" opacity="{t["halo"]}"/>'
        '<circle cx="1108" cy="74" r="23" fill="#FFF3D6" mask="url(#crescent)"/></g>'
    )

    # Far layer: new towers and a tower crane, the city coming for the old blocks.
    far = t["far"]
    el.append(
        f'<g fill="{far}"><rect x="438" y="196" width="66" height="204"/>'
        f'<rect x="688" y="150" width="78" height="250"/><rect x="684" y="142" width="86" height="10"/>'
        f'<rect x="597" y="122" width="7" height="278"/><path d="M596 122 L600.5 100 L605 122Z"/>'
        f'<rect x="566" y="120" width="210" height="5"/><rect x="568" y="125" width="24" height="10"/>'
        f'<rect x="730" y="125" width="10" height="6"/></g>'
        f'<g stroke="{far}" stroke-width="1.4" fill="none"><path d="M600.5 101 L578 121 M600.5 101 L768 121"/>'
        f'<path d="M735 131 V 188"/></g>'
        f'<rect x="731" y="188" width="8" height="5" fill="{far}"/>'
        f'<circle cx="600.5" cy="99" r="2.4" fill="#FF5A5A" opacity="{t["glow"] + 0.3}"/>'
    )

    # Street-level shop row between the blocks.
    near = t["near"]
    el.append(
        f'<rect x="560" y="346" width="244" height="54" fill="{near}"/>'
        f'<rect x="554" y="342" width="256" height="6" fill="{near}"/>'
    )
    shutters = []
    for sx in (574, 726):
        shutters += [f'<rect x="{sx}" y="{y}" width="60" height="1.5"/>' for y in range(358, 398, 5)]
    el.append(f'<g fill="{t["window"]}">{"".join(shutters)}</g>')

    # Old blocks with window grids and air conditioners.
    windows = []
    for x, w, floors in BLOCKS:
        top = HERO_H - floors * FLOOR - 8
        el.append(f'<rect x="{x}" y="{top}" width="{w}" height="{HERO_H - top}" fill="{near}"/>')
        el.append(f'<rect x="{x - 4}" y="{top - 4}" width="{w + 8}" height="5" fill="{near}"/>')
        cols = (w - 20) // 24
        offset = x + (w - (cols * 24 - 12)) / 2
        for row in range(floors):
            for col in range(cols):
                windows.append((offset + col * 24, top + 14 + row * FLOOR))
    # Rooftop clutter: water tanks and TV aerials.
    el.append(
        f'<g fill="{near}"><rect x="70" y="252" width="34" height="18"/><rect x="74" y="268" width="3" height="6"/>'
        f'<rect x="97" y="268" width="3" height="6"/><rect x="1060" y="222" width="40" height="20"/>'
        f'<rect x="890" y="166" width="3" height="16"/></g>'
        f'<g stroke="{near}" stroke-width="2" fill="none"><path d="M250 270 V 244 M240 250 H 262 M243 256 H 258"/>'
        f'<path d="M1150 242 V 214 M1140 220 H 1162 M1143 227 H 1159"/><path d="M880 172 H 904"/></g>'
    )

    lit_marks, dark_marks, ac_units = [], [], []
    lit_cells = []
    for wx, wy in windows:
        if rng.random() < 0.12:
            ac_units.append(f'<rect x="{num(wx + 12.5)}" y="{num(wy + 7)}" width="8" height="6"/>')
        if rng.random() < t["lit_ratio"]:
            lit_cells.append((wx, wy, rng.choice(t["lit"])))
        else:
            dark_marks.append(f'<rect x="{num(wx)}" y="{num(wy)}" width="11" height="14"/>')
    el.append(f'<g fill="{t["window"]}">{"".join(dark_marks)}{"".join(ac_units)}</g>')
    lit_cells.append((656, 356, "#FFD27F"))  # the corner shop, 56 wide
    rng.shuffle(lit_cells)
    for i, (wx, wy, color) in enumerate(lit_cells):
        delay = 0.25 + 2.4 * i / len(lit_cells)
        size = 'width="56" height="40"' if (wx, wy) == (656, 356) else 'width="11" height="14"'
        lit_marks.append(
            f'<rect class="on" style="animation-delay:{delay:.2f}s" x="{num(wx)}" y="{num(wy)}" {size} fill="{color}"/>'
        )
    el.append(f'<g>{"".join(lit_marks)}</g>')
    el.append(
        f'<g fill="{near}"><rect x="682" y="356" width="4" height="40"/><rect x="652" y="350" width="64" height="6"/></g>'
    )

    # A pagoda tree with a red lantern nobody hung.
    canopy = [(372, 296, 34), (404, 284, 30), (434, 302, 28), (392, 318, 30), (346, 316, 24)]
    el.append(
        f'<g fill="{t["tree"]}"><rect x="384" y="320" width="10" height="80"/>'
        + "".join(f'<circle cx="{cx}" cy="{cy}" r="{r}"/>' for cx, cy, r in canopy)
        + "</g>"
        f'<path d="M418 318 V 334" stroke="{t["tree"]}" stroke-width="1.2"/>'
        f'<circle cx="418" cy="342" r="14" fill="#FF4D4D" opacity="{t["glow"] * 0.35}"/>'
        f'<ellipse cx="418" cy="342" rx="6" ry="7.5" fill="#E8484D"/>'
        f'<g fill="{t["tree"]}"><rect x="414.5" y="333" width="7" height="2.4"/>'
        f'<rect x="414.5" y="348.6" width="7" height="2.4"/><rect x="417.4" y="351" width="1.2" height="6"/></g>'
    )

    # Sodium streetlamp; its camera has been watching the gate for years.
    el.append(
        f'<circle cx="702" cy="262" r="80" fill="url(#lamp)" opacity="{t["glow"]}"/>'
        f'<g fill="{near}"><rect x="664" y="262" width="5" height="138"/><rect x="638" y="300" width="28" height="3"/>'
        f'<path d="M631 296 h 14 v 12 h -14 z"/><path d="M624 299 h 8 v 6 h -8 z"/></g>'
        f'<path d="M666.5 264 Q 668 252 690 256" stroke="{near}" stroke-width="4" fill="none"/>'
        f'<ellipse cx="702" cy="259" rx="14" ry="4.5" fill="{near}"/>'
        f'<ellipse cx="702" cy="262" rx="9" ry="2.4" fill="#FFD27A"/>'
        f'<circle cx="634" cy="302" r="1.8" fill="#FF3B3B"/>'
    )

    # The vertical neon sign.
    size, gap, pad = 42, 6, 14
    sign_h = 3 * size + 2 * gap + 2 * pad
    sx, sy, sw = 754, 196, 56
    glyphs = serif.column("晚上好", size, sx + sw / 2, sy + pad, gap)
    el.append(
        f'<g fill="{near}"><rect x="{sx + sw - 4}" y="{sy + 18}" width="16" height="4"/>'
        f'<rect x="{sx + sw - 4}" y="{sy + sign_h - 22}" width="16" height="4"/></g>'
        f'<rect x="{sx}" y="{sy}" width="{sw}" height="{sign_h}" rx="4" fill="{t["sign_box"]}" '
        f'stroke="{near}" stroke-width="3"/>'
        f'<g class="sign"><path d="{glyphs}" fill="#FF4F6D" filter="url(#neon)" opacity="{t["glow"] + 0.4}"/>'
        f'<path d="{glyphs}" fill="#FF7A8C"/>'
        f'<path d="{glyphs}" fill="none" stroke="#FFE3E8" stroke-width="0.8" opacity="0.7"/></g>'
    )

    # Headline.
    el.append(f'<path d="{italic.line("Good evening", 88, 62, 150)}" fill="{t["ink"]}"/>')
    if t["edge"]:
        el.append(
            f'<rect x="0.5" y="0.5" width="{HERO_W - 1}" height="{HERO_H - 1}" rx="19.5" '
            f'fill="none" stroke="#FFFFFF" stroke-opacity="{t["edge"]}"/>'
        )

    defs = (
        gradient("sky", t["sky"])
        + '<radialGradient id="lamp"><stop offset="0" stop-color="#FFB547"/>'
        '<stop offset="1" stop-color="#FFB547" stop-opacity="0"/></radialGradient>'
        '<mask id="crescent"><rect width="1200" height="400" fill="#000"/>'
        '<circle cx="1108" cy="74" r="23" fill="#FFF"/><circle cx="1118" cy="66" r="21" fill="#000"/></mask>'
        '<filter id="neon" x="-50%" y="-20%" width="200%" height="140%">'
        '<feGaussianBlur stdDeviation="4"/></filter>'
        f'<clipPath id="tile"><rect width="{HERO_W}" height="{HERO_H}" rx="20"/></clipPath>'
    )
    style = (
        ".on{animation:on .6s ease-out both}"
        ".sign{animation:neon 1.2s linear 2.9s both}"
        "@keyframes on{from{opacity:0}}"
        "@keyframes neon{0%{opacity:0}8%{opacity:1}12%{opacity:.1}20%{opacity:1}"
        "25%{opacity:.35}33%,100%{opacity:1}}"
        "@media (prefers-reduced-motion:reduce){.on,.sign{animation:none}}"
    )
    label = "Good evening, with 晚上好 on a neon sign over an old neighbourhood"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {HERO_W} {HERO_H}" role="img" aria-label="{label}">'
        f"<style>{style}</style><defs>{defs}</defs>"
        f'<g clip-path="url(#tile)">{"".join(el)}</g></svg>\n'
    )


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
    serif = Face("Noto+Serif+SC:wght@900", "晚上好手行者")
    byline = Face("Noto+Serif+SC:wght@600", "Kimi K2.7 著")
    italic = Face("EB+Garamond:ital,wght@1,500", "Good evening")
    (ASSETS / "covers").mkdir(parents=True, exist_ok=True)
    for theme in HERO_THEMES:
        (ASSETS / f"hero-{theme}.svg").write_text(hero(theme, serif, italic), encoding="utf-8")
    (ASSETS / "covers" / "hand-walker.svg").write_text(hand_walker_cover(serif, byline), encoding="utf-8")


if __name__ == "__main__":
    main()
