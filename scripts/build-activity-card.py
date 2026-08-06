#!/usr/bin/env python3
"""Render assets/activity-{light,dark}.svg from the contribution calendar.

Every number on the card comes from one GraphQL response covering one window,
so the card can never disagree with the 3D calendar the way two third-party
services did.

Needs GITHUB_TOKEN in the environment.
"""

import json
import os
import urllib.request
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.github.com/graphql"
LOGIN = os.environ.get("PROFILE_LOGIN", "didik-maulana")

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          firstDay
          contributionDays { date contributionCount }
        }
      }
    }
  }
}
"""

THEMES = {
    "light": {
        "text": "#1f2328",
        "muted": "#59636e",
        "panel": "#ffffff",
        "border": "#d1d9e0",
        "bar": "#40c463",
        "bar_empty": "#ebedf0",
        "accent": "#0175C2",
    },
    "dark": {
        "text": "#e6edf3",
        "muted": "#8b949e",
        "panel": "#0d1117",
        "border": "#30363d",
        "bar": "#39d353",
        "bar_empty": "#161b22",
        "accent": "#58a6ff",
    },
}

WIDTH = 960
HEIGHT = 250
BAR_TOP = 130
BAR_MAX = 74
BAR_BASE = BAR_TOP + BAR_MAX
CHART_X = 40
CHART_WIDTH = WIDTH - CHART_X * 2


def fetch_calendar() -> dict:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is required")

    payload = json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode()
    request = urllib.request.Request(
        API,
        data=payload,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "profile-activity-card",
        },
    )
    with urllib.request.urlopen(request) as response:
        body = json.load(response)

    if "errors" in body:
        raise SystemExit(body["errors"])
    return body["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def current_streak(days: list[tuple[date, int]]) -> int:
    counts = dict(days)
    cursor = max(counts)
    if counts.get(cursor, 0) == 0:
        cursor -= timedelta(days=1)

    streak = 0
    while counts.get(cursor, 0) > 0:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def busiest_month(days: list[tuple[date, int]]) -> tuple[str, int]:
    totals: dict[tuple[int, int], int] = defaultdict(int)
    for day, count in days:
        totals[(day.year, day.month)] += count

    (year, month), count = max(totals.items(), key=lambda item: item[1])
    return date(year, month, 1).strftime("%b %Y"), count


def stat(x: int, value: str, label: str, theme: dict) -> str:
    return (
        f'  <text x="{x}" y="82" class="stat">{value}</text>\n'
        f'  <text x="{x}" y="102" class="stat-label">{label}</text>'
    )


def render(theme_name: str, theme: dict, calendar: dict) -> str:
    days = [
        (date.fromisoformat(day["date"]), day["contributionCount"])
        for week in calendar["weeks"]
        for day in week["contributionDays"]
    ]
    weeks = [
        (week["firstDay"], sum(day["contributionCount"] for day in week["contributionDays"]))
        for week in calendar["weeks"]
    ]

    peak = max(total for _, total in weeks) or 1
    slot = CHART_WIDTH / len(weeks)
    bar_width = max(4.0, slot - 5)

    bars = []
    ticks = []
    seen_months = set()
    for index, (first_day, total) in enumerate(weeks):
        x = CHART_X + slot * index
        if total:
            height = max(4.0, BAR_MAX * total / peak)
            bars.append(
                f'  <rect x="{x:.1f}" y="{BAR_BASE - height:.1f}" width="{bar_width:.1f}" '
                f'height="{height:.1f}" rx="2" fill="{theme["bar"]}" class="bar" '
                f'style="animation-delay: {index * 0.018:.3f}s"><title>{first_day}: {total}</title></rect>'
            )

        month = date.fromisoformat(first_day).strftime("%b")
        if month not in seen_months and index % 4 == 0:
            seen_months.add(month)
            ticks.append(
                f'  <text x="{x:.1f}" y="{BAR_BASE + 22}" class="tick">{month}</text>'
            )

    month_label, month_count = busiest_month(days)
    stats = "\n".join(
        [
            stat(40, f'{calendar["totalContributions"]:,}', "CONTRIBUTIONS", theme),
            stat(300, f"{current_streak(days)}", "DAY STREAK", theme),
            stat(560, f"{month_label.upper()}", f"BUSIEST MONTH, {month_count:,} CONTRIBUTIONS", theme),
        ]
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}" role="img" aria-label="{calendar["totalContributions"]} contributions over the last 12 months">
  <style>
    .title {{ font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace; font-size: 11px; fill: {theme["muted"]}; letter-spacing: 0.16em; }}
    .stat {{ font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace; font-size: 30px; font-weight: 600; fill: {theme["text"]}; }}
    .stat-label {{ font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace; font-size: 10px; fill: {theme["muted"]}; letter-spacing: 0.12em; }}
    .tick {{ font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace; font-size: 10px; fill: {theme["muted"]}; }}
    .bar {{ transform-origin: center {BAR_BASE}px; animation: grow 0.5s ease-out backwards; }}
    @keyframes grow {{ from {{ transform: scaleY(0); }} to {{ transform: scaleY(1); }} }}
  </style>

  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="12" fill="{theme["panel"]}" stroke="{theme["border"]}" />
  <text x="40" y="40" class="title">LAST 12 MONTHS</text>
  <line x1="40" y1="56" x2="{WIDTH - 40}" y2="56" stroke="{theme["border"]}" />
  <line x1="{CHART_X}" y1="{BAR_BASE + 0.5}" x2="{CHART_X + CHART_WIDTH}" y2="{BAR_BASE + 0.5}" stroke="{theme["border"]}" />

{stats}

{chr(10).join(bars)}

{chr(10).join(ticks)}
</svg>
'''


def main() -> None:
    calendar = fetch_calendar()
    for theme_name, theme in THEMES.items():
        target = ROOT / "assets" / f"activity-{theme_name}.svg"
        target.write_text(render(theme_name, theme, calendar))
        print(f"wrote {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
