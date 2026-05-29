#!/usr/bin/env python3
"""
build.py — Sync the Latest Devlogs section on index.html.

Reads the top 3 cards from pages/nav/devlogs.html and rewrites the
<!-- devlogs-start --> … <!-- devlogs-end --> block in index.html in place.

Run this after adding a new devlog card to pages/nav/devlogs.html.

Requires: pip install beautifulsoup4
"""

import sys
from pathlib import Path
from bs4 import BeautifulSoup

ROOT    = Path(__file__).parent
INDEX   = ROOT / "index.html"
DEVLOGS = ROOT / "pages" / "nav" / "devlogs.html"

_START = "<!-- devlogs-start -->"
_END   = "<!-- devlogs-end -->"


def _top_cards(count: int = 3) -> str:
    soup  = BeautifulSoup(DEVLOGS.read_text(encoding="utf-8"), "html.parser")
    cards = soup.select(".card")[:count]
    html  = "\n\n".join(str(c) for c in cards)
    # Cards are written relative to pages/nav/ — rewrite hrefs for root context
    html  = html.replace('href="../devlogs/', 'href="pages/devlogs/')
    html  = html.replace('href="../games/',   'href="pages/games/')
    return html


def main() -> int:
    content = INDEX.read_text(encoding="utf-8")
    s = content.find(_START)
    e = content.find(_END)
    if s == -1 or e == -1:
        print(f"Error: markers {_START!r} / {_END!r} not found in {INDEX}")
        return 1

    new_content = (
        content[:s + len(_START)]
        + "\n\n" + _top_cards() + "\n\n"
        + content[e:]
    )

    if new_content == content:
        print("index.html devlogs section already up to date.")
        return 0

    INDEX.write_text(new_content, encoding="utf-8")
    print("Updated index.html with latest 3 devlogs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
