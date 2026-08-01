#!/usr/bin/env python3
"""
build.py — Sync the Latest Devlogs and Workshop sections on index.html.

Reads the top 3 cards from pages/nav/devlogs.html and pages/nav/workshop.html
(newest first) and rewrites the <!-- devlogs-start --> … <!-- devlogs-end -->
and <!-- workshop-start --> … <!-- workshop-end --> blocks in index.html in
place.

Run this after adding a new devlog or workshop card to its nav page.

Requires: pip install beautifulsoup4
"""

import sys
from pathlib import Path
from bs4 import BeautifulSoup

ROOT     = Path(__file__).parent
INDEX    = ROOT / "index.html"
DEVLOGS  = ROOT / "pages" / "nav" / "devlogs.html"
WORKSHOP = ROOT / "pages" / "nav" / "workshop.html"

_SECTIONS = [
    ("devlogs section",  DEVLOGS,  "<!-- devlogs-start -->",  "<!-- devlogs-end -->"),
    ("workshop section", WORKSHOP, "<!-- workshop-start -->", "<!-- workshop-end -->"),
]


def _top_cards(nav_file: Path, count: int = 3) -> str:
    soup  = BeautifulSoup(nav_file.read_text(encoding="utf-8"), "html.parser")
    cards = soup.select(".card")[:count]
    html  = "\n\n".join(str(c) for c in cards)
    # Cards are written relative to pages/nav/ — rewrite hrefs for root context
    html  = html.replace('href="../devlogs/',  'href="pages/devlogs/')
    html  = html.replace('href="../games/',    'href="pages/games/')
    html  = html.replace('href="../workshop/', 'href="pages/workshop/')
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
