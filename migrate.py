#!/usr/bin/env python3
"""
migrate.py — One-time setup

Transforms the existing HTML files into src/ templates:
  • Removes <header> and <footer> blocks and replaces them with
    <!-- {{header}} --> and <!-- {{footer}} --> placeholders
  • Replaces ../../ with {{root}} in depth-2 pages
  • Adds {{root}} prefix to asset paths in index.html
  • Replaces the 3 hardcoded devlog cards in index.html with
    <!-- {{latest-devlogs}} -->
  • Copies styles/, scripts/, resources/, CNAME into src/

Run once, then use build.py for all future builds:
    python migrate.py
    python build.py          # verify dist/ looks correct

After verifying:
    git rm index.html pages/**/*.html
    git rm -r styles/ scripts/ resources/
    git commit -m "migrate to src/ build system"
    git push
"""

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
SRC  = ROOT / "src"

_HEADER_RE = re.compile(
    r'\n?<header class="site-header">.*?</header>\n?', re.DOTALL
)
_FOOTER_RE = re.compile(
    r'\n?<footer class="site-footer">.*?</footer>\n?', re.DOTALL
)


def _replace_devlog_cards(content: str) -> str:
    """
    Replace the 3 hardcoded devlog card <div>s inside #devlogs on index.html
    with a <!-- {{latest-devlogs}} --> placeholder.

    Strategy: find the <div class="grid grid-3"> that precedes the unique
    '</div>\\n    <br>\\n    <a href="pages/nav/devlogs.html"' sequence, then
    replace its inner content.
    """
    devlogs_start = content.find('id="devlogs"')
    if devlogs_start == -1:
        print("  ⚠  Could not find id=\"devlogs\" in index.html — skipping card replacement")
        return content

    # This sequence is unique to the end of the devlogs grid
    end_marker = '\n    </div>\n    <br>\n    <a href="pages/nav/devlogs.html"'
    end_pos = content.find(end_marker, devlogs_start)
    if end_pos == -1:
        print("  ⚠  Could not locate devlogs end-marker — skipping card replacement")
        return content

    grid_open = content.rfind('<div class="grid grid-3">', devlogs_start, end_pos)
    if grid_open == -1:
        print("  ⚠  Could not locate grid-3 opening — skipping card replacement")
        return content

    grid_open_end = grid_open + len('<div class="grid grid-3">')

    return (
        content[:grid_open_end]
        + "\n\n<!-- {{latest-devlogs}} -->\n\n    "
        + content[end_pos:]
    )


def _transform(file_path: Path, content: str) -> str:
    rel   = file_path.relative_to(ROOT)
    depth = len(rel.parts) - 1   # 0 = root (index.html), 2 = pages/*/*.html

    # Remove shared header and footer blocks
    content = _HEADER_RE.sub("\n<!-- {{header}} -->\n", content)
    content = _FOOTER_RE.sub("\n<!-- {{footer}} -->\n",  content)

    if depth == 0:
        # index.html — insert {{root}} before each local asset path
        # Matches href="styles/...", src="resources/...", etc.
        content = re.sub(
            r'((?:href|src)=")(styles/|resources/|scripts/)',
            r'\1{{root}}\2',
            content,
        )
        content = _replace_devlog_cards(content)
    else:
        # All depth-2 pages — swap ../../ prefix for {{root}}
        content = content.replace("../../", "{{root}}")

    return content


def main() -> None:
    print("=== Rat Haven Studios — Migration to src/ ===\n")

    SRC.mkdir(exist_ok=True)
    (SRC / "components").mkdir(exist_ok=True)

    # ── Copy static asset directories ──────────────────────────────────────
    for name in ("styles", "scripts", "resources"):
        src_dir = ROOT / name
        dst_dir = SRC / name
        if src_dir.exists():
            if dst_dir.exists():
                shutil.rmtree(dst_dir)
            shutil.copytree(src_dir, dst_dir)
            print(f"  Copied  {name}/  →  src/{name}/")
        else:
            print(f"  (skip)  {name}/ not found at root")

    # ── Copy CNAME ──────────────────────────────────────────────────────────
    cname = ROOT / "CNAME"
    if cname.exists():
        shutil.copy2(cname, SRC / "CNAME")
        print("  Copied  CNAME  →  src/CNAME")

    print()

    # ── Transform HTML files ─────────────────────────────────────────────────
    html_files = sorted(
        [ROOT / "index.html"] + list((ROOT / "pages").rglob("*.html"))
    )
    for html_file in html_files:
        # Don't re-process files already inside src/
        if SRC in html_file.parents:
            continue
        content     = html_file.read_text(encoding="utf-8")
        transformed = _transform(html_file, content)
        dest        = SRC / html_file.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(transformed, encoding="utf-8")
        print(f"  Migrated  {html_file.relative_to(ROOT)}")

    print("\nDone!  src/ is ready.")
    print()
    print("Next steps:")
    print("  1. python build.py")
    print("  2. Open dist/index.html and verify the site")
    print("  3. Remove originals once satisfied:")
    print("     git rm index.html")
    print("     git rm -r pages/")
    print("     git rm -r styles/ scripts/ resources/")
    print("  4. Push → GitHub Actions will build & deploy automatically")


if __name__ == "__main__":
    main()
