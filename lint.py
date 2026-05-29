#!/usr/bin/env python3
"""
lint.py — Rat Haven Studios site linter

ERRORS  — always exit 1:
  • Leftover {{...}} placeholder in any HTML page (forgot to run update_components.py)
  • Missing <header> or <footer> in any HTML page
  • Missing <!-- devlogs-start --> / <!-- devlogs-end --> markers in index.html

WARNINGS — exit 0 by default, exit 1 with --strict:
  • Card count in a nav page doesn't match .html file count in that directory
  • A card in a nav page links to a file that doesn't exist
  • A file in pages/devlogs|games|workshop/ has no card in its nav page
  • Devlog or workshop filename doesn't follow YYYY-MM-DD_shortname.html
  • An internal relative link resolves to a non-existent file

Usage:
    python lint.py               # run all checks
    python lint.py --strict      # warnings also cause exit 1
    python lint.py --no-links    # skip the broken-link crawl (faster)

Requires: pip install beautifulsoup4
"""

import re
import sys
import argparse
from pathlib import Path
from bs4 import BeautifulSoup

ROOT       = Path(".")
COMPONENTS = ROOT / "components"
PAGES      = ROOT / "pages"

_errors:   list[str] = []
_warnings: list[str] = []


def _err(msg: str)  -> None: _errors.append(msg)
def _warn(msg: str) -> None: _warnings.append(msg)


def _html_pages() -> list[Path]:
    files = [ROOT / "index.html"] + list(PAGES.rglob("*.html"))
    return [f for f in sorted(files) if f.exists()]


def _is_external(href: str) -> bool:
    return bool(re.match(r'^(https?://|//|mailto:|javascript:|#)', href.strip()))


def _resolve_link(from_file: Path, href: str) -> Path | None:
    href = href.strip()
    if not href or _is_external(href):
        return None
    path = re.split(r'[?#]', href)[0]
    if not path:
        return None
    return (from_file.parent / path).resolve()


def _cards_in_nav(nav_file: Path) -> list[dict]:
    soup = BeautifulSoup(nav_file.read_text(encoding="utf-8"), "html.parser")
    cards = []
    for card in soup.select(".card"):
        heading = card.find(["h2", "h3"])
        link    = heading.find("a") if heading else card.find("a")
        if link and link.get("href"):
            cards.append({"title": link.get_text(strip=True), "href": link["href"]})
    return cards


# ── Checks ────────────────────────────────────────────────────────────────────

def check_no_placeholders() -> None:
    """No page should have leftover {{...}} tokens — means update_components.py wasn't run."""
    for f in _html_pages():
        tokens = re.findall(r'\{\{[^}]+\}\}', f.read_text(encoding="utf-8"))
        if tokens:
            _err(
                f"{f.relative_to(ROOT)}  ←  leftover placeholder(s): "
                + ", ".join(dict.fromkeys(tokens))
            )


def check_components_injected() -> None:
    """Every page must have a <header> and <footer> element."""
    for f in _html_pages():
        content = f.read_text(encoding="utf-8")
        rel = f.relative_to(ROOT)
        if "<header" not in content:
            _err(f"{rel}  ←  missing <header> — run: python update_components.py")
        if "<footer" not in content:
            _err(f"{rel}  ←  missing <footer> — run: python update_components.py")


def check_devlogs_markers() -> None:
    """index.html must have devlogs-start / devlogs-end markers for build.py."""
    index = ROOT / "index.html"
    if not index.exists():
        return
    content = index.read_text(encoding="utf-8")
    if "<!-- devlogs-start -->" not in content or "<!-- devlogs-end -->" not in content:
        _err("index.html  ←  missing devlogs markers — run: python build.py")


def check_card_file_consistency() -> None:
    CONTENT_TYPES = [
        (PAGES / "nav/devlogs.html",  PAGES / "devlogs",  "devlog"),
        (PAGES / "nav/games.html",    PAGES / "games",    "game"),
        (PAGES / "nav/workshop.html", PAGES / "workshop", "workshop post"),
    ]
    for nav_file, content_dir, label in CONTENT_TYPES:
        if not nav_file.exists():
            _err(f"Missing nav file: {nav_file.relative_to(ROOT)}")
            continue
        if not content_dir.exists():
            continue

        cards = _cards_in_nav(nav_file)
        files = sorted(content_dir.glob("*.html"))

        if len(cards) != len(files):
            _warn(
                f"{nav_file.relative_to(ROOT)}  ←  {len(cards)} card(s), "
                f"but {len(files)} {label} file(s) in {content_dir.relative_to(ROOT)}/"
            )

        for card in cards:
            resolved = _resolve_link(nav_file, card["href"])
            if resolved and not resolved.exists():
                _warn(
                    f"{nav_file.relative_to(ROOT)}  ←  "
                    f'card "{card["title"]}" links to "{card["href"]}" which does not exist'
                )

        card_targets = {_resolve_link(nav_file, c["href"]) for c in cards} - {None}
        for f in files:
            if f.resolve() not in card_targets:
                _warn(
                    f"{f.relative_to(ROOT)}  ←  "
                    f"no card in {nav_file.relative_to(ROOT)} — unreachable from nav"
                )


def check_naming_convention() -> None:
    DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}_.+\.html$')
    for subdir in ("devlogs", "workshop"):
        d = PAGES / subdir
        if not d.exists():
            continue
        for f in sorted(d.glob("*.html")):
            if not DATE_RE.match(f.name):
                _warn(
                    f"pages/{subdir}/{f.name}  ←  "
                    "filename doesn't follow YYYY-MM-DD_shortname.html"
                )


def check_links() -> None:
    """Every relative internal link must resolve to an existing file."""
    for html_file in _html_pages():
        soup = BeautifulSoup(html_file.read_text(encoding="utf-8"), "html.parser")
        rel  = html_file.relative_to(ROOT)
        for tag in soup.find_all(["a", "link", "script", "img", "source"]):
            href = tag.get("href") or tag.get("src")
            if not href:
                continue
            resolved = _resolve_link(html_file, href)
            if resolved and not resolved.exists():
                _warn(f"{rel}  ←  broken link → {href}")


# ── Runner ────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rat Haven Studios site linter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--strict",   action="store_true",
                        help="Treat warnings as errors (exit 1 if any warnings exist)")
    parser.add_argument("--no-links", action="store_true",
                        help="Skip the broken-link crawl (faster)")
    args = parser.parse_args()

    print("=== Rat Haven Studios — Linter ===\n")

    check_no_placeholders()
    check_components_injected()
    check_devlogs_markers()
    check_card_file_consistency()
    check_naming_convention()
    if not args.no_links:
        check_links()

    if not _errors and not _warnings:
        print("✓  All checks passed — no issues found.")
        return 0

    if _errors:
        print("ERRORS  (must fix):")
        for msg in _errors:
            print(f"  ✗  {msg}")
        print()

    if _warnings:
        print("WARNINGS  (review recommended):")
        for msg in _warnings:
            print(f"  ⚠  {msg}")
        print()

    e, w = len(_errors), len(_warnings)
    parts = []
    if e: parts.append(f"{e} error(s)")
    if w: parts.append(f"{w} warning(s)")
    print("Found " + " and ".join(parts) + ".")

    if _errors:
        return 1
    if args.strict and _warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
