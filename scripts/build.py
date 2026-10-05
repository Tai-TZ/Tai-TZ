"""Build the static animated SVGs for the profile README.

    python scripts/build.py        # writes assets/*.svg

Everything is plain SVG + CSS/SMIL animation (no JavaScript), so it renders inside GitHub's <img>.
"""

import random
from pathlib import Path

from common import ACCENT, BORDER, DIM, FACES, INK, MONO, MUTED, PANEL, SANS, box, esc, frame, iso, pts, svg, top_matrix

OUT = Path(__file__).resolve().parent.parent / "assets"


# ---------------------------------------------------------------------------------------------------------------------
# Hero: name, typed roles, neon floor and a floating isometric agent graph
# ---------------------------------------------------------------------------------------------------------------------

ROLES = ["Software / AI Engineer", "building LLM agents", "LangChain + LangGraph", "always learning"]


def typed_roles(x0: float, y: float, size: int) -> str:
    """Cycle through ROLES with a type / hold / delete rhythm (SMIL, so it loops forever inside <img>)."""
    char_w, slot, cycle = size * 0.61, 3.2, 3.2 * len(ROLES)
    parts, cursor_times, cursor_values = [], [0.0], [x0]
    for k, role in enumerate(ROLES):
        width = len(role) * char_w + 4
        start = k * slot / cycle
        typed, held, deleted = start + 1.0 / cycle, start + 2.5 / cycle, start + 3.0 / cycle
        times = [0.0, start, typed, held, deleted, 1.0]
        widths = [0, 0, width, width, 0, 0]
        if start == 0:
            times, widths = times[1:], widths[1:]
        kt = ";".join(f"{t:.4f}" for t in times)
        parts.append(
            f'<clipPath id="role{k}"><rect x="{x0}" y="{y - size}" height="{size * 1.4}" width="0">'
            f'<animate attributeName="width" values="{";".join(f"{w:.1f}" for w in widths)}" keyTimes="{kt}" dur="{cycle}s" repeatCount="indefinite"/>'
            f"</rect></clipPath>"
            f'<text clip-path="url(#role{k})" x="{x0}" y="{y}" font-family="{MONO}" font-size="{size}" fill="{INK}" xml:space="preserve">{esc(role)}</text>'
        )
        cursor_times += [start, typed, held, deleted]
        cursor_values += [x0, x0 + width, x0 + width, x0]
    cursor_times.append(1.0)
    cursor_values.append(x0)
    pairs = sorted(set(zip(cursor_times, cursor_values, strict=True)))
    kt = ";".join(f"{t:.4f}" for t, _ in pairs)
    vals = ";".join(f"{v:.1f}" for _, v in pairs)
    parts.append(
        f'<rect class="blink" y="{y - size * 0.82}" width="{size * 0.5:.1f}" height="{size:.1f}" rx="2" fill="{ACCENT["cyan"]}" x="{x0}">'
        f'<animate attributeName="x" values="{vals}" keyTimes="{kt}" dur="{cycle}s" repeatCount="indefinite"/></rect>'
    )
    return "".join(parts)


def chip(x: float, y: float, label: str, color: str) -> tuple[str, float]:
    width = len(label) * 7.7 + 34
    return (
        f'<g><rect x="{x}" y="{y}" width="{width:.0f}" height="30" rx="15" fill="{PANEL}" stroke="{color}" stroke-opacity="0.55"/>'
        f'<circle cx="{x + 15}" cy="{y + 15}" r="4" fill="{color}" class="pulse"/>'
        f'<text x="{x + 26}" y="{y + 20}" font-family="{SANS}" font-size="13.5" font-weight="600" fill="{INK}">{esc(label)}</text></g>',
        width,
    )


