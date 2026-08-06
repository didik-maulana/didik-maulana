#!/usr/bin/env python3
"""Render assets/stack-{light,dark}.svg.

Icons are inlined rather than linked: an SVG loaded through an <img> tag runs
in secure static mode, so any external reference it holds is dropped and the
icons would render blank.

Devicon supplies the full-colour marks. Their gradients all declare id="a", so
every icon gets its ids namespaced before being nested, otherwise the last
definition wins and earlier icons render with the wrong fill. Marks that are
black in Devicon come from Simple Icons instead, coloured per theme, so they
stay visible on both backgrounds.
"""

import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEVICON_URL = "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/{path}.svg"
SIMPLE_URL = "https://cdn.simpleicons.org/{slug}/{color}"

GROUPS = [
    {
        "title": "MOBILE",
        "x": 30,
        "y": 40,
        "width": 440,
        "items": [
            ("Swift", {"devicon": "swift/swift-original"}),
            ("Kotlin", {"devicon": "kotlin/kotlin-original"}),
            ("Flutter", {"devicon": "flutter/flutter-original"}),
            ("Dart", {"devicon": "dart/dart-original"}),
            ("React Native", {"devicon": "react/react-original"}),
        ],
    },
    {
        "title": "FRONTEND",
        "x": 510,
        "y": 40,
        "width": 420,
        "items": [
            ("TypeScript", {"devicon": "typescript/typescript-original"}),
            ("React", {"devicon": "react/react-original"}),
            ("Next.js", {"simple": "nextdotjs", "light": "000000", "dark": "FFFFFF"}),
            ("Astro", {"simple": "astro", "light": "BC52EE", "dark": "C58AF9"}),
            ("Vite", {"devicon": "vitejs/vitejs-original"}),
            ("Tailwind", {"devicon": "tailwindcss/tailwindcss-original"}),
        ],
    },
    {
        "title": "BACKEND",
        "x": 340,
        "y": 280,
        "width": 280,
        "items": [
            ("Node.js", {"devicon": "nodejs/nodejs-original"}),
            ("Express.js", {"simple": "express", "light": "000000", "dark": "FFFFFF"}),
        ],
    },
    {
        "title": "DATABASE",
        "x": 270,
        "y": 470,
        "width": 420,
        "items": [
            ("Postgres", {"devicon": "postgresql/postgresql-original"}),
            ("Supabase", {"devicon": "supabase/supabase-original"}),
            ("Firebase", {"devicon": "firebase/firebase-plain"}),
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
    },
    "dark": {
        "text": "#e6edf3",
        "muted": "#8b949e",
        "panel": "#0d1117",
        "border": "#30363d",
        "wire_mobile": "#F05138",
        "wire_frontend": "#58A6FF",
        "wire_data": "#79C0FF",
    },
}

PANEL_HEIGHT = 150
ICON_SIZE = 34


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
    with urllib.request.urlopen(request) as response:
        return response.read().decode()


def namespace_ids(markup: str, prefix: str) -> str:
    for identifier in set(re.findall(r'id="([^"]+)"', markup)):
        unique = f"{prefix}-{identifier}"
        markup = markup.replace(f'id="{identifier}"', f'id="{unique}"')
        markup = markup.replace(f"url(#{identifier})", f"url(#{unique})")
        markup = markup.replace(f'href="#{identifier}"', f'href="#{unique}"')
    return markup


def inline_icon(markup: str, prefix: str, x: float, y: float) -> str:
    root = re.search(r"<svg[^>]*>", markup).group()
    view_box = re.search(r'viewBox="([^"]+)"', root).group(1)
    root_fill = re.search(r'\sfill="([^"]+)"', root)
    fill = f' fill="{root_fill.group(1)}"' if root_fill else ""
    inner = re.sub(r"^.*?<svg[^>]*>", "", markup, count=1, flags=re.S)
    inner = re.sub(r"</svg>\s*$", "", inner, flags=re.S)
    inner = re.sub(r"<title>.*?</title>", "", inner, flags=re.S)
    inner = namespace_ids(inner, prefix)
    return (
        f'  <svg x="{x:.1f}" y="{y}" width="{ICON_SIZE}" height="{ICON_SIZE}" '
        f'viewBox="{view_box}"{fill}>{inner.strip()}</svg>'
    )


def icon_markup(spec: dict, theme_name: str) -> str:
    if "devicon" in spec:
        return fetch(DEVICON_URL.format(path=spec["devicon"]))
    return fetch(SIMPLE_URL.format(slug=spec["simple"], color=spec[theme_name]))


def panel(group: dict, theme_name: str, icons: dict) -> str:
    items = group["items"]
    step = group["width"] / len(items)
    parts = [
        f'  <rect x="{group["x"]}" y="{group["y"]}" width="{group["width"]}" '
        f'height="{PANEL_HEIGHT}" rx="12" class="panel" />',
        f'  <text x="{group["x"] + 20}" y="{group["y"] + 30}" class="title">{group["title"]}</text>',
    ]
    for index, (label, _) in enumerate(items):
        center = group["x"] + step * (index + 0.5)
        slug = re.sub(r"[^a-z0-9]", "", label.lower())
        parts.append(
            inline_icon(
                icons[theme_name][label],
                f"{slug}-{group['title'].lower()}",
                center - ICON_SIZE / 2,
                group["y"] + 52,
            )
        )
        parts.append(
            f'  <text x="{center:.1f}" y="{group["y"] + 116}" class="label" '
            f'text-anchor="middle">{label}</text>'
        )
    return "\n".join(parts)


def render(theme_name: str, theme: dict, icons: dict) -> str:
    body = "\n\n".join(panel(group, theme_name, icons) for group in GROUPS)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 660" width="960" height="660" role="img" aria-label="Mobile and frontend clients calling a Node.js and Express.js backend, backed by Postgres, Supabase, and Firebase">
  <style>
    .title {{ font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace; font-size: 11px; fill: {theme["muted"]}; letter-spacing: 0.16em; }}
    .label {{ font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace; font-size: 11px; fill: {theme["text"]}; }}
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
    icons = {
        theme_name: {
            label: icon_markup(spec, theme_name)
            for group in GROUPS
            for label, spec in group["items"]
        }
        for theme_name in THEMES
    }

    for theme_name, theme in THEMES.items():
        target = ROOT / "assets" / f"stack-{theme_name}.svg"
        target.write_text(render(theme_name, theme, icons))
        print(f"wrote {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
