"""Build the static newsprint figures for the profile README.

    python scripts/build.py              # about, listing, stack, contact buttons
    python scripts/build_masthead.py     # masthead.svg (needs fonttools + uharfbuzz)

The skyline is dynamic and rendered by scripts/skyline.py from a GitHub Action.
"""

from __future__ import annotations

import re
from html import escape

from newsprint import LIGHT, MONO, OUT_DIR, W, Box, Diagram, _chip, _chip_w, cols, mono_w, pts

# ---------------------------------------------------------------------------------------------------------------------
# Helpers on top of the Arionear kit
# ---------------------------------------------------------------------------------------------------------------------


def mark(d: Diagram) -> dict[str, int]:
    """Remember how many fragments each layer holds, to wrap whatever gets added next."""
    return {k: len(v) for k, v in d.layers.items()}


def wrap(d: Diagram, since: dict[str, int], cls: str, style: str = "") -> None:
    """Wrap the fragments added since ``since`` (per layer) in an animated group."""
    attr = f' style="{style}"' if style else ""
    for layer, n in since.items():
        frags = d.layers[layer][n:]
        if frags:
            d.layers[layer][n:] = [f'<g class="{cls}"{attr}>{"".join(frags)}</g>']


def style(d: Diagram, css: str) -> None:
    d.defs.append(f"<style>{css}@media (prefers-reduced-motion:reduce){{.drop,.rise,.fl{{animation:none}}}}</style>")


def flash(d: Diagram, box: Box, events: list[float], dur: float) -> None:
    """Light a block's top face red at each event time (fraction of ``dur``), like a node executing."""
    if not events:
        return
    times, values = [0.0], [0.0]
    for t in sorted(events):
        for dt, v in ((0.0, 0.0), (0.02, 0.9), (0.09, 0.0)):
            tt = min(max(t + dt, times[-1]), 1.0)
            times.append(tt)
            values.append(v)
    times.append(1.0)
    values.append(0.0)
    top = pts((box.x, box.cy - box.hh), (box.x + box.hw, box.cy), (box.x, box.cy + box.hh), (box.x - box.hw, box.cy))
    d.add(
        "blocks",
        f'<polygon points="{top}" class="r" opacity="0"><animate attributeName="opacity" values="{";".join(f"{v:g}" for v in values)}" '
        f'keyTimes="{";".join(f"{t:.4f}" for t in times)}" dur="{dur}s" repeatCount="indefinite"/></polygon>',
    )


# ---------------------------------------------------------------------------------------------------------------------
# FIG. 1.0 — about me as a StateGraph
# ---------------------------------------------------------------------------------------------------------------------


