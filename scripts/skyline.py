"""Render the last year of GitHub contributions as a newsprint 3D skyline (one ink line-art column per day).

    GITHUB_TOKEN=... python scripts/skyline.py --user Tai-TZ --out dist          # writes dist/skyline.svg
    python scripts/skyline.py --input calendar.json --out assets                # offline, from a saved GraphQL response

Standard library only, so the GitHub Action needs no install step.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import urllib.request
from datetime import date
from pathlib import Path

from newsprint import W, Diagram, pts

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

# Low dimetric camera: weeks run almost horizontally, weekdays recede steeply, so the year reads left to right.
AX, AY = math.radians(11), math.radians(56)
CELL, STEP = 13.0, 16.0
MAX_H = 72.0


def fetch(user: str, token: str) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": user}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "tai-skyline"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 — fixed https URL
        return json.load(resp)


def proj(x: float, y: float, z: float, ox: float, oy: float) -> tuple[float, float]:
    return ox + x * math.cos(AX) - y * math.cos(AY), oy + x * math.sin(AX) + y * math.sin(AY) - z


def column(x: float, y: float, h: float, ox: float, oy: float, *, red: bool) -> str:
    p = lambda a, b, c: proj(a, b, c, ox, oy)  # noqa: E731
    w = CELL
    top = pts(p(x, y, h), p(x + w, y, h), p(x + w, y + w, h), p(x, y + w, h))
    front = pts(p(x, y + w, h), p(x + w, y + w, h), p(x + w, y + w, 0), p(x, y + w, 0))
    side = pts(p(x + w, y, h), p(x + w, y + w, h), p(x + w, y + w, 0), p(x + w, y, 0))
    return (
        f'<polygon points="{front}" class="L e" stroke-width=".8"/>'
        f'<polygon points="{side}" class="R e" stroke-width=".8"/><polygon points="{side}" fill="url(#hatch)"/>'
        f'<polygon points="{top}" class="{"r" if red else "t"} e" stroke-width=".8"/>'
    )


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


def render(calendar: dict, user: str) -> Diagram:
    weeks = calendar["weeks"]
    total = calendar["totalContributions"]
    days = [(date.fromisoformat(d["date"]), d["contributionCount"], wi, d["weekday"]) for wi, wk in enumerate(weeks) for d in wk["contributionDays"]]
    counts = sorted(n for _d, n, _w, _wd in days if n > 0)
    peak = max(counts) if counts else 1
    red_from = counts[int(len(counts) * 0.75)] if counts else 1
    current, longest = streaks([(d, n) for d, n, _w, _wd in days])
    best = max(days, key=lambda t: t[1]) if days else None
    active = len(counts)

    d = Diagram(
        "skyline",
        720,
        title="Contribution skyline",
        deck="A year on GitHub, one column per day; the busiest quarter of days is set in red",
        desk="ACTIVITY DESK",
        fig="3.0",
        kicker="COMMITS",
        source=f"@{user} · updated {date.today().isoformat()}",
        ticker=(f"{total:,} CONTRIBUTIONS", f"{active} ACTIVE DAYS", "REDRAWN DAILY", "GITHUB ACTIONS"),
        aria=f"{user}'s contributions over the last year as a 3D skyline: {total} contributions, {active} active days, "
        f"current streak {current} days, longest streak {longest} days.",
    )
    d.defs.append(
        "<style>.g{transform-box:fill-box;transform-origin:50% 100%;animation:g 1.1s cubic-bezier(.2,.8,.2,1) both;"
        "animation-delay:var(--d)}@keyframes g{from{transform:scaleY(0);opacity:0}}"
        "@media (prefers-reduced-motion:reduce){.g{animation:none}}</style>"
    )

    # Stats as newspaper columns.
    stats = [
        (f"{total:,}", "CONTRIBUTIONS / YEAR"),
        (f"{current}d", "CURRENT STREAK"),
        (f"{longest}d", "LONGEST STREAK"),
        (str(best[1]) if best else "0", f"BEST DAY · {best[0].strftime('%b %d').upper()}" if best else "BEST DAY"),
    ]
    col_w = (W - 80) / 4
    for i, (value, label) in enumerate(stats):
        x = 40 + i * col_w
        if i:
            d.line(x, 214, x, 284, opacity=0.3)
        tx = x + (0 if i == 0 else 22)
        d.text(tx, 258, value, size=40, cls="d r" if i == 0 else "d i", weight=700, layer="bg")
        d.text(tx, 280, label, size=12, cls="m k q", weight=700, layer="bg")
    d.line(40, 300, W - 40, 300, opacity=0.45)

    ox, oy = 92.0, 412.0
    n_weeks = len(weeks)
    span_x, span_y = n_weeks * STEP, 7 * STEP
    plate = [proj(-6, -6, 0, ox, oy), proj(span_x + 3, -6, 0, ox, oy), proj(span_x + 3, span_y + 3, 0, ox, oy), proj(-6, span_y + 3, 0, ox, oy)]
    d.add("lanes", f'<polygon points="{pts(*plate)}" class="t e" stroke-width="1.3"/><polygon points="{pts(*plate)}" fill="url(#dots)"/>')
    by_cell = {(wi, wd): (dd, n) for dd, n, wi, wd in days}
    out = []
    for wd in range(7):  # back row first, then left to right: correct painter's order for this camera
        for wi in range(n_weeks):
            if (wi, wd) not in by_cell:
                continue
            dd, n = by_cell[(wi, wd)]
            x, y = wi * STEP, wd * STEP
            if n == 0:
                tile = pts(proj(x, y, 0, ox, oy), proj(x + CELL, y, 0, ox, oy), proj(x + CELL, y + CELL, 0, ox, oy), proj(x, y + CELL, 0, ox, oy))
                out.append(f'<polygon points="{tile}" class="ln" stroke-opacity=".18" stroke-width=".8"/>')
                continue
            h = 5 + (MAX_H - 5) * math.sqrt(n / peak)
            out.append(
                f'<g class="g" style="--d:{0.3 + wi * 0.028 + wd * 0.02:.2f}s"><title>{dd.isoformat()}: {n} contributions</title>'
                f"{column(x, y, h, ox, oy, red=n >= red_from)}</g>"
            )
    d.add("blocks", "".join(out))
    if best and best[1] > 0:
        bx, by = best[2] * STEP + CELL / 2, best[3] * STEP + CELL / 2
        tx, ty = proj(bx, by, MAX_H, ox, oy)
        ring = pts((tx, ty - 9), (tx + 15, ty), (tx, ty + 9), (tx - 15, ty))
        d.add("packets", f'<polygon class="pl" points="{ring}"/>')
        d.edge(f"M {tx:.1f} {ty - 14:.1f} V {ty - 40:.1f}", arrow=False, flow=False, dotted=True)
        d.text(tx, ty - 48, f"peak · {best[1]}", cls="m i", anchor="middle", weight=700, halo=True)

    seen: set[int] = set()
    for dd, _n, wi, wd in days:
        if dd.day <= 7 and wd == 0 and dd.month not in seen:
            seen.add(dd.month)
            lx, ly = proj(wi * STEP, span_y + 12, 0, ox, oy)
            d.text(lx, ly + 14, dd.strftime("%b").upper(), size=12, cls="m k q", weight=700)
    return d


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
    path = render(calendar, args.user).save(Path(args.out))
    print(f"wrote {path} ({path.stat().st_size / 1024:.1f} KB), {calendar['totalContributions']} contributions")


if __name__ == "__main__":
    main()