def neon_floor(width: int, height: int, horizon: float, vx: float) -> str:
    depth = height - horizon
    lines = []
    for k in range(-14, 27):  # rays from the vanishing point
        bx = vx + k * 110 - 650
        lines.append(f'<line x1="{vx}" y1="{horizon}" x2="{bx}" y2="{height}"/>')
    rows = 9
    for i in range(rows):
        y_now = horizon + depth * (i / rows) ** 2
        y_next = horizon + depth * ((i + 1) / rows) ** 2
        lines.append(f'<line class="row" style="--dy:{y_next - y_now:.1f}px" x1="0" y1="{y_now:.1f}" x2="{width}" y2="{y_now:.1f}"/>')
    return (
        '<defs><linearGradient id="floor-fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        '<stop offset="1" stop-color="#fff" stop-opacity="1"/></linearGradient>'
        f'<mask id="floor-mask"><rect x="0" y="{horizon}" width="{width}" height="{depth}" fill="url(#floor-fade)"/></mask>'
        f'<clipPath id="floor-clip"><rect x="1" y="{horizon}" width="{width - 2}" height="{depth - 1}" rx="19"/></clipPath></defs>'
        f'<g clip-path="url(#floor-clip)" mask="url(#floor-mask)" stroke="{ACCENT["violet"]}" stroke-opacity="0.55" stroke-width="1">{"".join(lines)}</g>'
        f'<line x1="20" y1="{horizon}" x2="{width - 20}" y2="{horizon}" stroke="{ACCENT["pink"]}" stroke-opacity="0.45"/>'
    )


def stars(width: int, top: float, bottom: float, n: int) -> str:
    rng = random.Random(7)
    out = []
    for _ in range(n):
        x, y = rng.uniform(20, width - 20), rng.uniform(top, bottom)
        r = rng.choice([0.8, 1.0, 1.2, 1.6])
        out.append(f'<circle class="twinkle" style="--d:{rng.uniform(0, 4):.2f}s;--t:{rng.uniform(2.5, 5):.2f}s" cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="#fff"/>')
    return "".join(out)


