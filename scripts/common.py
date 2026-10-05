"""Shared helpers for the profile SVGs: palette, isometric projection, 3D boxes."""

import math

COS, SIN = math.cos(math.radians(30)), math.sin(math.radians(30))

# Night-lab palette. Every block has a lit top, a mid left face and a dark right face.
BG0, BG1 = "#060912", "#0d1530"
PANEL, BORDER = "#0b1122", "#1d2947"
INK, MUTED, DIM = "#e6edf7", "#8b9bb4", "#4a5a7a"
ACCENT = {"cyan": "#22d3ee", "violet": "#a78bfa", "pink": "#f472b6", "lime": "#a3e635", "amber": "#fbbf24"}
FACES = {
    "cyan": ("#67e8f9", "#0891b2", "#0e7490"),
    "violet": ("#c4b5fd", "#7c3aed", "#5b21b6"),
    "pink": ("#f9a8d4", "#db2777", "#9d174d"),
    "lime": ("#d9f99d", "#65a30d", "#3f6212"),
    "amber": ("#fde68a", "#d97706", "#92400e"),
    "slate": ("#26334f", "#151d33", "#0c1224"),
    "deck": ("#1a2440", "#10182e", "#0a1022"),
}

MONO = "'JetBrains Mono','Fira Code','Cascadia Code',Consolas,'Courier New',monospace"
SANS = "'Segoe UI','Inter',-apple-system,'Helvetica Neue',Arial,sans-serif"

REDUCED_MOTION = "@media (prefers-reduced-motion: reduce) { * { animation: none !important; } }"


def iso(x: float, y: float, z: float, ox: float, oy: float, s: float = 1.0) -> tuple[float, float]:
    """World (x right-down, y left-down, z up) to screen."""
    return ox + (x - y) * COS * s, oy + (x + y) * SIN * s - z * s


def pts(points: list[tuple[float, float]]) -> str:
    return " ".join(f"{px:.1f},{py:.1f}" for px, py in points)


def box(x: float, y: float, z: float, w: float, d: float, h: float, faces: tuple[str, str, str], ox: float, oy: float, s: float = 1.0, top_only: bool = False) -> str:
    top, left, right = faces
    p = lambda a, b, c: iso(a, b, c, ox, oy, s)  # noqa: E731
    top_face = [p(x, y, z + h), p(x + w, y, z + h), p(x + w, y + d, z + h), p(x, y + d, z + h)]
    if top_only:
        return f'<polygon points="{pts(top_face)}" fill="{top}"/>'
    left_face = [p(x, y + d, z + h), p(x + w, y + d, z + h), p(x + w, y + d, z), p(x, y + d, z)]
    right_face = [p(x + w, y, z + h), p(x + w, y + d, z + h), p(x + w, y + d, z), p(x + w, y, z)]
    return (
        f'<polygon points="{pts(left_face)}" fill="{left}"/>'
        f'<polygon points="{pts(right_face)}" fill="{right}"/>'
        f'<polygon points="{pts(top_face)}" fill="{top}"/>'
    )


def top_matrix(x: float, y: float, z: float, ox: float, oy: float, s: float = 1.0) -> str:
    """SVG transform that maps text drawn in the x/y world plane onto an isometric top face."""
    tx, ty = iso(x, y, z, ox, oy, s)
    return f"matrix({COS * s:.4f},{SIN * s:.4f},{-COS * s:.4f},{SIN * s:.4f},{tx:.1f},{ty:.1f})"


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg(width: int, height: int, title: str, desc: str, style: str, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-labelledby="t d">'
        f'<title id="t">{esc(title)}</title><desc id="d">{esc(desc)}</desc>'
        f"<style>{style}{REDUCED_MOTION}</style>{body}</svg>\n"
    )


def frame(width: int, height: int, gid: str) -> str:
    """Rounded night panel with a soft top glow, shared by every card."""
    return (
        f'<defs><linearGradient id="{gid}-bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG1}"/><stop offset="1" stop-color="{BG0}"/></linearGradient>'
        f'<radialGradient id="{gid}-glow" cx="0.5" cy="0" r="0.8"><stop offset="0" stop-color="#7c3aed" stop-opacity="0.28"/><stop offset="1" stop-color="#7c3aed" stop-opacity="0"/></radialGradient></defs>'
        f'<rect width="{width}" height="{height}" rx="20" fill="url(#{gid}-bg)"/>'
        f'<rect width="{width}" height="{height}" rx="20" fill="url(#{gid}-glow)"/>'
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="19.5" fill="none" stroke="{BORDER}"/>'
    )