def about() -> Diagram:
    d = Diagram(
        "about",
        700,
        title="Tai, as a StateGraph",
        deck="Every node is one piece of me — the run goes from START to END",
        desk="PROFILE DESK",
        fig="1.0",
        kicker="AGENT GRAPH",
        source="tai/graph.py",
        ticker=("PROBLEM SOLVER", "ALWAYS LEARNING", "COFFEE ∞", "UTC+7"),
        aria="About Nguyen Thanh Tai drawn as an agent graph: whoami, then location (Hanoi, Vietnam), focus "
        "(LLM agents with LangChain and LangGraph), stack (Python, TypeScript, PyTorch, FastAPI) and habits "
        "(VS Code, zsh, Tokyo Night), merging into runtime: always learning, fuelled by coffee.",
    )
    xs = cols(4, 20, W - 140)  # leave the right gutter for the last column's label
    big = {"hw": 30, "bh": 18, "mono_title": True, "title_size": 16, "label": "right"}
    start_x, row_a = xs[0], 262
    whoami = d.block(xs[1], row_a, code="WHO", title="whoami_node", sub="Nguyen Thanh Tai", sub2="Software / AI Engineer", **big)
    d.terminal(start_x, whoami.left[1], "START")
    d.edge(f"M {start_x + 30} {whoami.left[1]:.1f} H {whoami.left[0] - 10:.1f}")

    branches = (
        ("LOC", "locate_node", "Hanoi, Vietnam", "UTC+7", False),
        ("LLM", "focus_node", "LLM agents", "LangChain · LangGraph", True),
        ("STK", "stack_node", "Python · TypeScript", "PyTorch · FastAPI", False),
        ("DEV", "habits_node", "VS Code · zsh", "Tokyo Night", False),
    )
    row_b, bus_b, bus_c = 410, 345, 530
    small = {"mono_title": True, "title_size": 16, "label": "right"}
    nodes = [
        d.block(x, row_b, code=code, title=t, sub=s1, sub2=s2, key=key, pulse=key, **small)
        for x, (code, t, s1, s2, key) in zip(xs, branches, strict=True)
    ]
    d.edge(f"M {whoami.x:.1f} {whoami.bottom[1] + 8:.1f} V {bus_b}", arrow=False)
    d.drops(bus_b, nodes)
    for n in nodes:
        d.edge(f"M {n.x:.1f} {n.bottom[1] + 8:.1f} V {bus_c}", arrow=False)
    d.edge(f"M {nodes[0].x:.1f} {bus_c} H {nodes[-1].x:.1f}", arrow=False)

    runtime = d.block(520, 600, code="RUN", title="runtime_node", sub="uptime: always learning", sub2="fuel: coffee ∞", hw=30, bh=18, mono_title=True, title_size=16, label="left")
    d.edge(f"M 520 {bus_c} V {runtime.top[1] - 10:.1f}")
    end_x = W - 140
    d.terminal(end_x, runtime.right[1], "END")
    d.edge(f"M {runtime.right[0] + 8:.1f} {runtime.right[1]:.1f} H {end_x - 31}")
    d.text((whoami.x + nodes[0].x) / 2, bus_b - 10, "fan-out", cls="m q", anchor="middle", halo=True)
    d.text(nodes[-1].x - 70, bus_c - 10, "merge state", cls="m q", anchor="middle", halo=True)

    # Packets: one per branch, 1.75 s apart on a 7 s loop; each node flashes as a packet passes through it.
    dur, gap = 7.0, 1.75
    for i, n in enumerate(nodes):
        path = (
            f"M {start_x} {whoami.left[1]:.1f} H {whoami.x:.1f} V {bus_b} H {n.x:.1f} V {bus_c} H 520 "
            f"V {runtime.right[1]:.1f} H {end_x}"
        )
        d.packet(path, dur, i * gap)
        flash(d, n, [(i * gap + 0.42 * dur) / dur % 1.0], dur)
    flash(d, whoami, [(i * gap + 0.14 * dur) / dur % 1.0 for i in range(4)], dur)
    flash(d, runtime, [(i * gap + 0.8 * dur) / dur % 1.0 for i in range(4)], dur)
    return d


# ---------------------------------------------------------------------------------------------------------------------
# LISTING 1.1 — the same graph as code, with an execution bar and a streaming output column
# ---------------------------------------------------------------------------------------------------------------------

CODE = [
    "from langgraph.graph import StateGraph, START, END",
    "",
    "g = StateGraph(Tai)",
    'g.add_node("whoami", whoami)       # Nguyen Thanh Tai',
    'for n in ("locate", "focus", "stack", "habits"):',
    "    g.add_node(n, NODES[n])",
    '    g.add_edge("whoami", n)        # fan-out',
    '    g.add_edge(n, "runtime")       # merge state',
    'g.add_node("runtime", runtime)     # always learning',
    'g.add_edge(START, "whoami")',
    'g.add_edge("runtime", END)',
    "",
    "tai = g.compile()",
    'tai.invoke({"coffee": float("inf")})',
]
OUTPUT = [
    ("[whoami] ", 'name="Nguyen Thanh Tai"'),
    ("[locate] ", 'city="Hanoi" tz="UTC+7"'),
    ("[focus]  ", '"LLM agents"'),
    ("[stack]  ", "py · ts · torch · fastapi"),
    ("[habits] ", "vscode · zsh"),
    ("[runtime]", " learning=always"),
    ("✔ END    ", "coffee=inf"),
]
KEYWORDS = {"from", "import", "for", "in"}