def agent_graph(ox: float, oy: float) -> str:
    """Isometric LangGraph-style scene: an LLM core wired to tools, memory, planner and retriever."""
    deck_z, parts = 14.0, []
    parts.append(f'<ellipse cx="{ox}" cy="{oy + 40}" rx="300" ry="70" fill="{ACCENT["violet"]}" opacity="0.18" filter="url(#blur-xl)"/>')
    parts.append(box(-160, -160, 0, 320, 320, deck_z, FACES["deck"], ox, oy))
    # Grid etched on the deck.
    for k in range(-120, 161, 40):
        a, b = iso(k, -160, deck_z, ox, oy), iso(k, 160, deck_z, ox, oy)
        c, d = iso(-160, k, deck_z, ox, oy), iso(160, k, deck_z, ox, oy)
        parts.append(f'<path d="M{a[0]:.1f},{a[1]:.1f}L{b[0]:.1f},{b[1]:.1f}M{c[0]:.1f},{c[1]:.1f}L{d[0]:.1f},{d[1]:.1f}" stroke="{BORDER}" stroke-width="1"/>')
    edge = iso(160, -160, deck_z, ox, oy), iso(160, 160, deck_z, ox, oy), iso(-160, 160, deck_z, ox, oy)
    parts.append(f'<polyline points="{pts(list(edge))}" fill="none" stroke="{ACCENT["cyan"]}" stroke-opacity="0.5" stroke-width="1.2"/>')

    nodes = [  # (cx, cy, size, height, color, label)
        (0, -118, 50, 42, "cyan", "tools"),
        (-118, 0, 50, 42, "amber", "memory"),
        (118, 0, 50, 42, "pink", "planner"),
        (0, 118, 50, 42, "lime", "retriever"),
    ]
    center = iso(0, 0, deck_z, ox, oy)
    for i, (cx, cy, *_rest, color, _label) in enumerate(nodes):
        tx, ty = iso(cx, cy, deck_z, ox, oy)
        path = f"M{center[0]:.1f},{center[1]:.1f} L{tx:.1f},{ty:.1f}" if i % 2 == 0 else f"M{tx:.1f},{ty:.1f} L{center[0]:.1f},{center[1]:.1f}"
        parts.append(f'<path class="dash" d="{path}" stroke="{ACCENT[color]}" stroke-width="2" stroke-opacity="0.8" fill="none"/>')
        for j in range(2):
            parts.append(
                f'<circle class="packet" r="4" fill="{ACCENT[color]}" stroke="#fff" stroke-width="1.2" '
                f"style=\"offset-path:path('{path}');--dur:2.4s;--delay:{i * 0.35 + j * 1.2:.2f}s\"/>"
            )

    def node(cx: float, cy: float, size: float, height: float, color: str, label: str, delay: float) -> str:
        x, y = cx - size / 2, cy - size / 2
        lx, ly = iso(cx, cy, deck_z + height, ox, oy)
        return (
            f'<g class="float" style="--delay:{delay}s">{box(x, y, deck_z, size, size, height, FACES[color], ox, oy)}'
            f'<line x1="{lx:.1f}" y1="{ly - 6:.1f}" x2="{lx:.1f}" y2="{ly - 26:.1f}" stroke="{ACCENT[color]}" stroke-opacity="0.6"/>'
            f'<rect x="{lx - len(label) * 4.4 - 9:.1f}" y="{ly - 48:.1f}" width="{len(label) * 8.8 + 18:.1f}" height="22" rx="6" fill="{PANEL}" stroke="{ACCENT[color]}" stroke-opacity="0.7"/>'
            f'<text x="{lx:.1f}" y="{ly - 33:.1f}" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{INK}">{label}</text></g>'
        )

    back = [n for n in nodes if n[0] + n[1] < 0]
    front = [n for n in nodes if n[0] + n[1] >= 0]
    for i, n in enumerate(back):
        parts.append(node(*n, delay=i * 0.7))
    # LLM core: a tall glowing block with the label printed on its top face.
    size, height = 78, 96
    gx, gy = iso(0, 0, deck_z + height / 2, ox, oy)
    parts.append(f'<circle class="pulse" cx="{gx:.1f}" cy="{gy:.1f}" r="78" fill="{ACCENT["violet"]}" opacity="0.35" filter="url(#blur-lg)"/>')
    parts.append(
        f'<g class="float" style="--delay:0.3s">{box(-size / 2, -size / 2, deck_z, size, size, height, FACES["violet"], ox, oy)}'
        f'<text transform="{top_matrix(0, 0, deck_z + height, ox, oy)}" x="0" y="8" text-anchor="middle" font-family="{MONO}" font-size="24" font-weight="800" fill="#2e1065">LLM</text></g>'
    )
    for i, n in enumerate(front):
        parts.append(node(*n, delay=1.2 + i * 0.7))

    # Orbit ring with a satellite token.
    r, oz = 205, 70
    ex, ey = iso(0, 0, deck_z + oz, ox, oy)
    rx, ry = r * 1.2247, r * 0.7071
    ring = f"M{ex - rx:.1f},{ey:.1f} a{rx:.1f},{ry:.1f} 0 1,0 {2 * rx:.1f},0 a{rx:.1f},{ry:.1f} 0 1,0 {-2 * rx:.1f},0"
    parts.append(f'<path d="{ring}" fill="none" stroke="{ACCENT["cyan"]}" stroke-opacity="0.35" stroke-dasharray="2 7"/>')
    parts.append(
        f'<circle class="packet" r="6" fill="{ACCENT["cyan"]}" style="offset-path:path(\'{ring}\');--dur:9s;--delay:0s" filter="url(#blur-sm)"/>'
        f'<circle class="packet" r="3.5" fill="#fff" style="offset-path:path(\'{ring}\');--dur:9s;--delay:0s"/>'
    )
    return "".join(parts)


