"""Render the last year of GitHub contributions as an animated 3D skyline.

    GITHUB_TOKEN=... python scripts/skyline.py --user Tai-TZ --out dist/skyline.svg
    python scripts/skyline.py --input calendar.json --out assets/skyline.svg   # offline, from a saved GraphQL response

Standard library only, so the GitHub Action needs no install step.
"""

import argparse
import json
import math
import os
import urllib.request
from datetime import date

from common import ACCENT, INK, MONO, MUTED, SANS, esc, frame, pts, svg

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

# A low dimetric camera: weeks run almost horizontally, weekdays recede steeply, so the year reads left to right.
AX, AY = math.radians(12), math.radians(58)
CELL, GAP = 15.0, 3.2
LEVELS = [  # (top, front, side) per activity quartile
    ("#164e63", "#0e3a4a", "#0a2a36"),
    ("#22d3ee", "#0891b2", "#0e7490"),
    ("#a78bfa", "#7c3aed", "#5b21b6"),
    ("#f472b6", "#db2777", "#9d174d"),
]
EMPTY = ("#18213b", "#111933", "#0c1328")


def fetch(user: str, token: str) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": user}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "tai-skyline"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def proj(x: float, y: float, z: float, ox: float, oy: float) -> tuple[float, float]:
    return ox + x * math.cos(AX) - y * math.cos(AY), oy + x * math.sin(AX) + y * math.sin(AY) - z


def bar(x: float, y: float, h: float, faces: tuple[str, str, str], ox: float, oy: float) -> str:
    top, front, side = faces
    w = CELL
    p = lambda a, b, c: proj(a, b, c, ox, oy)  # noqa: E731
    t = [p(x, y, h), p(x + w, y, h), p(x + w, y + w, h), p(x, y + w, h)]
    if h <= 2.5:
        return f'<polygon points="{pts(t)}" fill="{top}"/>'
    f = [p(x, y + w, h), p(x + w, y + w, h), p(x + w, y + w, 0), p(x, y + w, 0)]
    s = [p(x + w, y, h), p(x + w, y + w, h), p(x + w, y + w, 0), p(x + w, y, 0)]
    return f'<polygon points="{pts(f)}" fill="{front}"/><polygon points="{pts(s)}" fill="{side}"/><polygon points="{pts(t)}" fill="{top}"/>'


def streaks(days: list[tuple[date, int]]) -> tuple[int, int]:
    longest = run = 0
    for _d, n in days:
        run = run + 1 if n > 0 else 0
        longest = max(longest, run)
    current = 0
    tail = days[:-1] if days and days[-1][1] == 0 else days  # today not over yet: count from yesterday
    for _d, n in reversed(tail):
        if n == 0:
            break
        current += 1
    return current, longest