def highlight(line: str) -> str:
    """Tiny Python highlighter in newsprint inks: keywords bold, strings red, comments muted italic."""
    code, _, comment = line.partition("#") if "#" in line and '"#' not in line else (line, "", "")
    out = []
    for tok in re.split(r'("[^"]*"|\b\w+\b)', code):
        if not tok:
            continue
        if tok.startswith('"'):
            out.append(f'<tspan class="r">{escape(tok)}</tspan>')
        elif tok in KEYWORDS:
            out.append(f'<tspan font-weight="700">{escape(tok)}</tspan>')
        elif tok in {"StateGraph", "START", "END", "float"}:
            out.append(f'<tspan class="r" font-weight="700">{escape(tok)}</tspan>')
        else:
            out.append(escape(tok))
    if comment:
        out.append(f'<tspan class="q" font-style="italic">#{escape(comment)}</tspan>')
    return "".join(out)


def listing() -> Diagram:
    d = Diagram(
        "listing",
        664,
        title="Listing 1.1 — compiling Tai",
        deck="The graph above, as code: the red bar follows the run, the right column streams the state",
        desk="PROFILE DESK",
        fig="1.1",
        kicker="LISTING",
        source="tai/graph.py",
        ticker=("PYTHON", "LANGGRAPH", "STATEGRAPH", "COMPILE()", "INVOKE()"),
        aria="A Python listing that builds Tai as a LangGraph StateGraph and invokes it, with the streamed output: "
        "name Nguyen Thanh Tai, Hanoi, LLM agents, Python and TypeScript stack, VS Code and zsh, always learning.",
    )
    x0, y0, cw, lh = 40, 218, 640, 25
    ch = lh * len(CODE) + 24
    d.add("lanes", f'<rect x="{x0 + 4}" y="{y0 + 4}" width="{cw}" height="{ch}" class="sh"/><rect x="{x0}" y="{y0}" width="{cw}" height="{ch}" class="t e"/>')
    d.add("lanes", f'<rect x="{x0}" y="{y0}" width="44" height="{ch}" class="i" fill-opacity=".05"/><path d="M {x0 + 44} {y0} V {y0 + ch}" class="ln" stroke-opacity=".3"/>')

    # Execution bar: steps through the statements, then holds on invoke() while the output streams.
    steps = [0, 2, 3, 4, 5, 6, 7, 4, 5, 6, 7, 8, 9, 10, 12, 13]
    cycle, step_t = 15.0, 0.42
    times = [i * step_t / cycle for i in range(len(steps))] + [1.0]
    ys = [y0 + 12 + s * lh for s in steps] + [y0 + 12 + steps[-1] * lh]
    kt = ";".join(f"{t:.4f}" for t in times)
    vals = ";".join(f"{y:.1f}" for y in ys)
    d.add(
        "edges",
        f'<rect x="{x0 + 1}" width="{cw - 2}" height="{lh}" class="r" fill-opacity=".1" y="{ys[0]:.1f}">'
        f'<animate attributeName="y" values="{vals}" keyTimes="{kt}" calcMode="discrete" dur="{cycle}s" repeatCount="indefinite"/></rect>'
        f'<path d="M 0 -6 L 8 0 L 0 6 z" class="r"><animateTransform attributeName="transform" type="translate" '
        f'values="{";".join(f"{x0 + 6} {y + lh / 2:.1f}" for y in ys)}" keyTimes="{kt}" calcMode="discrete" dur="{cycle}s" repeatCount="indefinite"/></path>',
    )
    for i, line in enumerate(CODE):
        y = y0 + 12 + i * lh + 17
        d.add("labels", f'<text x="{x0 + 34}" y="{y}" text-anchor="end" class="m q" font-size="12">{i + 1}</text>')
        if line:
            d.add("labels", f'<text x="{x0 + 58}" y="{y}" class="m i" font-size="14" xml:space="preserve">{highlight(line)}</text>')

    # Output column: an ink terminal that prints the state once invoke() is reached.
    ox, ow = x0 + cw + 24, W - 40 - (x0 + cw + 24)
    d.add("lanes", f'<rect x="{ox + 4}" y="{y0 + 4}" width="{ow}" height="{ch}" class="sh"/><rect x="{ox}" y="{y0}" width="{ow}" height="{ch}" class="i"/>')
    d.add("lanes", f'<rect x="{ox}" y="{y0}" width="{ow}" height="30" class="r"/>')
    d.text(ox + 12, y0 + 20, "STDOUT", cls="m k o", weight=700, layer="lanes")
    d.add("lanes", f'<circle cx="{ox + ow - 18}" cy="{y0 + 15}" r="4" class="o"><animate attributeName="opacity" values="1;.2;1" dur="1.4s" repeatCount="indefinite"/></circle>')
    start = (len(steps) - 1) * step_t / cycle + 0.02
    d.add("labels", f'<text x="{ox + 12}" y="{y0 + 56}" class="m o" font-size="12.5" opacity=".7">&gt;&gt;&gt; tai.invoke(...)</text>')
    for k, (tag, val) in enumerate(OUTPUT):
        t = start + k * 0.035
        y = y0 + 86 + k * 30
        anim = f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{t:.4f};{t + 0.01:.4f};.97;1" dur="{cycle}s" repeatCount="indefinite"/>'
        last = k == len(OUTPUT) - 1
        tag_css = 'fill="#FF5A5F"' if last else 'class="o" fill-opacity=".55"'
        d.add("labels", f'<text x="{ox + 12}" y="{y}" class="m" font-size="12.5" opacity="0" xml:space="preserve"><tspan {tag_css} font-weight="700">{escape(tag)}</tspan><tspan class="o"> {escape(val)}</tspan>{anim}</text>')
    caret_y = y0 + 86 + len(OUTPUT) * 30 - 12
    d.add("labels", f'<rect x="{ox + 12}" y="{caret_y}" width="8" height="15" class="r"><animate attributeName="opacity" values="1;0;1" dur="1s" calcMode="discrete" repeatCount="indefinite"/></rect>')
    return d


