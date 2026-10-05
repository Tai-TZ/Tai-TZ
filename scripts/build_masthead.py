"""Build the README masthead (``assets/masthead.svg``) in the Arionear newsprint style.

The name is set in Playfair Display Black and converted to outlines (fontTools + HarfBuzz), so GitHub shows
the exact face without loading fonts: "Nguyen Thanh" in ink, "Tai" in editorial red, followed by a
blinking editor caret. Adapted from the Arionear editor's ``scripts/build_banner.py``.

    pip install fonttools uharfbuzz
    python scripts/build_masthead.py

Playfair Display (SIL Open Font License 1.1) is downloaded once from github.com/google/fonts into ``.cache/fonts/``.
"""

from __future__ import annotations

import urllib.request
from html import escape
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "masthead.svg"
CACHE = ROOT / ".cache" / "fonts"
FONT_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/playfairdisplay/{}"
ROMAN, ITALIC = "PlayfairDisplay[wght].ttf", "PlayfairDisplay-Italic[wght].ttf"

W, H, M = 1040, 300, 40
INK, PAPER, RED = "#0A0A0A", "#F7F6F2", "#C9000C"  # Arionear light tokens: ink · newsprint · editorial red
MONO = "'JetBrains Mono', ui-monospace, 'Cascadia Mono', Consolas, Menlo, monospace"

NAME, RED_FROM = "Nguyen Thanh Tai", len("Nguyen Thanh ")
TAGLINE = "Building LLM agents with LangChain & LangGraph"
LEFT, RIGHT = "VOL. I · NO. 01", "SOFTWARE / AI ENGINEER · HANOI"
TICKER = ("LLM AGENTS", "LANGGRAPH", "PYTHON", "TYPESCRIPT", "HANOI, VN")


def font_path(name: str) -> Path:
    path = CACHE / name
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        url = FONT_URL.format(name.replace("[", "%5B").replace("]", "%5D"))
        with urllib.request.urlopen(url, timeout=60) as resp:  # noqa: S310 — fixed https URL
            path.write_bytes(resp.read())
    return path


def instance(name: str, weight: int) -> tuple[TTFont, bytes]:
    font = instantiateVariableFont(TTFont(font_path(name)), {"wght": weight})
    tmp = CACHE / f"{Path(name).stem}-{weight}.ttf"
    font.save(tmp)
    return TTFont(tmp), tmp.read_bytes()


def shape(blob: bytes, text: str) -> list[tuple[str, int, int]]:
    """HarfBuzz-shaped glyph runs. Ligatures off so glyph i is character i (the colour split relies on it)."""
    face = hb.Face(blob)
    font = hb.Font(face)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": False, "dlig": False})
    names = [font.glyph_to_string(info.codepoint) for info in buf.glyph_infos]
    return [(n, pos.x_advance, pos.x_offset) for n, pos in zip(names, buf.glyph_positions, strict=True)]


def outline(font: TTFont, runs, size: float, x: float, baseline: float, tracking_em: float = 0.0) -> tuple[list[str], float]:
    glyphs = font.getGlyphSet()
    scale = size / font["head"].unitsPerEm
    paths, pen_x = [], x
    for name, advance, offset in runs:
        pen = SVGPathPen(glyphs)
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, pen_x + offset * scale, baseline)))
        paths.append(pen.getCommands())
        pen_x += advance * scale + tracking_em * size
    return paths, pen_x - x


def build() -> str:
    black, black_blob = instance(ROMAN, 900)
    italic, italic_blob = instance(ITALIC, 400)

    size, track, base = 104, -0.03, 180
    runs = shape(black_blob, NAME)
    assert len(runs) == len(NAME), "glyphs must map 1:1 to characters"
    total = outline(black, runs, size, 0, 0, track)[1]
    x0 = (W - total) / 2 - 8  # leave room for the caret on the right
    paths, _ = outline(black, runs, size, x0, base, track)
    ink, red = "".join(paths[:RED_FROM]), "".join(paths[RED_FROM:])
    caret_x = x0 + total + 10

    tag_runs = shape(italic_blob, TAGLINE)
    tag_size = 28
    tag_w = outline(italic, tag_runs, tag_size, 0, 0)[1]
    tagline = "".join(outline(italic, tag_runs, tag_size, (W - tag_w) / 2, 230)[0])

    char_w = 13 * 0.72  # mono 13px + .12em tracking
    widths = [len(t) * char_w for t in TICKER]
    tx = (W - (sum(widths) + 26 * (len(TICKER) - 1))) / 2
    tick = []
    for i, (item, width) in enumerate(zip(TICKER, widths, strict=True)):
        if i:
            tick.append(f'<path class="tk" style="--i:{i}" d="M {tx - 13:.1f} 277 l 5 5 l -5 5 l -5 -5 z" fill="{RED}"/>')
        tick.append(f'<text x="{tx:.1f}" y="287" class="m">{escape(item)}</text>')
        tx += width + 26

    label = f"{NAME}: {TAGLINE}. Software / AI engineer in Hanoi."
    style = (
        f".m{{font-family:{MONO};font-size:13px;font-weight:700;letter-spacing:.12em;fill:{INK};fill-opacity:.78}}"
        ".cr{animation:cr 1.1s steps(1) infinite}@keyframes cr{50%{opacity:0}}"
        ".tk{animation:tk 3s ease-in-out infinite;animation-delay:calc(var(--i) * .35s)}@keyframes tk{0%,30%,100%{opacity:1}15%{opacity:.25}}"
        ".ul{stroke-dasharray:1000;stroke-dashoffset:1000;animation:ul 1.6s cubic-bezier(.2,.7,.2,1) .3s forwards}@keyframes ul{to{stroke-dashoffset:0}}"
        "@media (prefers-reduced-motion:reduce){.cr,.tk{animation:none}.ul{animation:none;stroke-dashoffset:0}.pk{display:none}}"
    )
    packet = (
        f'<g class="pk"><path d="M0,-5 L5,0 L0,5 L-5,0z" fill="{RED}"/>'
        f'<animateMotion dur="7s" repeatCount="indefinite" path="M {M} 263.5 H {W - M}"/></g>'
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title><style>{style}</style>'
        f'<rect width="{W}" height="{H}" fill="{PAPER}"/>'
        f'<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" fill="none" stroke="{INK}" stroke-width="1.5"/>'
        f'<text x="{M}" y="38" class="m">{escape(LEFT)}</text>'
        f'<text x="{W - M}" y="38" class="m" text-anchor="end">{escape(RIGHT)}</text>'
        f'<path d="M {M} 52 H {W - M}" stroke="{INK}" stroke-opacity=".45"/>'
        f'<path d="{ink}" fill="{INK}"/><path d="{red}" fill="{RED}"/>'
        f'<rect class="cr" x="{caret_x:.1f}" y="{base - 76}" width="7" height="86" fill="{RED}"/>'
        f'<path d="{tagline}" fill="{INK}" fill-opacity=".8"/>'
        f'<rect x="{M}" y="248" width="{W - 2 * M}" height="3" fill="{INK}"/>'
        f'<path class="ul" d="M {M} 255.5 H {W - M}" stroke="{RED}" stroke-width="1.5"/>'
        f'<path d="M {M} 263.5 H {W - M}" stroke="{INK}" stroke-opacity=".7"/>{packet}'
        f"{''.join(tick)}</svg>\n"
    )


def main() -> int:
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(build(), encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1024:.1f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
