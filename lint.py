#!/usr/bin/env python3
"""
lint.py — Rat Haven Studios site linter / consistency checker

Checks both source templates (src/) and the build output (dist/).

ERRORS  — site would be broken; always exit 1:
  • Missing <!-- {{header}} --> or <!-- {{footer}} --> in a src/ page
  • Leftover {{...}} tokens in dist/ HTML (build substitution failed)

WARNINGS — informational; exit 0 by default, exit 1 with --strict:
  • Card count in a nav page doesn't match .html file count in that directory
  • A card in a nav page links to a file that doesn't exist
  • A file in pages/devlogs|games|workshop/ has no card in its nav page
  • class="nav-active" hard-coded in a src/ template (build.py handles it)
  • Devlog or workshop filename doesn't follow YYYY-MM-DD_shortname.html
  • An internal relative link in dist/ resolves to a non-existent file

Usage:
    python lint.py                 # run all checks
    python lint.py --strict        # warnings also cause exit 1
    python lint.py --src-only      # skip dist/ checks (before first build)
    python lint.py --no-links      # skip the broken-link crawl (faster)

Requires: pip install beautifulsoup4
"""

import re
import sys
import argparse
from pathlib import Path
from bs4 import BeautifulSoup

SRC  = Path("src")
DIST = Path("dist")

_errors:   list[str] = []
_warnings: list[str] = []


def _err(msg: str)  -> None: _errors.append(msg)
def _warn(msg: str) -> None: _warnings.append(msg)


# ── Path / link helpers ───────────────────────────────────────────────────────

def _is_external(href: str) -> bool:
    return bool(re.match(r'^(https?://|//|mailto:|javascript:|#)', href.strip()))


def _resolve_link(from_file: Path, href: str) -> Path | None:
    """
    Resolve a relative href/src from from_file to an absolute Path.
    Returns None for external links, pure anchors, or empty strings.
    """
    href = href.strip()
    if not href or _is_external(href):
        return None
    # Strip query string and fragment
    path = re.split(r'[?#]', href)[0]
    if not path:
        return None
    return (from_file.parent / path).resolve()


def _cards_in_nav(nav_file: Path) -> list[dict]:
    """Return [{title, href}] for every .card found in a nav page."""
    soup = BeautifulSoup(nav_file.read_text(encoding="utf-8"), "html.parser")
    cards = []
    for card in soup.select(".card"):
        heading = card.find(["h2", "h3"])
        link    = heading.find("a") if heading else card.find("a")
        if link and link.get("href"):
            cards.append({"title": link.get_text(strip=True), "href": link["href"]})
    return cards


# ── Source checks ─────────────────────────────────────────────────────────────

def check_src_placeholders() -> None:
    """Every src/ HTML page (outside components/) must have header + footer placeholders."""
    for html_file in sorted(SRC.rglob("*.html")):
        try:
            html_file.relative_to(SRC / "components")
            continue
        except ValueError:
            pass

        content = html_file.read_text(encoding="utf-8")
        rel     = html_file.relative_to(SRC)

        if "<!-- {{header}} -->" not in content:
            _err(f"src/{rel}  ←  missing <!-- {{{{header}}}} --> placeholder")
        if "<!-- {{footer}} -->" not in content:
            _err(f"src/{rel}  ←  missing <!-- {{{{footer}}}} --> placeholder")


def check_src_no_nav_active() -> None:
    """src/ templates should not hard-code class="nav-active" — build.py adds it automatically."""
    for html_file in sorted(SRC.rglob("*.html")):
        try:
            html_file.relative_to(SRC / "components")
            continue
        except ValueError:
            pass
        content = html_file.read_text(encoding="utf-8")
        if 'class="nav-active"' in content:
            rel = html_file.relative_to(SRC)
            _warn(
                f"src/{rel}  ←  contains class=\"nav-active\"; "
                "remove it — build.py injects it from the file path"
            )