def hero() -> str:
    w, h = 1200, 470
    style = (
        ".twinkle{animation:twinkle var(--t) ease-in-out infinite;animation-delay:var(--d)}"
        "@keyframes twinkle{0%,100%{opacity:.15}50%{opacity:.9}}"
        ".row{animation:row 1.6s linear infinite}"
        "@keyframes row{to{transform:translateY(var(--dy))}}"
        ".float{animation:float 6s ease-in-out infinite;animation-delay:var(--delay,0s)}"
        "@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-7px)}}"
        ".packet{offset-rotate:0deg;animation:travel var(--dur) linear infinite;animation-delay:var(--delay)}"
        "@keyframes travel{from{offset-distance:0%;opacity:0}10%{opacity:1}90%{opacity:1}to{offset-distance:100%;opacity:0}}"
        ".dash{stroke-dasharray:5 6;animation:dash 1s linear infinite}"
        "@keyframes dash{to{stroke-dashoffset:-11}}"
        ".pulse{animation:pulse 2.6s ease-in-out infinite;transform-box:fill-box;transform-origin:center}"
        "@keyframes pulse{0%,100%{opacity:.45}50%{opacity:1}}"
        ".blink{animation:blink 1s steps(1) infinite}"
        "@keyframes blink{50%{opacity:0}}"
        ".rise{animation:rise .9s cubic-bezier(.2,.7,.2,1) both;animation-delay:var(--delay,0s)}"
        "@keyframes rise{from{opacity:0;transform:translateY(14px)}}"
    )
    defs = (
        "<defs>"
        '<filter id="blur-sm" x="-1" y="-1" width="3" height="3"><feGaussianBlur stdDeviation="3"/></filter>'
        '<filter id="blur-lg" x="-1" y="-1" width="3" height="3"><feGaussianBlur stdDeviation="22"/></filter>'
        '<filter id="blur-xl" x="-1" y="-1" width="3" height="3"><feGaussianBlur stdDeviation="30"/></filter>'
        '<linearGradient id="name-grad" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="640" y2="0" spreadMethod="repeat">'
        f'<stop offset="0" stop-color="{ACCENT["cyan"]}"/><stop offset="0.33" stop-color="{ACCENT["violet"]}"/>'
        f'<stop offset="0.66" stop-color="{ACCENT["pink"]}"/><stop offset="1" stop-color="{ACCENT["cyan"]}"/>'
        '<animateTransform attributeName="gradientTransform" type="translate" from="0 0" to="640 0" dur="7s" repeatCount="indefinite"/></linearGradient>'
        "</defs>"
    )
    body = [frame(w, h, "hero"), defs, stars(w, 20, 330, 70), neon_floor(w, h, 360, 870)]
    body.append(
        f'<g class="rise" style="--delay:.1s"><text x="64" y="104" font-family="{MONO}" font-size="16" fill="{MUTED}">'
        f'<tspan fill="{ACCENT["lime"]}">tai@hanoi</tspan>:<tspan fill="{ACCENT["cyan"]}">~</tspan>$ ./introduce --verbose</text></g>'
        f'<g class="rise" style="--delay:.3s"><text x="64" y="160" font-family="{SANS}" font-size="30" font-weight="600" fill="{INK}">Hi, I\'m</text>'
        f'<text x="62" y="226" font-family="{SANS}" font-size="64" font-weight="800" letter-spacing="-1.5" fill="url(#name-grad)">Nguyen Thanh Tai</text></g>'
        f'<text x="64" y="282" font-family="{MONO}" font-size="24" fill="{ACCENT["pink"]}">&gt;</text>'
    )
    body.append(typed_roles(92, 282, 24))
    x = 64.0
    chips = []
    for label, color in (("Hanoi, Vietnam", "pink"), ("LLM agents", "violet"), ("LangGraph", "cyan"), ("Python · TypeScript", "lime")):
        c, cw = chip(x, 310, label, ACCENT[color])
        chips.append(c)
        x += cw + 10
    body.append(f'<g class="rise" style="--delay:.6s">{"".join(chips)}</g>')
    body.append(agent_graph(888, 238))
    return svg(w, h, "Nguyen Thanh Tai", "Software and AI engineer in Hanoi building LLM agents with LangChain and LangGraph. An isometric agent graph floats on a neon grid.", style, "".join(body))


