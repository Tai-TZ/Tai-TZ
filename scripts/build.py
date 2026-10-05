"""Build the static newsprint figures for the profile README.

    python scripts/build.py              # about.svg, stack.svg, contact buttons
    python scripts/build_masthead.py     # masthead.svg (needs fonttools + uharfbuzz)

The skyline is dynamic and rendered by scripts/skyline.py from a GitHub Action.
"""

from __future__ import annotations

from html import escape

from newsprint import LIGHT, MONO, OUT_DIR, W, Diagram, _chip, _chip_w, cols, mono_w


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

    for i, n in enumerate(nodes):
        path = (
            f"M {start_x} {whoami.left[1]:.1f} H {whoami.x:.1f} V {bus_b} H {n.x:.1f} V {bus_c} H 520 "
            f"V {runtime.right[1]:.1f} H {end_x}"
        )
        d.packet(path, 7.0, i * 1.75)
    return d


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
    for i in reversed(range(len(layers))):  # bottom slab first so each upper slab sits in front
        code = layers[i][0]
        d.block(x_stack, cy0 + i * gap, hw=hw, bh=bh, code=code, key=code == "LLM", pulse=code == "LLM")
    for i, (_, name, chips) in enumerate(layers):
        cy = cy0 + i * gap
        d.edge(f"M {x_stack + hw + 8} {cy + bh / 2:.1f} H {label_x - 10}", arrow=False, dotted=True)
        d.text(label_x, cy - 10, f"{i + 1:02d}", cls="m r", weight=700)
        d.text(label_x + 30, cy - 10, name, cls="m k i", weight=700)
        x = label_x
        for chip in chips:
            w = _chip_w(chip)
            _chip(d, x, cy + 2, w, chip, h=28, bullet=False)
            x += w + 10
    return d


def button(name: str, tag: str, value: str) -> str:
    """Newsprint contact card: ink rule, hard shadow, red tag, a pulsing red diamond."""
    w, h, tw = 360, 64, mono_w(tag, 14, spaced=True) + 18
    style = (
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
        f'aria-label="{escape(label)}"><title>{escape(label)}</title><style>{style}</style>{body}</svg>\n'
    )


def main() -> None:
    for fig in (about(), stack()):
        print("wrote", fig.save().name)
    for name, tag, value in (("btn-email", "EMAIL", "n.t.tai435@gmail.com"), ("btn-linkedin", "LINKEDIN", "in/se-nttai")):
        (OUT_DIR / f"{name}.svg").write_text(button(name, tag, value), encoding="utf-8", newline="\n")
        print("wrote", f"{name}.svg")


if __name__ == "__main__":
    main()