# ---------------------------------------------------------------------------------------------------------------------
# FIG. 2.0 — tech stack: slabs drop in and assemble, chip rows slide in
# ---------------------------------------------------------------------------------------------------------------------


def stack() -> Diagram:
    d = Diagram(
        "stack",
        830,
        title="Tech stack",
        deck="Grouped by layer, from the first notebook to a deployed agent",
        desk="ENGINEERING DESK",
        fig="2.0",
        kicker="STACK",
        source="~/.stack",
        ticker=("PYTHON", "TYPESCRIPT", "LANGGRAPH", "PYTORCH", "FASTAPI"),
        aria="Tech stack by layer. Languages: Python, TypeScript, JavaScript, C. LLM: LangChain, LangGraph, LLM agents. "
        "AI/ML: PyTorch, TensorFlow, Keras, scikit-learn, NumPy, Pandas, SciPy. Backend: FastAPI, Django, Flask, Node.js. "
        "Frontend: React, Angular, HTML, CSS. Data: MySQL, SQLite. Tools: Git, GitHub, VS Code, Anaconda.",
    )
    style(
        d,
        ".drop{animation:drop .8s cubic-bezier(.3,1.35,.5,1) both;animation-delay:calc(var(--i) * .16s)}"
        "@keyframes drop{from{transform:translateY(-70px);opacity:0}}"
        ".rise{animation:rise .7s ease-out both;animation-delay:calc(1.2s + var(--i) * .12s)}"
        "@keyframes rise{from{transform:translateX(-14px);opacity:0}}"
        ".fl{animation:fl 4s ease-in-out infinite;animation-delay:calc(2.4s + var(--i) * .3s)}"
        "@keyframes fl{0%,100%{transform:translateY(0)}50%{transform:translateY(-3px)}}",
    )
    layers = (
        ("LANG", "LANGUAGES", ("Python", "TypeScript", "JavaScript", "C")),
        ("LLM", "LLM", ("LangChain", "LangGraph", "LLM agents")),
        ("ML", "AI / ML", ("PyTorch", "TensorFlow", "Keras", "scikit-learn", "NumPy", "Pandas", "SciPy")),
        ("API", "BACKEND", ("FastAPI", "Django", "Flask", "Node.js")),
        ("UI", "FRONTEND", ("React", "Angular", "HTML", "CSS")),
        ("DB", "DATA", ("MySQL", "SQLite")),
        ("DEV", "TOOLS", ("Git", "GitHub", "VS Code", "Anaconda")),
    )
    x_stack, hw, bh, gap, cy0 = 170, 54, 12, 76, 262
    label_x = 290
    for j, i in enumerate(reversed(range(len(layers)))):  # bottom slab first so each upper slab sits in front
        code = layers[i][0]
        snap = mark(d)
        d.block(x_stack, cy0 + i * gap, hw=hw, bh=bh, code=code, key=code == "LLM", pulse=code == "LLM")
        wrap(d, snap, "drop", f"--i:{j}")
    for i, (_, name, chips) in enumerate(layers):
        cy = cy0 + i * gap
        snap = mark(d)
        d.edge(f"M {x_stack + hw + 8} {cy + bh / 2:.1f} H {label_x - 10}", arrow=False, dotted=True)
        d.text(label_x, cy - 10, f"{i + 1:02d}", cls="m r", weight=700)
        d.text(label_x + 30, cy - 10, name, cls="m k i", weight=700)
        x = label_x
        for chip in chips:
            w = _chip_w(chip)
            _chip(d, x, cy + 2, w, chip, h=28, bullet=False)
            x += w + 10
        wrap(d, snap, "rise", f"--i:{i}")
    return d