def check_card_file_consistency() -> None:
    """
    For devlogs, games, and workshop:
      1. Card count in the nav page == .html file count in the content directory.
      2. Every card href resolves to an existing src/ file.
      3. Every content file has at least one card pointing at it.
    """
    CONTENT_TYPES = [
        (SRC / "pages/nav/devlogs.html",  SRC / "pages/devlogs",  "devlog"),
        (SRC / "pages/nav/games.html",    SRC / "pages/games",    "game"),
        (SRC / "pages/nav/workshop.html", SRC / "pages/workshop", "workshop post"),
    ]

    for nav_file, content_dir, label in CONTENT_TYPES:
        if not nav_file.exists():
            _err(f"Missing nav file: src/{nav_file.relative_to(SRC)}")
            continue
        if not content_dir.exists():
            continue  # no content yet — nothing to check

        cards = _cards_in_nav(nav_file)
        files = sorted(content_dir.glob("*.html"))

        # 1. Count mismatch
        if len(cards) != len(files):
            nav_rel = nav_file.relative_to(SRC)
            dir_rel = content_dir.relative_to(SRC)
            _warn(
                f"src/{nav_rel}  ←  {len(cards)} card(s), "
                f"but {len(files)} {label} file(s) in src/{dir_rel}/"
            )

        # 2. Each card must link to a file that exists
        for card in cards:
            resolved = _resolve_link(nav_file, card["href"])
            if resolved and not resolved.exists():
                _warn(
                    f"src/{nav_file.relative_to(SRC)}  ←  "
                    f'card "{card["title"]}" links to "{card["href"]}" '
                    f"which does not exist"
                )

        # 3. Each file must have a card pointing to it
        card_targets = set()
        for card in cards:
            resolved = _resolve_link(nav_file, card["href"])
            if resolved:
                card_targets.add(resolved)

        for f in files:
            if f.resolve() not in card_targets:
                dir_name = content_dir.name
                _warn(
                    f"src/pages/{dir_name}/{f.name}  ←  "
                    f"no card in src/{nav_file.relative_to(SRC)} "
                    f"— page is unreachable from the nav"
                )


def check_naming_convention() -> None:
    """Devlog and workshop source files should follow YYYY-MM-DD_shortname.html."""
    DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}_.+\.html$')
    for subdir in ("devlogs", "workshop"):
        d = SRC / "pages" / subdir
        if not d.exists():
            continue
        for f in sorted(d.glob("*.html")):
            if not DATE_RE.match(f.name):
                _warn(
                    f"src/pages/{subdir}/{f.name}  ←  "
                    "filename doesn't follow YYYY-MM-DD_shortname.html"
                )


# ── Build output checks ───────────────────────────────────────────────────────

def check_dist_placeholders() -> None:
    """dist/ HTML files must not contain any leftover {{...}} tokens."""
    for html_file in sorted(DIST.rglob("*.html")):
        content = html_file.read_text(encoding="utf-8")
        tokens  = re.findall(r'\{\{[^}]+\}\}', content)
        if tokens:
            rel = html_file.relative_to(DIST)
            _err(
                f"dist/{rel}  ←  un-substituted placeholder(s): "
                + ", ".join(dict.fromkeys(tokens))  # deduplicated, order-preserving
            )


def check_dist_links() -> None:
    """Every relative internal link in dist/ must resolve to an existing file."""
    for html_file in sorted(DIST.rglob("*.html")):
        soup = BeautifulSoup(html_file.read_text(encoding="utf-8"), "html.parser")
        rel  = html_file.relative_to(DIST)

        for tag in soup.find_all(["a", "link", "script", "img", "source"]):
            href = tag.get("href") or tag.get("src")
            if not href:
                continue
            resolved = _resolve_link(html_file, href)
            if resolved is None:
                continue  # external or anchor — skip
            if not resolved.exists():
                _warn(f"dist/{rel}  ←  broken link → {href}")


# ── Runner ────────────────────────────────────────────────────────────────────

def _section(title: str) -> None:
    print(f"  {title}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rat Haven Studios site linter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Treat warnings as errors (exit 1 if any warnings exist)"
    )
    parser.add_argument(
        "--src-only", action="store_true",
        help="Skip dist/ checks — useful before running build.py"
    )
    parser.add_argument(
        "--no-links", action="store_true",
        help="Skip the broken-link crawl on dist/ (faster)"
    )
    args = parser.parse_args()

    print("=== Rat Haven Studios — Linter ===\n")

    # ── Source checks ────────────────────────────────────────────────────────
    print("[Source templates — src/]")

    n_before = len(_errors) + len(_warnings)
    check_src_placeholders()
    check_src_no_nav_active()
    check_card_file_consistency()
    check_naming_convention()

    src_issues = len(_errors) + len(_warnings) - n_before
    if src_issues == 0:
        print("  ✓ All source checks passed\n")
    else:
        print()  # blank line; issues will be printed in the summary below

    # ── Build output checks ──────────────────────────────────────────────────
    print("[Build output — dist/]")

    if not DIST.exists():
        print("  ⓘ  dist/ not found — skipping (run: python build.py)\n")
    elif args.src_only:
        print("  ⓘ  Skipped (--src-only)\n")
    else:
        n_before = len(_errors) + len(_warnings)
        check_dist_placeholders()
        if not args.no_links:
            check_dist_links()
        dist_issues = len(_errors) + len(_warnings) - n_before
        if dist_issues == 0:
            print("  ✓ All build-output checks passed\n")
        else:
            print()

    # ── Summary ──────────────────────────────────────────────────────────────
    if _errors:
        print("ERRORS  (must fix — site is broken):")
        for msg in _errors:
            print(f"  ✗  {msg}")
        print()

    if _warnings:
        print("WARNINGS  (review recommended):")
        for msg in _warnings:
            print(f"  ⚠  {msg}")
        print()

    if not _errors and not _warnings:
        print("✓  All checks passed — no issues found.")
        return 0

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