# ---------------------------------------------------------------------------------------------------------------------
# Agent trace: "about me" streamed like a LangGraph run, with the graph lighting up node by node
# ---------------------------------------------------------------------------------------------------------------------

TRACE = [  # (kind, name, value, latency, color)
    ("start", "START", "", "", "violet"),
    ("node", "whoami", "Nguyen Thanh Tai · Software / AI Engineer", "38ms", "cyan"),
    ("node", "locate", "Hanoi, Vietnam · UTC+7", "12ms", "pink"),
    ("node", "focus", "LLM agents with LangChain & LangGraph", "64ms", "violet"),
    ("tool", "stack", "Python · TypeScript · PyTorch · FastAPI · React", "91ms", "amber"),
    ("node", "habits", "editor=VS Code · theme=Tokyo Night · shell=zsh", "17ms", "lime"),
    ("node", "runtime", "uptime=always learning · fuel=coffee ∞", "23ms", "cyan"),
    ("end", "END", '{"problem_solver": true, "learning": "always"}', "", "lime"),
]


def trace() -> str:
    w, h = 1200, 470
    cycle, step, first = 17.0, 1.15, 0.9
    style = (
        f".ln{{opacity:0;animation:ln {cycle}s ease-out infinite both;animation-delay:var(--d)}}"
        "@keyframes ln{0%{opacity:0;transform:translateX(-10px)}3%{opacity:1;transform:none}86%{opacity:1}92%,100%{opacity:0}}"
        f".lit{{animation:lit {cycle}s ease-out infinite both;animation-delay:var(--d)}}"
        "@keyframes lit{0%{fill-opacity:.08;stroke-opacity:.35}3%{fill-opacity:.95;stroke-opacity:1}86%{fill-opacity:.95;stroke-opacity:1}92%,100%{fill-opacity:.08;stroke-opacity:.35}}"
        ".blink{animation:blink 1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
        ".flow{stroke-dasharray:4 5;animation:flow .9s linear infinite}@keyframes flow{to{stroke-dashoffset:-9}}"
        ".live{animation:live 1.6s ease-in-out infinite}@keyframes live{50%{opacity:.25}}"
    )
    body = [frame(w, h, "trace")]
    # Window chrome.
    body.append(f'<line x1="0" y1="52" x2="{w}" y2="52" stroke="{BORDER}"/>')
    for i, c in enumerate(("pink", "amber", "lime")):
        body.append(f'<circle cx="{30 + i * 22}" cy="26" r="6.5" fill="{ACCENT[c]}"/>')
    body.append(f'<text x="{w / 2}" y="31" text-anchor="middle" font-family="{MONO}" font-size="14" fill="{MUTED}">tai.agent — langgraph stream</text>')
    body.append(f'<circle class="live" cx="{w - 74}" cy="26" r="5" fill="{ACCENT["pink"]}"/><text x="{w - 62}" y="31" font-family="{MONO}" font-size="13" fill="{MUTED}">live</text>')
    # Prompt line.
    body.append(
        f'<text x="40" y="96" font-family="{MONO}" font-size="17" fill="{INK}"><tspan fill="{ACCENT["lime"]}">$</tspan> python -m tai.agent --stream '
        f'<tspan fill="{DIM}"># introduce yourself</tspan></text>'
    )
    y0, lh = 138, 37
    for i, (kind, name, value, latency, color) in enumerate(TRACE):
        y, d = y0 + i * lh, first + i * step
        mark = {"start": "◆", "end": "✔"}.get(kind, "▸")
        tag = {"node": "node", "tool": "tool"}.get(kind, "")
        head = f'<tspan fill="{DIM}">[{i:02d}]</tspan> <tspan fill="{ACCENT[color]}">{mark}</tspan> '
        if kind in ("node", "tool"):
            label = f"{tag}:{name}"
            pad = " " * (13 - len(label))
            head += f'<tspan fill="{MUTED}">{tag}:</tspan><tspan fill="{ACCENT[color]}" font-weight="700">{name}</tspan>{pad}<tspan fill="{DIM}">→</tspan> <tspan fill="{INK}">{esc(value)}</tspan>'
        elif kind == "start":
            head += f'<tspan fill="{ACCENT[color]}" font-weight="700">START</tspan>  <tspan fill="{DIM}">thread_id=tai-tz · checkpointer=memory</tspan>'
        else:
            head += f'<tspan fill="{ACCENT[color]}" font-weight="700">END</tspan>    <tspan fill="{MUTED}">state=</tspan><tspan fill="{ACCENT["amber"]}">{esc(value)}</tspan>'
        right = f'<text x="820" y="{y}" text-anchor="end" font-family="{MONO}" font-size="14" fill="{DIM}">{latency}</text>' if latency else ""
        body.append(f'<g class="ln" style="--d:{d:.2f}s"><text x="40" y="{y}" font-family="{MONO}" font-size="16.5" xml:space="preserve">{head}</text>{right}</g>')
    end_y = y0 + len(TRACE) * lh
    body.append(
        f'<g class="ln" style="--d:{first + len(TRACE) * step:.2f}s"><text x="40" y="{end_y}" font-family="{MONO}" font-size="16.5" fill="{ACCENT["lime"]}">$</text>'
        f'<rect class="blink" x="58" y="{end_y - 15}" width="10" height="19" fill="{ACCENT["cyan"]}"/></g>'
    )
    # Mini graph on the right, lighting up in sync with the trace.
    gx, top, gap = 1010, 92, 47
    body.append(f'<line x1="850" y1="70" x2="850" y2="{h - 24}" stroke="{BORDER}"/>')
    for i in range(len(TRACE) - 1):
        body.append(f'<line class="flow" x1="{gx}" y1="{top + i * gap + 15}" x2="{gx}" y2="{top + (i + 1) * gap - 15}" stroke="{ACCENT[TRACE[i + 1][4]]}" stroke-opacity="0.6" stroke-width="2"/>')
    for i, (kind, name, _v, _l, color) in enumerate(TRACE):
        cy, d = top + i * gap, first + i * step
        label = name if kind in ("start", "end") else name
        bw = 150
        shape_rx = 15 if kind in ("start", "end") else 7
        body.append(
            f'<rect class="lit" style="--d:{d:.2f}s" x="{gx - bw / 2}" y="{cy - 15}" width="{bw}" height="30" rx="{shape_rx}" fill="{ACCENT[color]}" stroke="{ACCENT[color]}" stroke-width="1.5"/>'
            f'<text x="{gx}" y="{cy + 5}" text-anchor="middle" font-family="{MONO}" font-size="13.5" font-weight="700" fill="{INK}" stroke="{PANEL}" stroke-width="3" paint-order="stroke">{name}</text>'
        )
    return svg(w, h, "About me, streamed as an agent run", "A terminal streams a LangGraph-style run that introduces Nguyen Thanh Tai node by node while a small graph lights up.", style, "".join(body))