def render(calendar: dict, user: str) -> str:
    weeks = calendar["weeks"]
    total = calendar["totalContributions"]
    days = [(date.fromisoformat(d["date"]), d["contributionCount"], wi, d["weekday"]) for wi, wk in enumerate(weeks) for d in wk["contributionDays"]]
    counts = sorted(n for _d, n, _w, _wd in days if n > 0)
    peak = max(counts) if counts else 1
    q = [counts[int(len(counts) * f)] if counts else 1 for f in (0.25, 0.5, 0.75)]
    current, longest = streaks([(d, n) for d, n, _w, _wd in days])
    best = max(days, key=lambda t: t[1]) if days else None

    w, h = 1200, 500
    ox, oy = 150.0, 168.0
    style = (
        ".b{transform-box:fill-box;transform-origin:50% 100%;animation:grow 1.1s cubic-bezier(.2,.8,.2,1) both;animation-delay:var(--d)}"
        "@keyframes grow{from{transform:scaleY(0);opacity:0}}"
        ".sweep{animation:sweep 7s ease-in-out infinite;animation-delay:2.5s}"
        "@keyframes sweep{0%{transform:translateX(-260px)}60%,100%{transform:translateX(1250px)}}"
        ".peak{animation:peak 1.8s ease-in-out infinite}@keyframes peak{50%{opacity:.35}}"
        ".fade{animation:fade 1s ease both;animation-delay:var(--d,0s)}@keyframes fade{from{opacity:0;transform:translateY(8px)}}"
    )
    parts = [frame(w, h, "sky")]
    parts.append('<defs><linearGradient id="beam" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                 '<stop offset="0.5" stop-color="#fff" stop-opacity="0.13"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
                 '<filter id="sky-blur" x="-1" y="-1" width="3" height="3"><feGaussianBlur stdDeviation="16"/></filter>'
                 '<linearGradient id="vfade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                 '<stop offset="0.35" stop-color="#fff"/><stop offset="0.8" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
                 f'<mask id="beam-mask"><rect x="0" y="90" width="{w}" height="{h - 120}" fill="url(#vfade)"/></mask></defs>')
    n_weeks = len(weeks)
    span_x, span_y = n_weeks * (CELL + GAP), 7 * (CELL + GAP)
    plate = [proj(-8, -8, 0, ox, oy), proj(span_x + 5, -8, 0, ox, oy), proj(span_x + 5, span_y + 5, 0, ox, oy), proj(-8, span_y + 5, 0, ox, oy)]
    parts.append(f'<polygon points="{pts(plate)}" fill="{ACCENT["violet"]}" opacity="0.25" filter="url(#sky-blur)"/>')
    plate_low = [(px, py + 10) for px, py in plate]
    parts.append(f'<polygon points="{pts(plate_low[1:3] + plate[2:0:-1])}" fill="#0c1328"/><polygon points="{pts([plate_low[3], plate_low[2], plate[2], plate[3]])}" fill="#111933"/>')
    parts.append(f'<polygon points="{pts(plate)}" fill="#0d1428" stroke="{ACCENT["cyan"]}" stroke-opacity="0.35"/>')

    bars = []
    by_cell = {(wi, wd): (d, n) for d, n, wi, wd in days}
    for wd in range(7):  # back rows first, then left to right: correct painter's order for this camera
        for wi in range(n_weeks):
            if (wi, wd) not in by_cell:
                continue
            d, n = by_cell[(wi, wd)]
            x, y = wi * (CELL + GAP), wd * (CELL + GAP)
            if n == 0:
                bars.append(bar(x, y, 2, EMPTY, ox, oy))
                continue
            level = sum(n > t for t in q)
            height = 6 + 74 * math.sqrt(n / peak)
            bars.append(f'<g class="b" style="--d:{0.3 + wi * 0.03 + wd * 0.02:.2f}s"><title>{d.isoformat()}: {n} contributions</title>{bar(x, y, height, LEVELS[level], ox, oy)}</g>')
    parts.append("".join(bars))
    if best and best[1] > 0:
        bx, by = best[2] * (CELL + GAP) + CELL / 2, best[3] * (CELL + GAP) + CELL / 2
        tx, ty = proj(bx, by, 6 + 74 + 14, ox, oy)
        parts.append(f'<g class="fade" style="--d:2.2s"><circle class="peak" cx="{tx:.1f}" cy="{ty:.1f}" r="5" fill="{ACCENT["pink"]}"/>'
                     f'<text x="{tx:.1f}" y="{ty - 12:.1f}" text-anchor="middle" font-family="{MONO}" font-size="12" fill="{INK}">peak · {best[1]}</text></g>')
    # Light beam sweeping across the city.
    parts.append(f'<g mask="url(#beam-mask)" style="mix-blend-mode:screen"><rect class="sweep" x="0" y="90" width="200" height="{h - 120}" fill="url(#beam)"/></g>')

    # Month labels along the front edge.
    seen = set()
    for d, _n, wi, wd in days:
        if d.day <= 7 and wd == 0 and d.month not in seen:
            seen.add(d.month)
            lx, ly = proj(wi * (CELL + GAP), span_y + 14, 0, ox, oy)
            parts.append(f'<text x="{lx:.1f}" y="{ly + 12:.1f}" font-family="{MONO}" font-size="12" fill="{MUTED}">{d.strftime("%b").lower()}</text>')

    # Title and stats.
    parts.append(f'<g class="fade" style="--d:.1s"><text x="40" y="58" font-family="{MONO}" font-size="16" fill="{MUTED}"><tspan fill="{ACCENT["lime"]}">$</tspan> git log --since="1 year" | skyline</text>'
                 f'<text x="40" y="86" font-family="{MONO}" font-size="12.5" fill="{MUTED}">@{esc(user)} · updated {date.today().isoformat()}</text></g>')
    stats = [
        (f"{total:,}", "contributions / year", "cyan"),
        (f"{current}d", "current streak", "lime"),
        (f"{longest}d", "longest streak", "violet"),
        (str(best[1]) if best else "0", f"best day · {best[0].strftime('%b %d').lower()}" if best else "best day", "pink"),
    ]
    sx = 690.0
    for i, (value, label, color) in enumerate(stats):
        x = sx + (i % 2) * 245
        y = 34 + (i // 2) * 72
        parts.append(
            f'<g class="fade" style="--d:{0.4 + i * 0.15:.2f}s"><rect x="{x}" y="{y}" width="230" height="60" rx="12" fill="#0b1122" stroke="{ACCENT[color]}" stroke-opacity="0.5"/>'
            f'<text x="{x + 16}" y="{y + 36}" font-family="{SANS}" font-size="26" font-weight="800" fill="{ACCENT[color]}">{esc(value)}</text>'
            f'<text x="{x + 16}" y="{y + 52}" font-family="{MONO}" font-size="11.5" fill="{MUTED}">{esc(label)}</text></g>'
        )
    lx = 40.0
    for i, (top, _f, _s) in enumerate(LEVELS):
        parts.append(f'<rect x="{lx + i * 22}" y="{h - 44}" width="14" height="14" rx="3" fill="{top}"/>')
    parts.append(f'<text x="{lx + 4 * 22 + 6}" y="{h - 33}" font-family="{MONO}" font-size="12" fill="{MUTED}">less → more · bar height ∝ √contributions</text>')
    return svg(w, h, f"{user}'s contribution skyline", f"{total} contributions in the last year drawn as a 3D city; current streak {current} days, longest {longest} days.", style, "".join(parts))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default=os.environ.get("GITHUB_REPOSITORY_OWNER", "Tai-TZ"))
    ap.add_argument("--input", help="saved GraphQL JSON response (skips the API call)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    if args.input:
        with open(args.input, encoding="utf-8") as fh:
            data = json.load(fh)
    else:
        data = fetch(args.user, os.environ["GITHUB_TOKEN"])
    if "errors" in data:
        raise SystemExit(f"GraphQL error: {data['errors']}")
    calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    out = render(calendar, args.user)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(out)
    print(f"wrote {args.out} ({len(out) / 1024:.1f} KB), {calendar['totalContributions']} contributions")


if __name__ == "__main__":
    main()
