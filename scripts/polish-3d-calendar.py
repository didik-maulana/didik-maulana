#!/usr/bin/env python3
"""Tidy the generated 3D contribution calendars.

Three edits the action offers no settings for: the language ring, which reads
as a single "other" slice because the Actions token only sees this repository,
the footer totals, which sit under the middle of a calendar that runs to the
right edge, and the missing space below them.

Every edit is marked and skipped on a second pass, so running this over
already-polished files leaves them alone rather than shifting them twice.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RING_ANCHOR = '<g transform="translate(40, 520)">'
FOOTER_ANCHOR = '<g><text style="font-size: 32px; font-weight: bold;"'
FOOTER_MARK = 'data-polish="footer"'
PADDING_MARK = 'data-polish="padding"'
FOOTER_SHIFT_X = -310
FOOTER_SHIFT_Y = 28
DATE_LABEL = re.compile(r'<text[^>]*dominant-baseline="hanging"[^>]*>[^<]*</text>')
BOTTOM_PADDING = 40
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
    if FOOTER_MARK in markup:
        return markup

    start = markup.find(FOOTER_ANCHOR)
    if start == -1:
        return markup

    start, end = group_bounds(markup, start)
    group = markup[start:end]

    date_label = DATE_LABEL.search(group)
    kept = DATE_LABEL.sub("", group) if date_label else group
    trailing = date_label.group() if date_label else ""

    wrapper = f'<g {FOOTER_MARK} transform="translate({FOOTER_SHIFT_X}, {FOOTER_SHIFT_Y})">'
    return markup[:start] + wrapper + kept + "</g>" + trailing + markup[end:]


def add_bottom_padding(markup: str) -> str:
    if PADDING_MARK in markup:
        return markup

    root = re.search(r"<svg[^>]*>", markup).group()
    width = int(re.search(r'width="(\d+)"', root).group(1))
    height = int(re.search(r'height="(\d+)"', root).group(1))
    grown = height + BOTTOM_PADDING

    patched = root.replace(f'height="{height}"', f'height="{grown}"')
    patched = patched.replace(f"0 0 {width} {height}", f"0 0 {width} {grown}")
    patched = patched.replace("<svg ", f"<svg {PADDING_MARK} ", 1)
    markup = markup.replace(root, patched, 1)

    return re.sub(
        rf'(<rect x="0" y="0" width="{width}" height=")\d+(")',
        rf"\g<1>{grown}\g<2>",
        markup,
        count=1,
    )


def main() -> None:
    changed = 0
    for target in sorted((ROOT / "profile-3d-contrib").glob("*.svg")):
        markup = target.read_text()
        polished = add_bottom_padding(shift_footer(strip_ring(markup)))
        if polished != markup:
            target.write_text(polished)
            changed += 1

    print(f"polished {changed} file(s)")
    if not changed:
        sys.exit("nothing matched, the action's markup may have changed")


if __name__ == "__main__":
    main()
