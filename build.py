#!/usr/bin/env python3
"""
build.py: Sync the Latest Devlogs and Workshop sections on index.html.

Reads the top 3 cards from pages/nav/devlogs.html and pages/nav/workshop.html
(newest first) and rewrites the <!-- devlogs-start --> … <!-- devlogs-end -->
and <!-- workshop-start --> … <!-- workshop-end --> blocks in index.html in
place.

Run this ONLY when a new devlog/workshop card changes what belongs in the
homepage's top-3 (i.e. you added the newest post). Editing existing card text
doesn't require a rebuild; index.html only mirrors the top 3 cards' raw HTML.

Does pure text extraction, never reparses or reformats the cards, so
whatever indentation/style is in the nav page is carried over exactly.
"""

import re
import sys
from pathlib import Path

ROOT     = Path(__file__).parent
INDEX    = ROOT / "index.html"
DEVLOGS  = ROOT / "pages" / "nav" / "devlogs.html"
WORKSHOP = ROOT / "pages" / "nav" / "workshop.html"

_SECTIONS = [
    ("devlogs section",  DEVLOGS,  "<!-- devlogs-start -->",  "<!-- devlogs-end -->"),
    ("workshop section", WORKSHOP, "<!-- workshop-start -->", "<!-- workshop-end -->"),
]

_CARD_OPEN_RE = re.compile(r'<div class="card"[^>]*>')
_DIV_RE       = re.compile(r'<(/?)div\b')


def _top_cards(nav_file: Path, count: int = 3) -> str:
    text  = nav_file.read_text(encoding="utf-8")
    cards: list[str] = []

    for m in _CARD_OPEN_RE.finditer(text):
        if len(cards) >= count:
            break
        depth = 1
        for dm in _DIV_RE.finditer(text, m.end()):
            depth += -1 if dm.group(1) else 1
            if depth == 0:
                cards.append(text[m.start():dm.end()])
                break

    html = "\n\n".join(cards)
    # Cards are written relative to pages/nav/, rewrite hrefs for root context
    html = html.replace('href="../devlogs/',  'href="pages/devlogs/')
    html = html.replace('href="../games/',    'href="pages/games/')
    html = html.replace('href="../workshop/', 'href="pages/workshop/')
    return html


def main() -> int:
    content = INDEX.read_text(encoding="utf-8")
    original = content
    updated_labels = []

    for label, nav_file, start, end in _SECTIONS:
        s = content.find(start)
        e = content.find(end)
        if s == -1 or e == -1:
            print(f"Error: markers {start!r} / {end!r} not found in {INDEX}")
            return 1

        new_content = (
            content[:s + len(start)]
            + "\n\n" + _top_cards(nav_file) + "\n\n"
            + content[e:]
        )
        if new_content != content:
            updated_labels.append(label)
        content = new_content

    if content == original:
        print("index.html devlogs and workshop sections already up to date.")
        return 0

    INDEX.write_text(content, encoding="utf-8")
    print(f"Updated index.html: {', '.join(updated_labels)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