# ---------------------------------------------------------------------------------------------------------------------
# Contact cards
# ---------------------------------------------------------------------------------------------------------------------


def button(tag: str, value: str) -> str:
    """Newsprint contact card: ink rule, hard shadow, red tag, a pulsing red diamond."""
    w, h, tw = 360, 64, mono_w(tag, 14, spaced=True) + 18
    css = (
        f":root{{{';'.join(f'--{k}:{v}' for k, v in LIGHT.items())}}}"
        ".dm{animation:dm 2.4s ease-in-out infinite;transform-box:fill-box;transform-origin:center}"
        "@keyframes dm{0%,100%{transform:scale(1)}50%{transform:scale(1.5)}}"
        "@media (prefers-reduced-motion:reduce){.dm{animation:none}}"
    )
    body = (
        f'<rect x="4" y="4" width="{w - 5}" height="{h - 5}" fill="var(--ik)" fill-opacity=".18"/>'
        f'<rect x=".75" y=".75" width="{w - 5.5}" height="{h - 5.5}" fill="var(--tp)" stroke="var(--ik)" stroke-width="1.5"/>'
        f'<rect x="14" y="{(h - 4) / 2 - 13:.1f}" width="{tw:.1f}" height="26" fill="var(--rd)"/>'
        f'<text x="24" y="{(h - 4) / 2 + 5:.1f}" font-family="{MONO}" font-size="14" font-weight="700" letter-spacing=".12em" fill="var(--on)">{tag}</text>'
        f'<text x="{24 + tw:.1f}" y="{(h - 4) / 2 + 6:.1f}" font-family="{MONO}" font-size="16" font-weight="700" fill="var(--ik)">{escape(value)}</text>'
        f'<path class="dm" d="M {w - 30} {(h - 4) / 2 - 6:.1f} l 6 6 l -6 6 l -6 -6 z" fill="var(--rd)"/>'
    )
    label = f"{tag}: {value}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
        f'aria-label="{escape(label)}"><title>{escape(label)}</title><style>{css}</style>{body}</svg>\n'
    )


def main() -> None:
    for fig in (about(), listing(), stack()):
        print("wrote", fig.save().name)
    for name, tag, value in (("btn-email", "EMAIL", "n.t.tai435@gmail.com"), ("btn-linkedin", "LINKEDIN", "in/se-nttai")):
        (OUT_DIR / f"{name}.svg").write_text(button(tag, value), encoding="utf-8", newline="\n")
        print("wrote", f"{name}.svg")


if __name__ == "__main__":
    main()