# ---------------------------------------------------------------------------------------------------------------------
# Stack: an isometric mechanical keyboard whose keycaps carry the tech stack and press in a wave
# ---------------------------------------------------------------------------------------------------------------------

STACK = [  # (category, color, [(label, width_in_units)])
    ("languages", "cyan", [("Python", 1.5), ("TypeScript", 1.5), ("JavaScript", 1.5), ("C", 1), ("HTML", 1), ("CSS", 1)]),
    ("ai / ml", "violet", [("PyTorch", 1.25), ("TensorFlow", 1.5), ("Keras", 1), ("scikit-learn", 1.75), ("NumPy", 1), ("SciPy", 1)]),
    ("llm", "pink", [("LangChain", 2), ("LangGraph", 2), ("LLM Agents", 3.5)]),
    ("web / backend", "amber", [("FastAPI", 1.25), ("Django", 1.25), ("Flask", 1), ("Node.js", 1.25), ("React", 1.25), ("Angular", 1.5)]),
    ("data / tools", "lime", [("MySQL", 1.25), ("SQLite", 1.25), ("Git", 1), ("GitHub", 1.25), ("VS Code", 1.5), ("Anaconda", 1.25)]),
]


def stack() -> str:
    w, h = 1200, 700
    unit, gap, pad = 80.0, 8.0, 22.0
    case_h, base_h, cap_h = 22.0, 14.0, 9.0
    style = (
        ".key{animation:press 5s ease-in-out infinite;animation-delay:var(--d)}"
        "@keyframes press{0%,9%,100%{transform:translateY(0)}4%{transform:translateY(6px)}}"
        ".glow{animation:glow 5s ease-in-out infinite;animation-delay:var(--d)}"
        "@keyframes glow{0%,12%,100%{opacity:.25}4%{opacity:.95}}"
        ".legend{animation:legend 5s ease-in-out infinite;animation-delay:var(--d)}"
        "@keyframes legend{0%,12%,100%{opacity:.85}4%{opacity:1}}"
    )
    rows_w = max(sum(k[1] for k in r[2]) for r in STACK) * unit
    depth = len(STACK) * unit
    ox, oy = 513.0, 135.0
    parts = [frame(w, h, "stack")]
    parts.append('<defs><filter id="kblur" x="-1" y="-1" width="3" height="3"><feGaussianBlur stdDeviation="9"/></filter></defs>')
    parts.append(f'<text x="40" y="58" font-family="{MONO}" font-size="16" fill="{MUTED}"><tspan fill="{ACCENT["lime"]}">$</tspan> cat ~/.stack</text>')
    # Case.
    cx0, cy0, cw, cd = -pad, -pad, rows_w + 2 * pad - gap, depth + 2 * pad - gap
    shadow = [iso(cx0, cy0, 0, ox, oy + 26), iso(cx0 + cw, cy0, 0, ox, oy + 26), iso(cx0 + cw, cy0 + cd, 0, ox, oy + 26), iso(cx0, cy0 + cd, 0, ox, oy + 26)]
    parts.append(f'<polygon points="{pts(shadow)}" fill="{ACCENT["violet"]}" opacity="0.22" filter="url(#kblur)"/>')
    parts.append(box(cx0, cy0, -case_h, cw, cd, case_h, FACES["deck"], ox, oy))
    rim = [iso(cx0 + cw, cy0, 0, ox, oy), iso(cx0 + cw, cy0 + cd, 0, ox, oy), iso(cx0, cy0 + cd, 0, ox, oy)]
    parts.append(f'<polyline points="{pts(rim)}" fill="none" stroke="{ACCENT["cyan"]}" stroke-opacity="0.45" stroke-width="1.3"/>')
    for r, (_cat, color, keys) in enumerate(STACK):
        x = 0.0
        y = r * unit
        for label, units in keys:
            kw, kd = units * unit - gap, unit - gap
            delay = (x / unit + r * 0.9) * 0.13
            glow = [iso(x - 4, y - 4, 0, ox, oy), iso(x + kw + 4, y - 4, 0, ox, oy), iso(x + kw + 4, y + kd + 4, 0, ox, oy), iso(x - 4, y + kd + 4, 0, ox, oy)]
            cap_faces = ("#1b2644", "#111a31", "#0b1224")
            base_faces = ("#141d36", "#0d152a", "#080e1e")
            inset = 7.0
            parts.append(
                f'<g style="--d:{delay:.2f}s">'
                f'<polygon class="glow" points="{pts(glow)}" fill="{ACCENT[color]}" filter="url(#kblur)"/>'
                f'<g class="key">{box(x, y, 0, kw, kd, base_h, base_faces, ox, oy)}'
                f"{box(x + inset, y + inset, base_h, kw - 2 * inset, kd - 2 * inset, cap_h, cap_faces, ox, oy)}"
                f'<polygon points="{pts([iso(x + inset, y + inset, base_h + cap_h, ox, oy), iso(x + kw - inset, y + inset, base_h + cap_h, ox, oy), iso(x + kw - inset, y + kd - inset, base_h + cap_h, ox, oy), iso(x + inset, y + kd - inset, base_h + cap_h, ox, oy)])}" fill="none" stroke="{ACCENT[color]}" stroke-opacity="0.45"/>'
                f'<text class="legend" transform="{top_matrix(x + kw / 2, y + kd / 2, base_h + cap_h, ox, oy)}" x="0" y="5" text-anchor="middle" font-family="{MONO}" font-size="{14 if len(label) < 11 else 12.5}" font-weight="700" fill="{ACCENT[color]}">{esc(label)}</text>'
                "</g></g>"
            )
            x += units * unit
    # Legend.
    lx = w - 40 - sum(46 + len(cat) * 8.6 for cat, _c, _k in STACK) + 46 - 20
    for cat, color, _keys in STACK:
        parts.append(f'<rect x="{lx:.0f}" y="{47}" width="12" height="12" rx="3" fill="{ACCENT[color]}"/><text x="{lx + 20:.0f}" y="58" font-family="{MONO}" font-size="14" fill="{MUTED}">{cat}</text>')
        lx += 46 + len(cat) * 8.6
    return svg(w, h, "Tech stack keyboard", "An isometric mechanical keyboard; each glowing keycap is a technology Tai uses, grouped by color: languages, AI/ML, LLM, web/backend, data and tools.", style, "".join(parts))


