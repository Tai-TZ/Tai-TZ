"""Render the last year of GitHub contributions as a 3D skyline in the portfolio's style.

One column per day on a graph-paper plate; the busiest quarter of days is topped in red.
Writes a light and a dark SVG so the README can follow the viewer's GitHub theme.

    GITHUB_TOKEN=... python scripts/contrib3d.py --user Tai-TZ --out dist
    python scripts/contrib3d.py --input calendar.json --out dist      # offline, from a saved GraphQL response

Standard library only, so the GitHub Action needs no install step.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import urllib.request
from datetime import date, datetime, timezone
from html import escape
from pathlib import Path

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount weekday } }
      }
    }
  }
}
"""

# The portfolio's tokens (taithanh.ai20k.cloud, src/app/globals.css).
THEMES = {
    "light": {
        "paper": "#ebeae4",
        "plate": "#f2f1ec",
        "grid": "#dedcd3",
        "ink": "#22211d",
        "graphite": "#5a5851",
        "line": "#d6d4cb",
        "top": "#f7f6f2",
        "left": "#dcdad1",
        "right": "#c7c4b9",
        "edge": "#8f8c82",
        "red": "#b42a20",
        "red_left": "#8f2018",
        "red_right": "#741912",
    },
    "dark": {
        "paper": "#10100e",
        "plate": "#171715",
        "grid": "#1d1d1a",
        "ink": "#f3f3e6",
        "graphite": "#a3a399",
        "line": "#2a2a27",
        "top": "#3a3a35",
        "left": "#26261f",
        "right": "#1c1c18",
        "edge": "#4a4a43",
        "red": "#ef4a3c",
        "red_left": "#b8362b",
        "red_right": "#8f2a22",
    },
}

SANS = "'Be Vietnam Pro', Inter, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
W, H = 1040, 520
# Low dimetric camera: weeks run almost horizontally, weekdays recede steeply, so the year reads left to right.
AX, AY = math.radians(11), math.radians(56)
CELL, STEP = 13.0, 16.0
MAX_H = 84.0


def fetch(user: str, token: str) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": user}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "tai-contrib3d"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 (fixed https URL)
        return json.load(resp)


def pts(*points: tuple[float, float]) -> str:
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def streaks(days: list[tuple[date, int]]) -> tuple[int, int]:
    longest = run = 0
    for _d, n in days:
        run = run + 1 if n > 0 else 0
        longest = max(longest, run)
    current = 0
    tail = days[:-1] if days and days[-1][1] == 0 else days  # today is not over yet: count from yesterday
    for _d, n in reversed(tail):
        if n == 0:
            break
        current += 1
    return current, longest


