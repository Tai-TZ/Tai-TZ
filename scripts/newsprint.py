"""Newsprint diagram kit for the profile README.

Ported from the Arionear editor's ``scripts/build_diagrams.py`` (same author), so the profile wears the
same editorial identity: newsprint paper, ink line-art isometric blocks with hatched faces, editorial red
for the live flow, square corners, hard offset shadows, Playfair / Source Serif / JetBrains Mono stacks.
Standard library only. SVGs are self-contained and animate with CSS + SMIL.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from html import escape
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parents[1] / "assets"
BRAND = "TAI-TZ"

ISO = math.tan(math.radians(30))  # vertical / horizontal ratio of an isometric top face
W = 1040  # canvas width
M = 40  # outer margin
GUTTER = M + 44  # content starts here when lanes carry a rotated label in the left gutter

DISPLAY = "'Playfair Display', Georgia, 'Times New Roman', serif"
SERIF = "'Source Serif 4', 'Source Serif Pro', Georgia, 'Times New Roman', serif"
# Georgia has no precomposed Vietnamese glyphs, so Vietnamese text skips it.
DISPLAY_VI = "'Playfair Display', 'Noto Serif Display', 'Noto Serif', 'Times New Roman', Times, serif"
SERIF_VI = "'Source Serif 4', 'Noto Serif', 'Times New Roman', Times, serif"
MONO = "'JetBrains Mono', ui-monospace, 'Cascadia Mono', Consolas, Menlo, monospace"
SANS = "Inter, 'Helvetica Neue', Arial, sans-serif"
VI_TEXT = re.compile(r"[À-ɏḀ-ỿ]")

# App tokens (frontend/src/styles.css), oklch converted to the sRGB hex the browser renders.
# light: newsprint oklch(.973 .005 90) · ink oklch(.145 0 0) · red oklch(.52 .22 27) · divider oklch(.91 .003 90)
LIGHT = {
    "pp": "#F7F6F2",  # newsprint (page)
    "ik": "#0A0A0A",  # ink
    "rd": "#C9000C",  # editorial red
    "mu": "#555555",  # muted foreground
    "tp": "#FEFDFB",  # block top face (hero surface)
    "fl": "#E2E1DF",  # block left face (divider)
    "fr": "#C9C7C1",  # block right face
    "on": "#F7F6F2",  # text on red / ink
}


def _vars(tokens: dict[str, str]) -> str:
    return ";".join(f"--{k}:{v}" for k, v in tokens.items())


CSS = (
    f":root{{{_vars(LIGHT)}}}"
    f".d{{font-family:{DISPLAY}}}.dv{{font-family:{DISPLAY_VI}}}.s{{font-family:{SERIF}}}"
    f".sv{{font-family:{SERIF_VI}}}.m{{font-family:{MONO}}}.u{{font-family:{SANS}}}"
    ".k{letter-spacing:.12em}"
    ".i{fill:var(--ik)}.p{fill:var(--pp)}.r{fill:var(--rd)}.q{fill:var(--mu)}"
    ".t{fill:var(--tp)}.L{fill:var(--fl)}.R{fill:var(--fr)}.o{fill:var(--on)}"
    ".e{stroke:var(--ik);stroke-width:1.3;stroke-linejoin:round}"
    ".h{paint-order:stroke;stroke:var(--pp);stroke-width:5px;stroke-linejoin:round}"
    ".ln{fill:none;stroke:var(--ik)}"
    ".sh{fill:var(--ik);fill-opacity:.18}"
    ".tk{fill:none;stroke:var(--ik);stroke-opacity:.42;stroke-width:1.3}"
    ".dt{fill:none;stroke:var(--ik);stroke-opacity:.6;stroke-width:1.3;stroke-dasharray:2 5;stroke-linecap:round}"
    ".fw{fill:none;stroke:var(--rd);stroke-width:2;stroke-dasharray:6 10;animation:fw 1.4s linear infinite}"
    "@keyframes fw{to{stroke-dashoffset:-32}}"
    ".pl{fill:none;stroke:var(--rd);stroke-width:1.6;transform-box:fill-box;transform-origin:center;"
    "animation:pl 2.8s ease-out infinite}"
    "@keyframes pl{0%{opacity:.9;transform:scale(1)}100%{opacity:0;transform:scale(1.35)}}"
    "@media (prefers-reduced-motion:reduce){.fw,.pl{animation:none}.pl{opacity:.5}.pk{display:none}}"
)


def pts(*points: tuple[float, float]) -> str:
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def mono_w(s: str, size: float = 14, spaced: bool = False) -> float:
    """Approximate rendered width of monospace text (JetBrains Mono / Consolas fallbacks)."""
    return len(s) * size * (0.6 + (0.12 if spaced else 0))


def cols(n: int, x0: float = GUTTER, x1: float = W - M) -> list[float]:
    """Centres of ``n`` equal columns between x0 and x1."""
    step = (x1 - x0) / n
    return [x0 + step * (i + 0.5) for i in range(n)]


@dataclass(frozen=True)
class Box:
    """Geometry of an isometric block: (x, cy) is the centre of its top face."""

    x: float
    cy: float
    hw: float
    bh: float

    @property
    def hh(self) -> float:
        return self.hw * ISO

    @property
    def top(self) -> tuple[float, float]:
        return self.x, self.cy - self.hh

    @property
    def bottom(self) -> tuple[float, float]:
        return self.x, self.cy + self.hh + self.bh

    @property
    def left(self) -> tuple[float, float]:
        return self.x - self.hw, self.cy + self.bh / 2

    @property
    def right(self) -> tuple[float, float]:
        return self.x + self.hw, self.cy + self.bh / 2


class Diagram:
    """Collects SVG fragments in z-ordered layers and writes the final file.

    Every figure shares the same newspaper furniture: masthead line (desk + FIG. number), red
    kicker tag with the source reference, Playfair headline, italic deck, thick+thin double rule,
    and an optional ink ticker band along the bottom edge.
    """

    LAYERS = ("bg", "lanes", "edges", "blocks", "packets", "labels")

    def __init__(
        self,
        name: str,
        height: int,
        *,
        title: str,
        deck: str,
        desk: str,
        fig: str,
        kicker: str,
        source: str = "",
        ticker: tuple[str, ...] = (),
        aria: str = "",
    ) -> None:
        self.name, self.w, self.h = name, W, height
        self.aria = aria or f"{title}. {deck}"
        self.defs: list[str] = []
        self.layers: dict[str, list[str]] = {k: [] for k in self.LAYERS}
        self._header(title, deck, desk, fig, kicker, source)
        if ticker:
            self._ticker(ticker)

    # ---- primitives ---------------------------------------------------------
    def add(self, layer: str, fragment: str) -> None:
        self.layers[layer].append(fragment)

    def text(
        self, x, y, s, *, size=14, cls="u i", anchor="start", weight=None, italic=False, halo=False, layer="labels"
    ) -> None:
        if VI_TEXT.search(s):  # Georgia / Consolas lack precomposed Vietnamese glyphs
            cls = " ".join({"s": "sv", "d": "dv", "m": "u"}.get(c, c) for c in cls.split())
        attrs = f'x="{x:.1f}" y="{y:.1f}" class="{cls}{" h" if halo else ""}" font-size="{size}"'
        if anchor != "start":
            attrs += f' text-anchor="{anchor}"'
        if weight:
            attrs += f' font-weight="{weight}"'
        if italic:
            attrs += ' font-style="italic"'
        self.add(layer, f"<text {attrs}>{escape(s)}</text>")

    def line(self, x1, y1, x2, y2, *, width=1.0, opacity=None, layer="bg") -> None:
        extra = f' stroke-opacity="{opacity}"' if opacity is not None else ""
        self.add(
            layer,
            f'<path d="M {x1:.1f} {y1:.1f} L {x2:.1f} {y2:.1f}" class="ln" stroke-width="{width}"{extra}/>',
        )

    def tag(self, x, y, label, *, red=True, layer="bg", h=26) -> float:
        """Solid tag label (the site's red "BREAKING" box). Returns its width."""
        w = mono_w(label, 14, spaced=True) + 18
        self.add(layer, f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" class="{"r" if red else "i"}"/>')
        self.text(x + 10, y + h / 2 + 5, label, cls="m k o", weight=700, layer=layer)
        return w

    def _header(self, title, deck, desk, fig, kicker, source) -> None:
        w, h = self.w, self.h
        self.defs += [
            '<pattern id="dots" width="4" height="4" patternUnits="userSpaceOnUse">'
            '<path d="M1 3h1v1H1zM3 1h1v1H3z" class="i" fill-opacity=".05"/></pattern>',
            '<pattern id="hatch" width="4" height="4" patternUnits="userSpaceOnUse">'
            '<path d="M1 0V4" class="ln" stroke-width=".8" stroke-opacity=".26"/></pattern>',
            '<marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" '
            'markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0,1 L10,5 L0,9 z" class="i"/></marker>',
        ]
        self.add(
            "bg",
            f'<rect width="{w}" height="{h}" class="p"/><rect width="{w}" height="{h}" fill="url(#dots)"/>'
            f'<rect x=".75" y=".75" width="{w - 1.5}" height="{h - 1.5}" class="ln" stroke-width="1.5"/>',
        )
        self.text(M, 38, f"{BRAND} · {desk}", cls="m k i", weight=700, layer="bg")
        self.text(w - M, 38, f"FIG. {fig}", cls="m k r", weight=700, anchor="end", layer="bg")
        self.line(M, 50, w - M, 50)
        tw = self.tag(M, 66, kicker)
        if source:
            self.text(M + tw + 14, 84, source, cls="m q", layer="bg")
        self.text(M, 140, title, size=42, cls="d i", weight=700, layer="bg")
        self.text(M, 172, deck, size=18, cls="s q", italic=True, layer="bg")
        self.add("bg", f'<rect x="{M}" y="188" width="{w - 2 * M}" height="3" class="i"/>')
        self.line(M, 196, w - M, 196)

    def _ticker(self, items: tuple[str, ...]) -> None:
        y0 = self.h - 40
        self.add("bg", f'<rect x="0" y="{y0}" width="{self.w}" height="40" class="i"/>')
        x = M
        for i, item in enumerate(items):
            if i:
                self.add("bg", f'<path d="M {x + 2:.1f} {y0 + 14} l 6 6 l -6 6 l -6 -6 z" class="r"/>')
                x += 20
            self.text(x, y0 + 25, item, cls="m k o", weight=700, layer="bg")
            x += mono_w(item, 14, spaced=True) + 10

    # ---- building blocks ----------------------------------------------------
    def lane(self, top, bottom, number, name, caption="", *, tint=False, x0=M, x1=None) -> None:
        """Newspaper section band: rule on top, red number, mono name, italic caption."""
        x1 = self.w - M if x1 is None else x1
        if tint:
            self.add(
                "lanes",
                f'<rect x="{x0}" y="{top}" width="{x1 - x0}" height="{bottom - top}" class="i" fill-opacity=".035"/>',
            )
        self.line(x0, top, x1, top, width=1.3, layer="lanes")
        self.text(x0 + 10, top + 23, number, cls="m r", weight=700, layer="lanes")
        nx = x0 + 10 + mono_w(number) + 12
        self.text(nx, top + 23, name, cls="m k i", weight=700, layer="lanes")
        if caption:
            cx = nx + mono_w(name, 14, spaced=True) + 8
            self.text(cx, top + 23, f"— {caption}", size=15, cls="s q", italic=True, layer="lanes")

    def glane(self, top, bottom, number, name, *, tint=False) -> None:
        """Lane whose label reads bottom-to-top in the left gutter, so vertical edges never cross it."""
        x1 = self.w - M
        if tint:
            self.add(
                "lanes",
                f'<rect x="{M}" y="{top}" width="{x1 - M}" height="{bottom - top}" class="i" fill-opacity=".035"/>',
            )
        self.line(M, top, x1, top, width=1.3, layer="lanes")
        self.line(M + 32, top + 8, M + 32, bottom - 8, opacity=0.35, layer="lanes")
        self.add(
            "lanes",
            f'<g transform="translate({M + 21} {(top + bottom) / 2:.1f}) rotate(-90)"><text x="0" y="0" '
            f'text-anchor="middle" class="m k i" font-size="14" font-weight="700"><tspan class="r">{number}</tspan> '
            f"{escape(name)}</text></g>",
        )

    def panel(self, x, y, w, h, title, caption=None, *, red=False) -> None:
        self.add("lanes", f'<rect x="{x}" y="{y}" width="{w}" height="{h}" class="ln" stroke-width="1.3"/>')
        tw = self.tag(x, y, title, red=red, layer="lanes", h=24)
        if caption:
            self.text(x + tw + 10, y + 17, caption, size=14, cls="s q", italic=True, layer="lanes")

    def edge(self, d, *, arrow=True, flow=True, dotted=False, label=None, at=None, anchor="middle") -> None:
        marker = ' marker-end="url(#ah)"' if arrow else ""
        if dotted:
            self.add("edges", f'<path d="{d}" class="dt"{marker}/>')
        else:
            self.add("edges", f'<path d="{d}" class="tk"{marker}/>')
            if flow:
                self.add("edges", f'<path d="{d}" class="fw"/>')
        if label and at:
            self.text(*at, label, cls="m q", anchor=anchor, halo=True)

    def drops(self, y, boxes, *, x_from=None, x_to=None, gap=8) -> None:
        """Horizontal bus at ``y`` with an arrow dropping into the top of every box."""
        xs = [b.x for b in boxes]
        x0 = min(xs) if x_from is None else x_from
        x1 = max(xs) if x_to is None else x_to
        self.edge(f"M {x0:.1f} {y:.1f} H {x1:.1f}", arrow=False)
        for b in boxes:
            self.edge(f"M {b.x:.1f} {y:.1f} V {b.top[1] - gap:.1f}", flow=False)

    def link(self, a: Box, b: Box, *, y=None, **kw) -> None:
        """Straight horizontal arrow between two blocks on the same row (either direction)."""
        if b.x > a.x:
            x1, x2 = a.right[0] + 8, b.left[0] - 10
        else:
            x1, x2 = a.left[0] - 8, b.right[0] + 10
        yy = a.right[1] if y is None else y
        if "label" in kw and "at" not in kw:
            kw["at"] = ((x1 + x2) / 2, yy - 11)
        self.edge(f"M {x1:.1f} {yy:.1f} H {x2:.1f}", **kw)

    def packet(self, path, dur, begin=0.0, *, key_points=None, key_times=None, fade=True, size=5.5) -> None:
        motion = f'dur="{dur}s" begin="{begin}s" repeatCount="indefinite" path="{path}"'
        if key_points:
            motion += f' keyPoints="{key_points}" keyTimes="{key_times}" calcMode="linear"'
        anim = f"<animateMotion {motion}/>"
        if fade:
            anim += (
                f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.06;0.92;1" dur="{dur}s" '
                f'begin="{begin}s" repeatCount="indefinite"/>'
            )
        opacity = ' opacity="0"' if fade else ""
        s = size
        self.add("packets", f'<g class="pk"{opacity}><path d="M0,{-s} L{s},0 L0,{s} L{-s},0z" class="r"/>{anim}</g>')

    def terminal(self, x, y, label) -> None:
        """START / END node: solid ink disc with a pulsing red ring."""
        self.add(
            "blocks",
            f'<g class="b"><circle cx="{x}" cy="{y}" r="29" class="sh" transform="translate(3 3)"/>'
            f'<circle class="pl" cx="{x}" cy="{y}" r="29"/><circle cx="{x}" cy="{y}" r="29" class="i"/></g>',
        )
        self.text(x, y + 5, label, cls="m o", weight=700, anchor="middle")

    def block(
        self,
        x,
        cy,
        *,
        hw=26,
        bh=16,
        code=None,
        title=None,
        sub=None,
        sub2=None,
        label="below",
        label_y=None,
        title_size=16,
        mono_title=False,
        number=None,
        key=False,
        cluster=False,
        glyphs=False,
        pulse=False,
        muted=False,
    ) -> Box:
        box = Box(x, cy, hw, bh)
        hh = box.hh
        sil = pts((x - hw, cy), (x, cy - hh), (x + hw, cy), (x + hw, cy + bh), (x, cy + hh + bh), (x - hw, cy + bh))
        g: list[str] = [f'<polygon points="{sil}" class="sh" transform="translate(4 4)"/>']
        if pulse:
            ring = pts((x, cy - hh - 7), (x + hw + 12, cy), (x, cy + hh + 7), (x - hw - 12, cy))
            g.append(f'<polygon class="pl" points="{ring}"/>')
        left = pts((x - hw, cy), (x, cy + hh), (x, cy + hh + bh), (x - hw, cy + bh))
        right = pts((x, cy + hh), (x + hw, cy), (x + hw, cy + bh), (x, cy + hh + bh))
        top = pts((x, cy - hh), (x + hw, cy), (x, cy + hh), (x - hw, cy))
        dash = ' stroke-dasharray="4 3"' if muted else ""
        g.append(f'<polygon points="{left}" class="L e"{dash}/>')
        g.append(f'<polygon points="{right}" class="R e"{dash}/><polygon points="{right}" fill="url(#hatch)"/>')
        g.append(f'<polygon points="{top}" class="{"r" if key else "t"} e"{dash}/>')
        face = "o" if key else "i"
        if number is not None:
            g.append(self._iso_text(x, cy, f"{number:02d}", 30 if hw > 40 else 20, f"m {face}", 0.62))
        if code:
            size = min(14.0, 2.0 * hw / max(len(code), 1))
            g.append(self._iso_text(x, cy, code, round(size, 1), f"m {face}", 0.8))
        if cluster:
            g.extend(self._cluster(box))
        if glyphs:
            g.append(self._iso_text(x - 15, cy - 9, "✓", 24, "u i", 0.9))
            g.append(self._iso_text(x + 15, cy + 9, "✕", 21, "u r", 0.95))
        self.add("blocks", f'<g class="b">{"".join(g)}</g>')

        style = {"size": max(14, title_size - 1.5), "cls": "m i"} if mono_title else {"size": title_size, "cls": "s i"}
        if title and label == "below":
            lines = title.split("\n")
            y = label_y if label_y is not None else box.bottom[1] + 26
            for ln in lines:
                self.text(x, y, ln, **style, weight=700, anchor="middle")
                y += 19
            for s in (sub, sub2):
                if s:
                    self.text(x, y, s, cls="u q", anchor="middle")
                    y += 18
        elif title and label in ("left", "right"):
            lx = x - hw - 18 if label == "left" else x + hw + 18
            anchor = "end" if label == "left" else "start"
            lines = title.split("\n")
            n = len(lines) + (sub is not None) + (sub2 is not None)
            y = (label_y if label_y is not None else cy + bh / 2 + 5) - (n - 1) * 9
            for ln in lines:
                self.text(lx, y, ln, **style, weight=700, anchor=anchor)
                y += 19
            for s in (sub, sub2):
                if s:
                    self.text(lx, y, s, cls="u q", anchor=anchor)
                    y += 18
        return box

    @staticmethod
    def _iso_text(cx, cy, text, size, cls, opacity) -> str:
        return (
            f'<g transform="matrix(.866 .5 -.866 .5 {cx:.1f} {cy:.1f})">'
            f'<text x="0" y="{size * 0.36:.1f}" text-anchor="middle" class="{cls}" font-size="{size}" '
            f'font-weight="700" fill-opacity="{opacity}">{escape(text)}</text></g>'
        )

    @staticmethod
    def _cluster(box: Box) -> list[str]:
        """Six mini cubes on a platform — one per Ario agent."""
        if box.hw >= 80:
            grid, mw, mhgt, lift = [(-48, -48), (-16, -48), (-48, -16), (16, -48), (-48, 16), (-16, -16)], 13, 10, 4
        else:
            grid, mw, mhgt, lift = [(u, v) for u in (-15, 0, 15) for v in (-8, 8)], 7, 6, 3
        cubes = sorted(((0.866 * (u - v), 0.5 * (u + v)) for u, v in grid), key=lambda t: t[1])
        out = []
        for dx, dy in cubes:
            mx, my = box.x + dx, box.cy + dy - lift
            mh = mw * ISO
            for face, cls in (
                (((mx - mw, my), (mx, my + mh), (mx, my + mh + mhgt), (mx - mw, my + mhgt)), "L"),
                (((mx, my + mh), (mx + mw, my), (mx + mw, my + mhgt), (mx, my + mh + mhgt)), "R"),
                (((mx, my - mh), (mx + mw, my), (mx, my + mh), (mx - mw, my)), "t"),
            ):
                out.append(f'<polygon points="{pts(*face)}" class="{cls} e" stroke-width="1"/>')
        return out

    # ---- output -------------------------------------------------------------
    def save(self, out_dir: Path = OUT_DIR) -> Path:
        body = "".join("".join(self.layers[k]) for k in self.LAYERS)
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" '
            f'height="{self.h}" role="img" aria-label="{escape(self.aria)}"><title>{escape(self.aria)}</title>'
            f"<style>{CSS}</style><defs>{''.join(self.defs)}</defs>{body}</svg>\n"
        )
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{self.name}.svg"
        path.write_text(svg, encoding="utf-8", newline="\n")
        return path


def _chip(d: Diagram, x: float, y: float, w: float, label: str, *, h: float = 30, bullet: bool = True) -> None:
    """Newsprint chip with an ink rule and a hard shadow, like the app's cards."""
    d.add(
        "blocks",
        f'<rect x="{x + 3:.1f}" y="{y + 3:.1f}" width="{w:.1f}" height="{h}" class="sh"/>'
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" class="t e"/>',
    )
    tx = x + 12
    if bullet:
        d.add("blocks", f'<rect x="{x + 12:.1f}" y="{y + h / 2 - 3:.1f}" width="6" height="6" class="r"/>')
        tx = x + 26
    d.text(tx, y + h / 2 + 5, label)


def _chip_w(label: str) -> float:
    return len(label) * 7.6 + 24
