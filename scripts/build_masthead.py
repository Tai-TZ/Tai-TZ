"""Build the README masthead (``assets/masthead.svg``) in the Arionear newsprint style, with a tech edge.

The name is set in Playfair Display Black and converted to outlines (fontTools + HarfBuzz), so GitHub shows the
exact face without loading fonts. On load every glyph is inked stroke by stroke and then filled; "Tai" is set in
editorial red. Around it: an isometric LLM chip wired into PCB traces carrying red signal pulses, a server rack
with blinking status LEDs, a self-typing terminal line and a scrolling ticker. Adapted from the Arionear editor's
``scripts/build_banner.py``.

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

W, H, M = 1040, 340, 40
INK, PAPER, RED = "#0A0A0A", "#F7F6F2", "#C9000C"  # Arionear light tokens: ink · newsprint · editorial red
TOP, LEFT_F, RIGHT_F = "#FEFDFB", "#E2E1DF", "#C9C7C1"  # block faces
MONO = "'JetBrains Mono', ui-monospace, 'Cascadia Mono', Consolas, Menlo, monospace"
ISO = 0.5773502691896257  # tan 30°

NAME, RED_FROM = "Nguyen Thanh Tai", len("Nguyen Thanh ")
TAGLINE = "Building LLM agents with LangChain & LangGraph"
COMMAND = '$ tai --focus "llm agents" --stack langchain,langgraph'
LEFT, CENTER, RIGHT = "VOL. I · NO. 01", "HANOI EDITION · 21.03°N 105.85°E", "SOFTWARE / AI ENGINEER"
TICKER = ("LLM AGENTS", "LANGGRAPH", "LANGCHAIN", "PYTHON", "TYPESCRIPT", "PYTORCH", "FASTAPI", "REACT", "HANOI, VN", "ALWAYS LEARNING")


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


def pts(*points: tuple[float, float]) -> str:
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def iso_block(x: float, cy: float, hw: float, bh: float, *, top: str = TOP, shadow: bool = True) -> str:
    """Arionear block: (x, cy) is the centre of the top face; hatched right face; hard offset shadow."""
    hh = hw * ISO
    out = []
    if shadow:
        sil = pts((x - hw, cy), (x, cy - hh), (x + hw, cy), (x + hw, cy + bh), (x, cy + hh + bh), (x - hw, cy + bh))
        out.append(f'<polygon points="{sil}" fill="{INK}" fill-opacity=".18" transform="translate(4 4)"/>')
    left = pts((x - hw, cy), (x, cy + hh), (x, cy + hh + bh), (x - hw, cy + bh))
    right = pts((x, cy + hh), (x + hw, cy), (x + hw, cy + bh), (x, cy + hh + bh))
    face = pts((x, cy - hh), (x + hw, cy), (x, cy + hh), (x - hw, cy))
    stroke = f'stroke="{INK}" stroke-width="1.3" stroke-linejoin="round"'
    out.append(f'<polygon points="{left}" fill="{LEFT_F}" {stroke}/>')
    out.append(f'<polygon points="{right}" fill="{RIGHT_F}" {stroke}/><polygon points="{right}" fill="url(#hatch)"/>')
    out.append(f'<polygon points="{face}" fill="{top}" {stroke}/>')
    return "".join(out)


def iso_text(cx: float, cy: float, text: str, size: float, fill: str) -> str:
    return (
        f'<g transform="matrix(.866 .5 -.866 .5 {cx:.1f} {cy:.1f})"><text x="0" y="{size * 0.36:.1f}" text-anchor="middle" '
        f'font-family="{MONO}" font-size="{size}" font-weight="700" fill="{fill}">{escape(text)}</text></g>'
    )


def pulse(path: str, dur: float, begin: float, size: float = 4.5) -> str:
    return (
        f'<g class="pk" opacity="0"><path d="M0,{-size} L{size},0 L0,{size} L{-size},0z" fill="{RED}"/>'
        f'<animateMotion dur="{dur}s" begin="{begin}s" repeatCount="indefinite" path="{path}"/>'
        f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.08;.9;1" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/></g>'
    )


def chip(cx: float, cy: float) -> tuple[str, list[str]]:
    """Isometric LLM chip: pinned package with a red die. Returns (svg, trace paths leaving its pins)."""
    hw, bh = 58, 9
    hh = hw * ISO
    out = []
    # Pins on the two visible sides (front-left and front-right edges), drawn under the package.
    for k in range(1, 7):
        t = k / 7
        lx, ly = cx - hw + hw * t, cy + hh * t + bh  # along the front-left edge
        rx, ry = cx + hw * t, cy + hh - hh * t + bh  # along the front-right edge
        out.append(f'<path d="M {lx:.1f} {ly:.1f} l -7 4" stroke="{INK}" stroke-width="2.2" stroke-linecap="square"/>')
        out.append(f'<path d="M {rx:.1f} {ry:.1f} l 7 4" stroke="{INK}" stroke-width="2.2" stroke-linecap="square"/>')
    out.append(iso_block(cx, cy, hw, bh))
    out.append(f'<g class="die">{iso_block(cx, cy - 8, 30, 8, top=RED, shadow=False)}{iso_text(cx, cy - 8, "LLM", 13, PAPER)}</g>')
    out.append(f'<circle class="led" cx="{cx + hw - 16:.1f}" cy="{cy + 2:.1f}" r="3" fill="{RED}"/>')
    # Traces from the bottom pins down to the rule and out to the left margin.
    traces = [
        f"M {cx - hw + hw * 2 / 7 - 7:.1f} {cy + hh * 2 / 7 + bh + 4:.1f} l -26 15 V 262 H 20",
        f"M {cx - hw + hw * 5 / 7 - 7:.1f} {cy + hh * 5 / 7 + bh + 4:.1f} V 248 H 18",
        f"M {cx + hw * 3 / 7 + 7:.1f} {cy + hh - hh * 3 / 7 + bh + 4:.1f} l 18 10 V 236 H 196",
    ]
    return "".join(out), traces


def rack(cx: float, top_cy: float) -> tuple[str, list[str]]:
    """Three stacked server units with blinking status LEDs on the front face."""
    hw, bh, gap = 46, 16, 26
    out = []
    for i in reversed(range(3)):  # lowest unit first so upper ones overlap correctly
        cy = top_cy + i * gap
        out.append(iso_block(cx, cy, hw, bh, top=RED if i == 0 else TOP))
        hh = hw * ISO
        for k in range(3):  # LEDs along the front-left face
            t = 0.25 + k * 0.2
            lx, ly = cx - hw + hw * t, cy + hh * t + bh / 2 + 1
            out.append(f'<circle class="blink" style="--d:{(i * 3 + k) * 0.37:.2f}s" cx="{lx:.1f}" cy="{ly:.1f}" r="2.3" fill="{RED if (i + k) % 2 else INK}"/>')
    out.append(iso_text(cx, top_cy, "GPU", 14, PAPER))
    base_y = top_cy + 2 * gap + hw * ISO + bh
    traces = [f"M {cx:.1f} {base_y + 4:.1f} V 248 H 1022", f"M {cx - 30:.1f} {base_y - 10:.1f} V 236 H 844"]
    return "".join(out), traces


def build() -> str:
    black, black_blob = instance(ROMAN, 900)
    italic, italic_blob = instance(ITALIC, 400)

    # Wordmark between the chip and the rack.
    region_x0, region_x1, base, track = 196, 846, 166, -0.03
    runs = shape(black_blob, NAME)
    assert len(runs) == len(NAME), "glyphs must map 1:1 to characters"
    size = 92.0
    total = outline(black, runs, size, 0, 0, track)[1]
    if total > region_x1 - region_x0 - 20:
        size *= (region_x1 - region_x0 - 20) / total
        total = outline(black, runs, size, 0, 0, track)[1]
    x0 = region_x0 + (region_x1 - region_x0 - total) / 2 - 6
    paths, _ = outline(black, runs, size, x0, base, track)
    glyphs = []
    for i, d in enumerate(paths):
        if not d:
            continue
        color = RED if i >= RED_FROM else INK
        glyphs.append(f'<path class="gl" pathLength="1" style="--i:{i}" d="{d}" fill="{color}" stroke="{color}"/>')
    caret_x = x0 + total + 8

    tag_runs = shape(italic_blob, TAGLINE)
    tag_size = 25
    tag_w = outline(italic, tag_runs, tag_size, 0, 0)[1]
    tagline = "".join(outline(italic, tag_runs, tag_size, (region_x0 + region_x1 - tag_w) / 2, 204)[0])

    # Self-typing terminal line (SMIL clip so it loops inside <img>).
    cmd_size = 14
    cmd_w = len(COMMAND) * cmd_size * 0.6 + 4
    cmd_x = (region_x0 + region_x1 - cmd_w) / 2
    cycle = 9.0
    typing = (
        f'<clipPath id="cmd"><rect x="{cmd_x:.1f}" y="216" height="26" width="0">'
        f'<animate attributeName="width" values="0;0;{cmd_w:.1f};{cmd_w:.1f};0" keyTimes="0;.12;.5;.92;1" dur="{cycle}s" repeatCount="indefinite"/></rect></clipPath>'
        f'<rect x="{cmd_x - 12:.1f}" y="217" width="{cmd_w + 34:.1f}" height="26" fill="{INK}"/>'
        f'<text clip-path="url(#cmd)" x="{cmd_x:.1f}" y="235" font-family="{MONO}" font-size="{cmd_size}" fill="{PAPER}" xml:space="preserve">'
        f'<tspan fill="{RED}" font-weight="700">$</tspan>{escape(COMMAND[1:])}</text>'
        f'<rect class="cr" y="221" width="8" height="17" fill="{RED}" x="{cmd_x:.1f}">'
        f'<animate attributeName="x" values="{cmd_x:.1f};{cmd_x:.1f};{cmd_x + cmd_w:.1f};{cmd_x + cmd_w:.1f};{cmd_x:.1f}" keyTimes="0;.12;.5;.92;1" dur="{cycle}s" repeatCount="indefinite"/></rect>'
    )

    chip_svg, chip_traces = chip(108, 132)
    rack_svg, rack_traces = rack(942, 96)
    traces = chip_traces + rack_traces
    trace_svg = "".join(f'<path d="{t}" fill="none" stroke="{INK}" stroke-opacity=".32" stroke-width="1.4"/>' for t in traces)
    vias = "".join(
        f'<circle cx="{x}" cy="{y}" r="3.2" fill="{PAPER}" stroke="{INK}" stroke-opacity=".5" stroke-width="1.3"/>'
        for x, y in ((20, 262), (18, 248), (196, 236), (1022, 248), (844, 236))
    )
    pulses = "".join(pulse(t, 2.6 + i * 0.4, i * 0.7) for i, t in enumerate(traces))

    # Scrolling ticker: two copies side by side, shifted by one copy's width forever.
    char_w = 13 * 0.72
    row, x = [], 0.0
    for item in TICKER:
        row.append(f'<text x="{x:.1f}" y="319" class="m o">{escape(item)}</text>')
        x += len(item) * char_w + 14
        row.append(f'<path d="M {x:.1f} 309 l 5 5 l -5 5 l -5 -5 z" fill="{RED}"/>')
        x += 19
    row_w = x
    ticker = (
        f'<rect x="0" y="{H - 40}" width="{W}" height="40" fill="{INK}"/>'
        f'<clipPath id="tk"><rect x="0" y="{H - 40}" width="{W}" height="40"/></clipPath>'
        f'<g clip-path="url(#tk)"><g class="mq" style="--w:-{row_w:.1f}px">'
        f'<g transform="translate({M} 0)">{"".join(row)}</g><g transform="translate({M + row_w:.1f} 0)">{"".join(row)}</g></g></g>'
    )

    label = f"{NAME}: {TAGLINE}. Software / AI engineer in Hanoi."
    style = (
        f".m{{font-family:{MONO};font-size:13px;font-weight:700;letter-spacing:.12em;fill:{INK};fill-opacity:.78}}"
        f".o{{fill:{PAPER};fill-opacity:1}}"
        ".gl{stroke-width:1.2;fill-opacity:0;stroke-dasharray:1 1;stroke-dashoffset:1;"
        "animation:ink 1.3s cubic-bezier(.55,.1,.3,1) forwards,fill .6s ease forwards;"
        "animation-delay:calc(var(--i) * .07s),calc(.9s + var(--i) * .07s)}"
        "@keyframes ink{to{stroke-dashoffset:0}}@keyframes fill{to{fill-opacity:1;stroke-width:0}}"
        ".cr{animation:cr 1s steps(1) infinite}@keyframes cr{50%{opacity:0}}"
        ".blink{animation:bl 2.2s steps(1) infinite;animation-delay:var(--d)}@keyframes bl{0%{opacity:1}40%{opacity:.15}60%{opacity:1}}"
        ".led{animation:led 1.4s ease-in-out infinite}@keyframes led{50%{opacity:.2}}"
        ".die{animation:die 3.2s ease-in-out infinite}@keyframes die{0%,100%{transform:translateY(0)}50%{transform:translateY(-3px)}}"
        ".tg{opacity:0;animation:tg .8s ease forwards 1.9s}@keyframes tg{from{opacity:0;transform:translateY(6px)}to{opacity:1}}"
        ".mq{animation:mq 38s linear infinite}@keyframes mq{to{transform:translateX(var(--w))}}"
        ".ul{stroke-dasharray:1000;stroke-dashoffset:1000;animation:ul 1.6s cubic-bezier(.2,.7,.2,1) .4s forwards}@keyframes ul{to{stroke-dashoffset:0}}"
        "@media (prefers-reduced-motion:reduce){.gl{animation:none;fill-opacity:1;stroke-width:0}.tg{animation:none;opacity:1}"
        ".ul{animation:none;stroke-dashoffset:0}.cr,.blink,.led,.die,.mq{animation:none}.pk{display:none}}"
    )
    defs = (
        '<defs><pattern id="hatch" width="4" height="4" patternUnits="userSpaceOnUse">'
        f'<path d="M1 0V4" stroke="{INK}" stroke-width=".8" stroke-opacity=".26"/></pattern>'
        '<pattern id="dots" width="4" height="4" patternUnits="userSpaceOnUse">'
        f'<path d="M1 3h1v1H1zM3 1h1v1H3z" fill="{INK}" fill-opacity=".05"/></pattern></defs>'
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title><style>{style}</style>{defs}'
        f'<rect width="{W}" height="{H}" fill="{PAPER}"/><rect width="{W}" height="{H}" fill="url(#dots)"/>'
        f'<text x="{M}" y="38" class="m">{escape(LEFT)}</text>'
        f'<text x="{W / 2}" y="38" class="m" text-anchor="middle">{escape(CENTER)}</text>'
        f'<text x="{W - M}" y="38" class="m" text-anchor="end">{escape(RIGHT)}</text>'
        f'<path d="M {M} 52 H {W - M}" stroke="{INK}" stroke-opacity=".45"/>'
        f"{trace_svg}{vias}{pulses}{chip_svg}{rack_svg}"
        f'{"".join(glyphs)}<rect class="cr" x="{caret_x:.1f}" y="{base - 66:.1f}" width="6" height="74" fill="{RED}"/>'
        f'<g class="tg"><path d="{tagline}" fill="{INK}" fill-opacity=".8"/></g>{typing}'
        f'<rect x="{M}" y="270" width="{W - 2 * M}" height="3" fill="{INK}"/>'
        f'<path class="ul" d="M {M} 277.5 H {W - M}" stroke="{RED}" stroke-width="1.5"/>'
        f'<path d="M {M} 284.5 H {W - M}" stroke="{INK}" stroke-opacity=".7"/>{ticker}'
        f'<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" fill="none" stroke="{INK}" stroke-width="1.5"/></svg>\n'
    )


def main() -> int:
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(build(), encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1024:.1f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
