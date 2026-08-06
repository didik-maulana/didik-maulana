#!/usr/bin/env python3
"""Drop the language ring from the generated 3D contribution calendars.

The action has no switch for it, and with only the Actions token available it
can see one repository, so the ring renders as a single "other" slice.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RING_ANCHOR = '<g transform="translate(40, 520)">'
TAG = re.compile(r"</?g\b")


def strip_ring(markup: str) -> str:
    start = markup.find(RING_ANCHOR)
    if start == -1:
        return markup

    depth = 0
    for tag in TAG.finditer(markup, start):
        depth += -1 if tag.group().startswith("</") else 1
        if depth == 0:
            end = markup.index(">", tag.end()) + 1
            return markup[:start] + markup[end:]

    raise RuntimeError("unbalanced <g> around the language ring")


def main() -> None:
    stripped = 0
    for target in sorted((ROOT / "profile-3d-contrib").glob("*.svg")):
        markup = target.read_text()
        cleaned = strip_ring(markup)
        if cleaned != markup:
            target.write_text(cleaned)
            stripped += 1

    print(f"stripped the language ring from {stripped} file(s)")
    if not stripped:
        sys.exit("no language ring found, the action's markup may have changed")


if __name__ == "__main__":
    main()
