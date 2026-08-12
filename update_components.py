#!/usr/bin/env python3
"""
update_components.py: Propagate header/footer changes to all pages.

Run this ONLY after editing components/header.html or components/footer.html.
You do not need to run it after creating a new page, just copy the header/footer
block from an existing sibling page (they're plain HTML, no build step needed).

Rewrites every HTML page in place; skips files where nothing changed.
Does pure text substitution, never reparses or reformats your HTML, so
whatever indentation/style you use in the component files is preserved exactly.
"""

import re
import sys
from pathlib import Path

ROOT       = Path(__file__).parent
COMPONENTS = ROOT / "components"
PAGES      = ROOT / "pages"

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

_HEADER_RE = re.compile(r'<header\b[^>]*>.*?</header>', re.DOTALL)
_FOOTER_RE = re.compile(r'<footer\b[^>]*>.*?</footer>', re.DOTALL)


def _root_prefix(file_path: Path) -> str:
    depth = len(file_path.relative_to(ROOT).parts) - 1
    return "../../" if depth >= 2 else ""


def _infer_nav_active(file_path: Path) -> str:
    posix = file_path.relative_to(ROOT).as_posix()
    for fragment, key in _NAV_RULES:
        if fragment in posix:
            return key
    return "home"


_NAV_A_RE = re.compile(r'<a\b[^>]*\bdata-nav="([^"]*)"[^>]*>')


def _render_header(template: str, root: str, active_key: str) -> str:
    html = template.replace("{{root}}", root)

    def repl(m: re.Match) -> str:
        tag = re.sub(r'\s+data-nav="[^"]*"', '', m.group(0))
        if m.group(1) == active_key:
            tag = tag.replace('<a ', '<a class="nav-active" ', 1)
        return tag

    return _NAV_A_RE.sub(repl, html)


def _render_footer(template: str, root: str) -> str:
    return template.replace("{{root}}", root)


def main() -> int:
    header_tpl = (COMPONENTS / "header.html").read_text(encoding="utf-8")
    footer_tpl = (COMPONENTS / "footer.html").read_text(encoding="utf-8")

    pages = [ROOT / "index.html"] + list(PAGES.rglob("*.html"))
    updated = skipped = 0

    for f in sorted(pages):
        if not f.exists():
            continue
        content = f.read_text(encoding="utf-8")
        root    = _root_prefix(f)
        active  = _infer_nav_active(f)
        header  = _render_header(header_tpl, root, active)
        footer  = _render_footer(footer_tpl, root)
        out = _HEADER_RE.sub(lambda m: header, content)
        out = _FOOTER_RE.sub(lambda m: footer, out)
        if out == content:
            skipped += 1
        else:
            f.write_text(out, encoding="utf-8")
            print(f"  updated  {f.relative_to(ROOT)}")
            updated += 1

    print(f"\n{updated} file(s) updated, {skipped} unchanged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
