#!/usr/bin/env python3
"""
build.py — Rat Haven Studios static site builder

Processes src/ → dist/:
  • Injects shared header/footer from src/components/
  • Infers nav-active from each file's path (no per-page annotation needed)
  • Auto-populates the Latest Devlogs section on index.html from the top 3
    cards in src/pages/nav/devlogs.html (keep that file newest-first)
  • Copies all non-HTML files (CSS, JS, images, CNAME) unchanged

Usage:
    python build.py

Output goes to dist/ (created fresh on every run).
Requires: pip install beautifulsoup4
"""

import shutil
from pathlib import Path

from bs4 import BeautifulSoup

SRC        = Path("src")
DIST       = Path("dist")
COMPONENTS = SRC / "components"

# ---------------------------------------------------------------------------
# Nav-active inference
# ---------------------------------------------------------------------------

# Ordered rules — first match wins.
# Each entry is (path-fragment, nav-key).
_NAV_RULES: list[tuple[str, str]] = [
    ("pages/nav/games",      "games"),
    ("pages/nav/devlogs",    "devlogs"),
    ("pages/nav/workshop",   "workshop"),
    ("pages/nav/developers", "developers"),
    ("pages/games/",         "games"),
    ("pages/devlogs/",       "devlogs"),
    ("pages/workshop/",      "workshop"),
    ("pages/developers/",    "developers"),
]


def _infer_nav_active(src_path: Path) -> str:
    posix = src_path.as_posix()
    for fragment, key in _NAV_RULES:
        if fragment in posix:
            return key
    return "home"


def _root_prefix(src_path: Path) -> str:
    """Return '' for root-level files, '../../' for files two dirs deep."""
    depth = len(src_path.relative_to(SRC).parts) - 1
    return "../../" if depth >= 2 else ""


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------


def _render_header(template: str, root: str, active_key: str) -> str:
    """
    1. Substitute {{root}} with the correct relative prefix.
    2. Add class="nav-active" to the <a data-nav="…"> that matches active_key.
    3. Strip all data-nav attributes so they don't appear in the output.
    """
    html = template.replace("{{root}}", root)
    soup = BeautifulSoup(html, "html.parser")

    for a in soup.find_all("a", attrs={"data-nav": True}):
        if a["data-nav"] == active_key:
            classes = a.get("class", [])
            a["class"] = classes + ["nav-active"]
        del a["data-nav"]

    # Use .find("header") so we never accidentally include stray html/body wrappers
    tag = soup.find("header")
    return str(tag) if tag else str(soup)


def _render_footer(template: str, root: str) -> str:
    return template.replace("{{root}}", root)


def _extract_top_cards(devlogs_html: str, count: int) -> str:
    """Return the first *count* .card elements from devlogs.html as HTML."""
    soup = BeautifulSoup(devlogs_html, "html.parser")
    cards = soup.select(".card")[:count]
    return "\n\n".join(str(c) for c in cards)


def _fix_card_paths_for_root(cards_html: str) -> str:
    """
    Cards extracted from src/pages/nav/devlogs.html use relative paths from
    that file's location (e.g. ../devlogs/, ../games/).
    Rewrite them so they work from the site root (index.html).
    """
    return (
        cards_html
        .replace('href="../devlogs/', 'href="pages/devlogs/')
        .replace('href="../games/',   'href="pages/games/')
    )


def _process_html(
    src_file: Path,
    header_tpl: str,
    footer_tpl: str,
    latest_devlogs: str,
) -> str:
    content = src_file.read_text(encoding="utf-8")
    root    = _root_prefix(src_file)
    active  = _infer_nav_active(src_file)

    # Inject components
    content = content.replace(
        "<!-- {{header}} -->", _render_header(header_tpl, root, active)
    )
    content = content.replace(
        "<!-- {{footer}} -->", _render_footer(footer_tpl, root)
    )

    # Substitute any remaining {{root}} tokens (CSS/script links in <head>)
    content = content.replace("{{root}}", root)

    # Homepage only: inject auto-generated devlog cards
    if src_file.name == "index.html" and src_file.parent == SRC:
        cards = _fix_card_paths_for_root(latest_devlogs)
        content = content.replace("<!-- {{latest-devlogs}} -->", cards)

    return content


# ---------------------------------------------------------------------------
# Build entry point
# ---------------------------------------------------------------------------


def build() -> None:
    # Fresh output directory
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()

    # Load shared component templates
    header_tpl = (COMPONENTS / "header.html").read_text(encoding="utf-8")
    footer_tpl  = (COMPONENTS / "footer.html").read_text(encoding="utf-8")

    # Extract top 3 devlog cards from the nav page
    devlogs_src    = (SRC / "pages" / "nav" / "devlogs.html").read_text(encoding="utf-8")
    latest_devlogs = _extract_top_cards(devlogs_src, 3)

    html_count = asset_count = 0

    for src_file in sorted(SRC.rglob("*")):
        if not src_file.is_file():
            continue

        # Skip component templates — they are not standalone pages
        try:
            src_file.relative_to(COMPONENTS)
            continue
        except ValueError:
            pass

        rel  = src_file.relative_to(SRC)
        dest = DIST / rel
        dest.parent.mkdir(parents=True, exist_ok=True)

        if src_file.suffix == ".html":
            dest.write_text(
                _process_html(src_file, header_tpl, footer_tpl, latest_devlogs),
                encoding="utf-8",
            )
            html_count += 1
        else:
            shutil.copy2(src_file, dest)
            asset_count += 1

    print(
        f"Build complete → {DIST}/  "
        f"({html_count} HTML pages, {asset_count} assets)"
    )


if __name__ == "__main__":
    build()