def render(calendar: dict, user: str, theme: str) -> str:
    c = THEMES[theme]
    weeks = calendar["weeks"]
    total = calendar["totalContributions"]
    days = [
        (date.fromisoformat(d["date"]), d["contributionCount"], wi, d["weekday"])
        for wi, wk in enumerate(weeks)
        for d in wk["contributionDays"]
    ]
    counts = sorted(n for _d, n, _w, _wd in days if n > 0)
    peak = max(counts) if counts else 1
    red_from = counts[int(len(counts) * 0.75)] if counts else 1
    current, longest = streaks([(d, n) for d, n, _w, _wd in days])
    best = max(days, key=lambda t: t[1]) if days else None
    active = len(counts)

    # Camera origin: centres the plate horizontally and leaves room above it for the tallest columns.
    ox, oy = 136.0, 214.0

    def proj(x: float, y: float, z: float) -> tuple[float, float]:
        return ox + x * math.cos(AX) - y * math.cos(AY), oy + x * math.sin(AX) + y * math.sin(AY) - z

    out: list[str] = []
    add = out.append

    # Stats row.
    stats = [
        (f"{total:,}", "contributions in the last year"),
        (f"{active}", "active days"),
        (f"{longest} days", "longest streak"),
        (str(best[1]) if best else "0", f"best day, {best[0].strftime('%b')} {best[0].day}" if best else "best day"),
    ]
    col_w = (W - 80) / 4
    for i, (value, label) in enumerate(stats):
        x = 40 + i * col_w
        if i:
            add(f'<line x1="{x:.1f}" y1="38" x2="{x:.1f}" y2="98" stroke="{c["line"]}" stroke-width="1"/>')
        tx = x + (0 if i == 0 else 24)
        fill = c["red"] if i == 0 else c["ink"]
        add(f'<text x="{tx:.1f}" y="74" font-size="38" font-weight="700" fill="{fill}" letter-spacing="-1">{escape(value)}</text>')
        add(f'<text x="{tx:.1f}" y="96" font-size="14" fill="{c["graphite"]}">{escape(label)}</text>')

    # Plate.
    n_weeks = len(weeks)
    span_x, span_y = n_weeks * STEP, 7 * STEP
    plate = [proj(-8, -8, 0), proj(span_x + 4, -8, 0), proj(span_x + 4, span_y + 4, 0), proj(-8, span_y + 4, 0)]
    lip = [proj(-8, span_y + 4, 0), proj(span_x + 4, span_y + 4, 0), proj(span_x + 4, span_y + 4, -6), proj(-8, span_y + 4, -6)]
    side = [proj(span_x + 4, -8, 0), proj(span_x + 4, span_y + 4, 0), proj(span_x + 4, span_y + 4, -6), proj(span_x + 4, -8, -6)]
    add(f'<polygon points="{pts(*lip)}" fill="{c["left"]}"/><polygon points="{pts(*side)}" fill="{c["right"]}"/>')
    add(f'<polygon points="{pts(*plate)}" fill="{c["plate"]}" stroke="{c["line"]}" stroke-width="1"/>')

    by_cell = {(wi, wd): (dd, n) for dd, n, wi, wd in days}
    blocks: list[str] = []
    for wd in range(7):  # back row first, then left to right: correct painter's order for this camera
        for wi in range(n_weeks):
            if (wi, wd) not in by_cell:
                continue
            dd, n = by_cell[(wi, wd)]
            x, y = wi * STEP, wd * STEP
            if n == 0:
                tile = pts(proj(x, y, 0), proj(x + CELL, y, 0), proj(x + CELL, y + CELL, 0), proj(x, y + CELL, 0))
                blocks.append(f'<polygon points="{tile}" fill="none" stroke="{c["line"]}" stroke-width=".8"/>')
                continue
            h = 4 + (MAX_H - 4) * math.sqrt(n / peak)
            red = n >= red_from
            p = lambda a, b, z: proj(a, b, z)  # noqa: E731
            w = CELL
            top = pts(p(x, y, h), p(x + w, y, h), p(x + w, y + w, h), p(x, y + w, h))
            front = pts(p(x, y + w, h), p(x + w, y + w, h), p(x + w, y + w, 0), p(x, y + w, 0))
            right = pts(p(x + w, y, h), p(x + w, y + w, h), p(x + w, y + w, 0), p(x + w, y, 0))
            delay = 0.25 + wi * 0.022 + wd * 0.015
            blocks.append(
                f'<g class="g" style="animation-delay:{delay:.2f}s"><title>{dd.isoformat()}: {n} contributions</title>'
                f'<polygon points="{front}" fill="{c["red_left"] if red else c["left"]}" stroke="{c["edge"]}" stroke-width=".5"/>'
                f'<polygon points="{right}" fill="{c["red_right"] if red else c["right"]}" stroke="{c["edge"]}" stroke-width=".5"/>'
                f'<polygon points="{top}" fill="{c["red"] if red else c["top"]}" stroke="{c["edge"]}" stroke-width=".5"/></g>'
            )
    add("".join(blocks))

    # Month labels along the front edge.
    seen: set[int] = set()
    for dd, _n, wi, wd in days:
        if dd.day <= 7 and wd == 0 and dd.month not in seen:
            seen.add(dd.month)
            lx, ly = proj(wi * STEP, span_y + 14, 0)
            add(f'<text x="{lx:.1f}" y="{ly + 16:.1f}" font-size="13" fill="{c["graphite"]}">{dd.strftime("%b")}</text>')

    # Legend and timestamp share the row under the stats, above the skyline.
    stamp = datetime.now(timezone.utc).strftime("%b %-d, %Y")
    add(f'<line x1="40" y1="122" x2="{W - 40}" y2="122" stroke="{c["line"]}" stroke-width="1"/>')
    add(
        f'<g transform="translate(40 140)"><rect width="12" height="12" rx="2" fill="{c["red"]}"/>'
        f'<text x="20" y="11" font-size="13" fill="{c["graphite"]}">busiest quarter of active days</text></g>'
    )
    add(
        f'<text x="{W - 40}" y="151" text-anchor="end" font-size="13" fill="{c["graphite"]}">'
        f"@{escape(user)} on GitHub, updated {stamp}</text>"
    )

    aria = (
        f"{user}'s GitHub contributions over the last year as a 3D skyline: {total} contributions, {active} active days, "
        f"current streak {current} days, longest streak {longest} days."
    )
    style = (
        f"text{{font-family:{SANS}}}"
        ".g{transform-box:fill-box;transform-origin:50% 100%;animation:g 1s cubic-bezier(.22,1,.36,1) both}"
        "@keyframes g{from{transform:scaleY(0);opacity:0}}"
        "@media (prefers-reduced-motion:reduce){.g{animation:none}}"
    )
    grid = (
        f'<pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">'
        f'<path d="M32 0H0V32" fill="none" stroke="{c["grid"]}" stroke-width="1"/></pattern>'
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(aria)}">'
        f"<title>{escape(aria)}</title><style>{style}</style><defs>{grid}</defs>"
        f'<rect width="{W}" height="{H}" rx="18" fill="{c["paper"]}"/>'
        f'<rect width="{W}" height="{H}" rx="18" fill="url(#grid)" opacity=".9"/>'
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="17.5" fill="none" stroke="{c["line"]}"/>'
        + "".join(out)
        + "</svg>\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default=os.environ.get("GITHUB_REPOSITORY_OWNER", "Tai-TZ"))
    ap.add_argument("--input", help="saved GraphQL JSON response (skips the API call)")
    ap.add_argument("--out", required=True, help="output directory")
    args = ap.parse_args()
    if args.input:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    else:
        data = fetch(args.user, os.environ["GITHUB_TOKEN"])
    if "errors" in data:
        raise SystemExit(f"GraphQL error: {data['errors']}")
    calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        path = out / f"skyline-{theme}.svg"
        path.write_text(render(calendar, args.user, theme), encoding="utf-8")
        print(f"wrote {path} ({path.stat().st_size / 1024:.1f} KB)")
    print(f"{calendar['totalContributions']} contributions")


if __name__ == "__main__":
    main()
