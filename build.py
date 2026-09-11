#!/usr/bin/env python3
"""
build.py: Generate card grids from the cards/ JSON files.

Reads cards/games/*.json, cards/devlogs/*.json, cards/workshop/*.json and
renders them into:

  - the <!-- cards-start --> / <!-- cards-end --> block in each of
    pages/nav/games.html, pages/nav/devlogs.html, pages/nav/workshop.html
    (all cards in that folder, newest date first)
  - the <!-- games-start --> / <!-- games-end --> block in index.html
    (only cards with a "featured_order" key, sorted by that value)
  - the <!-- devlogs-start --> / <!-- devlogs-end --> and
    <!-- workshop-start --> / <!-- workshop-end --> blocks in index.html
    (top 3 cards, newest date first)

To add a new card: drop a new .json file in the matching cards/<kind>/
folder and run this script. To remove one, delete its JSON file and run
this script again. Never hand-edit the generated blocks, edit the JSON
and rerun.

Every card has a "variant" field ("game" or "post") that picks which
shape it renders as, independent of which cards/<kind>/ folder it lives
in (see _RENDERERS below). Card JSON stores "page"/"cover" paths
root-relative (e.g. "pages/games/foo.html", "resources/games/foo/cover.png").
This script rewrites them (including any internal links inside
"description_html") to be relative to whichever file it's writing into.
"""

import json
import posixpath
import re
import sys
from pathlib import Path

ROOT  = Path(__file__).parent
CARDS = ROOT / "cards"
INDEX = ROOT / "index.html"

NAV_FILES = {
    "games":    ROOT / "pages" / "nav" / "games.html",
    "devlogs":  ROOT / "pages" / "nav" / "devlogs.html",
    "workshop": ROOT / "pages" / "nav" / "workshop.html",
}
NAV_FROM_DIR = "pages/nav"
INDEX_FROM_DIR = "."

_INTERNAL_HREF_RE = re.compile(r'href="(pages/[^"]+)"')


def load_cards(kind: str) -> list[dict]:
    cards = []
    for f in sorted((CARDS / kind).glob("*.json")):
        cards.append(json.loads(f.read_text(encoding="utf-8")))
    cards.sort(key=lambda c: c["date"], reverse=True)
    return cards


def _rel(path: str, from_dir: str) -> str:
    return posixpath.relpath(path, from_dir)


def _rewrite_internal_links(html: str, from_dir: str) -> str:
    return _INTERNAL_HREF_RE.sub(lambda m: f'href="{_rel(m.group(1), from_dir)}"', html)


def _render_post(card: dict, from_dir: str, home: bool, indent: str) -> str:
    page = _rel(card["page"], from_dir)
    desc = _rewrite_internal_links(card["description_html"], from_dir)
    return (
        f'{indent}<div class="card" data-tags="{card["tags"]}">\n'
        f'{indent}  <h3><a href="{page}">{card["title"]}</a></h3>\n'
        f'{indent}  <span class="card-subtitle">{card["subtitle"]}</span>\n'
        f'{indent}  <p>{desc}</p>\n'
        f'{indent}  <a href="{page}" class="btn">Read</a>\n'
        f'{indent}</div>'
    )


def _render_game(card: dict, from_dir: str, home: bool, indent: str) -> str:
    page = _rel(card["page"], from_dir)
    cover = _rel(card["cover"], from_dir)
    icon = _rel("resources/icons/itch-icon.svg", from_dir)
    desc = _rewrite_internal_links(card["description_html"], from_dir)
    tags_attr = "" if home else f' data-tags="{card["tags"]}"'
    return "\n".join([
        f'{indent}<div class="card"{tags_attr}>',
        f'{indent}  <a class="card-img" href="{page}">',
        f'{indent}    <img src="{cover}" alt="{card["cover_alt"]}" />',
        f'{indent}  </a>',
        f'{indent}  <h3><a href="{page}">{card["title"]}</a></h3>',
        f'{indent}  <span class="card-subtitle">{card["subtitle"]}</span>',
        f'{indent}  <p>{desc}</p>',
        f'{indent}  <div class="btn-grid">',
        f'{indent}    <a href="{page}" class="btn">View</a>',
        f'{indent}    <a href="{card["itch_url"]}" class="btn icon-btn itch-btn" target="_blank"><img',
        f'{indent}        src="{icon}">itch</a>',
        f'{indent}  </div>',
        f'{indent}</div>',
    ])


# Each renderer only reads the fields its own variant defines; a card's
# extra fields (e.g. a post's "tags") are only ever accessed by the
# renderer its own "variant" selects.
_RENDERERS = {
    "post": _render_post,
    "game": _render_game,
}


def _render_card(card: dict, from_dir: str, home: bool = False, indent: str = "        ") -> str:
    variant = card.get("variant")
    renderer = _RENDERERS.get(variant)
    if renderer is None:
        raise ValueError(f'card "{card.get("title")}" has unknown variant {variant!r}')
    return renderer(card, from_dir, home, indent)


def _replace_block(content: str, start: str, end: str, inner: str) -> str:
    s = content.find(start)
    e = content.find(end)
    if s == -1 or e == -1:
        raise ValueError(f"markers {start!r} / {end!r} not found")
    return content[:s + len(start)] + "\n\n" + inner + "\n\n" + content[e:]


def compute_new_contents() -> dict[Path, str]:
    """Return {path: new_full_content} for every card-driven page, computed
    from the current cards/ JSON. Does not touch disk."""
    all_cards = {kind: load_cards(kind) for kind in ("games", "devlogs", "workshop")}
    result: dict[Path, str] = {}

    for kind, path in NAV_FILES.items():
        content = path.read_text(encoding="utf-8")
        rendered = "\n\n".join(_render_card(c, NAV_FROM_DIR) for c in all_cards[kind])
        result[path] = _replace_block(content, "<!-- cards-start -->", "<!-- cards-end -->", rendered)

    content = INDEX.read_text(encoding="utf-8")

    featured_games = sorted(
        (c for c in all_cards["games"] if "featured_order" in c),
        key=lambda c: c["featured_order"],
    )
    games_html = "\n\n".join(_render_card(c, INDEX_FROM_DIR, home=True) for c in featured_games)
    content = _replace_block(content, "<!-- games-start -->", "<!-- games-end -->", games_html)

    devlogs_html = "\n\n".join(_render_card(c, INDEX_FROM_DIR, home=True) for c in all_cards["devlogs"][:3])
    content = _replace_block(content, "<!-- devlogs-start -->", "<!-- devlogs-end -->", devlogs_html)

    workshop_html = "\n\n".join(_render_card(c, INDEX_FROM_DIR, home=True) for c in all_cards["workshop"][:3])
    content = _replace_block(content, "<!-- workshop-start -->", "<!-- workshop-end -->", workshop_html)

    result[INDEX] = content
    return result


def main() -> int:
    try:
        new_contents = compute_new_contents()
    except ValueError as e:
        print(f"Error: {e}")
        return 1

    updated = []
    for path, new_content in new_contents.items():
        if path.read_text(encoding="utf-8") != new_content:
            path.write_text(new_content, encoding="utf-8")
            updated.append(str(path.relative_to(ROOT)))

    if not updated:
        print("All card-driven pages already up to date.")
    else:
        print(f"Updated: {', '.join(updated)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
