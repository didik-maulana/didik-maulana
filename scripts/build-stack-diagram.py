#!/usr/bin/env python3
"""Render assets/stack-{light,dark}.svg.

Simple Icons paths are inlined rather than linked: an SVG loaded through an
<img> tag runs in secure static mode, so any external reference it holds is
dropped and the icons would render blank.
"""

import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ICON_URL = "https://cdn.simpleicons.org/{slug}"

GROUPS = [
    {
        "id": "mobile",
        "title": "MOBILE",
        "x": 30,
        "y": 40,
        "width": 440,
        "items": [
            ("swift", "Swift", "#F05138", "#F05138"),
            ("kotlin", "Kotlin", "#7F52FF", "#A371F7"),
            ("flutter", "Flutter", "#02569B", "#47C5FB"),
            ("dart", "Dart", "#0175C2", "#40C4FF"),
            ("react", "React Native", "#149ECA", "#61DAFB"),
        ],
    },
    {
        "id": "frontend",
        "title": "FRONTEND",
        "x": 510,
        "y": 40,
        "width": 420,
        "items": [
            ("typescript", "TypeScript", "#3178C6", "#3178C6"),
            ("react", "React", "#149ECA", "#61DAFB"),
            ("nextdotjs", "Next.js", "#000000", "#FFFFFF"),
            ("astro", "Astro", "#BC52EE", "#BC52EE"),
            ("vite", "Vite", "#646CFF", "#8B8FFF"),
            ("tailwindcss", "Tailwind", "#06B6D4", "#38BDF8"),
        ],
    },
    {
        "id": "backend",
        "title": "BACKEND",
        "x": 340,
        "y": 280,
        "width": 280,
        "items": [
            ("nodedotjs", "Node.js", "#5FA04E", "#7EE787"),
            ("express", "Express.js", "#000000", "#FFFFFF"),
        ],
    },
    {
        "id": "database",
        "title": "DATABASE",
        "x": 270,
        "y": 470,
        "width": 420,
        "items": [
            ("postgresql", "Postgres", "#4169E1", "#79C0FF"),
            ("supabase", "Supabase", "#3FCF8E", "#3FCF8E"),
            ("firebase", "Firebase", "#DD2C00", "#FFCA28"),
        ],
    },
]

THEMES = {
    "light": {
        "text": "#1f2328",
        "muted": "#59636e",
        "panel": "#ffffff",
        "border": "#d1d9e0",
        "wire_mobile": "#F05138",
        "wire_frontend": "#3178C6",
        "wire_data": "#4169E1",
        "color_index": 2,
    },
    "dark": {
        "text": "#e6edf3",
        "muted": "#8b949e",
        "panel": "#0d1117",
        "border": "#30363d",
        "wire_mobile": "#F05138",
        "wire_frontend": "#58A6FF",
        "wire_data": "#79C0FF",
        "color_index": 3,
    },
}

PANEL_HEIGHT = 150
ICON_SIZE = 34


def fetch_path(slug: str) -> str:
    request = urllib.request.Request(
        ICON_URL.format(slug=slug), headers={"User-Agent": "curl/8"}
    )
    with urllib.request.urlopen(request) as response:
        markup = response.read().decode()
    match = re.search(r'\sd="([^"]+)"', markup)
    if not match:
        raise RuntimeError(f"no path found for {slug}")
    return match.group(1)


def panel(group: dict, theme: dict, paths: dict) -> str:
    items = group["items"]
    step = group["width"] / len(items)
    parts = [
        f'  <rect x="{group["x"]}" y="{group["y"]}" width="{group["width"]}" '
        f'height="{PANEL_HEIGHT}" rx="12" class="panel" />',
        f'  <text x="{group["x"] + 20}" y="{group["y"] + 30}" class="title">{group["title"]}</text>',
    ]
    for index, (slug, label, *colors) in enumerate(items):
        color = colors[theme["color_index"] - 2]
        center = group["x"] + step * (index + 0.5)
        icon_x = center - ICON_SIZE / 2
        icon_y = group["y"] + 52
        scale = ICON_SIZE / 24
        parts.append(
            f'  <g transform="translate({icon_x:.1f} {icon_y}) scale({scale:.4f})" class="icon">'
            f'<path d="{paths[slug]}" fill="{color}" /></g>'
        )
        parts.append(
            f'  <text x="{center:.1f}" y="{group["y"] + 116}" class="label" '
            f'text-anchor="middle">{label}</text>'
        )
    return "\n".join(parts)


def render(theme_name: str, theme: dict, paths: dict) -> str:
    body = "\n\n".join(panel(group, theme, paths) for group in GROUPS)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 660" width="960" height="660" role="img" aria-label="Mobile, frontend, and backend stacks and how they connect">
  <style>
    .title {{ font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace; font-size: 11px; fill: {theme["muted"]}; letter-spacing: 0.16em; }}
    .label {{ font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace; font-size: 11px; fill: {theme["text"]}; }}
    .note {{ font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace; font-size: 10px; fill: {theme["muted"]}; letter-spacing: 0.08em; }}
    .panel {{ fill: {theme["panel"]}; stroke: {theme["border"]}; stroke-width: 1; }}
    .wire {{ fill: none; stroke-width: 1.5; stroke-linecap: round; stroke-dasharray: 5 9; animation: flow 1.8s linear infinite; }}
    .to-api-mobile {{ stroke: {theme["wire_mobile"]}; }}
    .to-api-frontend {{ stroke: {theme["wire_frontend"]}; animation-delay: 0.6s; }}
    .to-data {{ stroke: {theme["wire_data"]}; animation-delay: 1.2s; }}
    @keyframes flow {{ to {{ stroke-dashoffset: -28; }} }}
  </style>

{body}

  <path d="M250 190 C250 244, 400 226, 420 280" class="wire to-api-mobile" />
  <path d="M720 190 C720 244, 560 226, 540 280" class="wire to-api-frontend" />

  <path d="M480 430 L480 470" class="wire to-data" />
</svg>
'''


def main() -> None:
    slugs = {slug for group in GROUPS for slug, *_ in group["items"]}
    paths = {slug: fetch_path(slug) for slug in sorted(slugs)}
    for name, theme in THEMES.items():
        target = ROOT / "assets" / f"stack-{name}.svg"
        target.write_text(render(name, theme, paths))
        print(f"wrote {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
