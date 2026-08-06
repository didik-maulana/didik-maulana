#!/usr/bin/env python3
"""Tidy the generated 3D contribution calendars.

Two edits the action offers no settings for: the language ring, which reads as
a single "other" slice because the Actions token only sees this repository,
and the footer totals, which sit under the middle of a calendar that runs to
the right edge.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RING_ANCHOR = '<g transform="translate(40, 520)">'
FOOTER_ANCHOR = '<g><text style="font-size: 32px; font-weight: bold;"'
FOOTER_SHIFT = -272
TAG = re.compile(r"</?g\b")


def group_bounds(markup: str, start: int) -> tuple[int, int]:
    depth = 0
    for tag in TAG.finditer(markup, start):
        depth += -1 if tag.group().startswith("</") else 1
        if depth == 0:
            return start, markup.index(">", tag.end()) + 1
    raise RuntimeError("unbalanced <g>")


def strip_ring(markup: str) -> str:
    start = markup.find(RING_ANCHOR)
    if start == -1:
        return markup
    start, end = group_bounds(markup, start)
    return markup[:start] + markup[end:]


def shift_footer(markup: str) -> str:
    start = markup.find(FOOTER_ANCHOR)
    if start == -1:
        return markup
    start, end = group_bounds(markup, start)
    group = markup[start:end]
    shifted = f'<g transform="translate({FOOTER_SHIFT}, 0)">{group}</g>'
    return markup[:start] + shifted + markup[end:]


def main() -> None:
    changed = 0
    for target in sorted((ROOT / "profile-3d-contrib").glob("*.svg")):
        markup = target.read_text()
        polished = shift_footer(strip_ring(markup))
        if polished != markup:
            target.write_text(polished)
            changed += 1

    print(f"polished {changed} file(s)")
    if not changed:
        sys.exit("nothing matched, the action's markup may have changed")


if __name__ == "__main__":
    main()