# ---------------------------------------------------------------------------------------------------------------------
# Contact buttons
# ---------------------------------------------------------------------------------------------------------------------


def button(name: str, label: str, value: str, color: str, icon: str) -> str:
    w, h = 340, 64
    style = (
        ".shine{animation:shine 4.5s ease-in-out infinite}"
        "@keyframes shine{0%,55%{transform:translateX(-160px)}85%,100%{transform:translateX(420px)}}"
    )
    body = (
        f'<defs><clipPath id="{name}-clip"><rect width="{w}" height="{h}" rx="14"/></clipPath>'
        f'<linearGradient id="{name}-sh" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.5" stop-color="#fff" stop-opacity="0.16"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>'
        f'<rect width="{w}" height="{h}" rx="14" fill="{PANEL}"/>'
        f'<rect x="0.75" y="0.75" width="{w - 1.5}" height="{h - 1.5}" rx="13.25" fill="none" stroke="{color}" stroke-opacity="0.7" stroke-width="1.5"/>'
        f'<rect x="12" y="12" width="40" height="40" rx="10" fill="{color}"/>{icon}'
        f'<text x="66" y="28" font-family="{MONO}" font-size="12" fill="{MUTED}">{label}</text>'
        f'<text x="66" y="48" font-family="{SANS}" font-size="16.5" font-weight="700" fill="{INK}">{esc(value)}</text>'
        f'<g clip-path="url(#{name}-clip)"><rect class="shine" x="0" y="-20" width="90" height="{h + 40}" fill="url(#{name}-sh)" transform="skewX(-20)"/></g>'
    )
    return svg(w, h, f"{label}: {value}", f"Contact button: {label} {value}", style, body)


MAIL_ICON = '<rect x="21" y="23" width="22" height="16" rx="2.5" fill="none" stroke="#0b1122" stroke-width="2.4"/><path d="M22 25l10 7 10-7" fill="none" stroke="#0b1122" stroke-width="2.4" stroke-linejoin="round"/>'
IN_ICON = f'<text x="32" y="40" text-anchor="middle" font-family="{SANS}" font-size="21" font-weight="800" fill="#0b1122">in</text>'


def main() -> None:
    OUT.mkdir(exist_ok=True)
    files = {
        "hero.svg": hero(),
        "agent-trace.svg": trace(),
        "stack.svg": stack(),
        "btn-email.svg": button("mail", "email", "n.t.tai435@gmail.com", ACCENT["pink"], MAIL_ICON),
        "btn-linkedin.svg": button("li", "linkedin", "in/se-nttai", ACCENT["cyan"], IN_ICON),
    }
    for name, content in files.items():
        (OUT / name).write_text(content, encoding="utf-8")
        print(f"wrote assets/{name} ({len(content) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
