# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Do not use em dashes (—) anywhere in this project** - not in code comments, docstrings, docs, or content pages. Use a comma, period, semicolon, or parentheses instead.

## Project Overview

Static HTML/CSS website for Rat Haven Studios - a small indie game studio. All site files live directly at the project root, no `src/` or `dist/` separation. Open any `.html` file in a browser directly for local development. GitHub Actions deploys on every push to `main`.

## Scripts

```
python build.py               # sync Latest Devlogs/Workshop sections on index.html
python update_components.py   # propagate header/footer changes to all pages
python lint.py                # check for issues (run before pushing)
# lint.py requires: pip install beautifulsoup4  (or use .venv/bin/python)
```

Both `build.py` and `update_components.py` do pure text surgery (regex, no HTML parsing/reserialization): they only touch the exact block they own and never reformat anything else in a file. Neither needs `beautifulsoup4`.

**Don't run these reflexively on every change.** They exist for two narrow, infrequent cases:

- **`update_components.py`**: run this *only* after editing `components/header.html` or `components/footer.html` themselves. For a brand-new page, don't run it, just copy the `<header>`/`<footer>` block verbatim from an existing sibling page (same depth) and swap the `nav-active` class onto the right link by hand. It's plain HTML; there's no build step required for that.
- **`build.py`**: run this *only* when the newest devlog/workshop post changes what belongs in the homepage's top-3 featured cards (i.e. you just added the newest-dated post). It's fine to hand-edit the `<!-- devlogs-start -->`/`<!-- workshop-start -->` block in `index.html` directly to match instead, it's just a copy of the top 3 `.card` blocks from the nav page with `../devlogs/` etc. rewritten to `pages/devlogs/`.
- **`lint.py`**: safe to run anytime (read-only, never writes files); run before pushing.

### build.py
Updates the `<!-- devlogs-start -->` / `<!-- devlogs-end -->` and `<!-- workshop-start -->` / `<!-- workshop-end -->` blocks in `index.html` with the top 3 cards from `pages/nav/devlogs.html` / `pages/nav/workshop.html`.

### update_components.py
Reads `components/header.html` and `components/footer.html`, re-injects them into every page in place. Automatically infers `nav-active` from each file's path, do **not** set it manually. Components use `{{root}}` internally; all pages get real relative paths after injection.

### Architecture

```
index.html                           (homepage)
pages/
  nav/games.html                     (games nav, top-3 cards auto-populate homepage)
  nav/devlogs.html
  nav/workshop.html
  nav/developers.html
  games/<game>.html
  devlogs/YYYY-MM-DD_name.html
  workshop/YYYY-MM-DD_name.html
  developers/<name>.html
components/
  header.html                        (template, uses {{root}} and data-nav="...")
  footer.html                        (template, uses {{root}})
styles/styles.css
scripts/filter.js  lightbox.js  game-embed.js  gdscript-highlight.js
resources/                           (images/GIFs)
resources/workshop/                  (images for workshop posts)
CNAME
build.py
update_components.py
lint.py
requirements.txt
.github/workflows/deploy.yml
```

### Asset paths in HTML pages

All pages use real relative paths, no placeholder tokens. `index.html` uses bare paths (`styles/styles.css`, `resources/logo.png`). Depth-2 pages (`pages/*/*.html`) use `../../` prefix (`../../styles/styles.css`, `../../resources/logo.png`).

### GitHub Pages setup
Pages source must be set to **GitHub Actions** (not a branch):
Repo Settings → Pages → Build and deployment → Source → **GitHub Actions**

### Adding new content

For all three: copy an existing sibling page as the starting point, including its already-injected `<header>`/`<footer>`, just swap `class="nav-active"` onto the correct nav link if the section differs. No script run needed for this step.

**New game page** (`pages/games/<name>.html`): copy an existing game page. Use the hero layout with `.container.hero`. Asset paths use `../../` prefix. Add a card to `pages/nav/games.html` with appropriate `data-tags` (documented in a comment at the top of that file), and optionally add a featured card to `index.html#games`.

**New devlog** (`pages/devlogs/YYYY-MM-DD_shortname.html`): copy an existing devlog. Asset paths use `../../` prefix. Add a card to `pages/nav/devlogs.html` (newest first) with `data-tags`. Only if this is now the newest devlog: update `index.html`'s `<!-- devlogs-start -->` block to match (either by hand or via `python build.py`).

**New workshop post** (`pages/workshop/YYYY-MM-DD_shortname.html`): similar to devlogs, `.container` with `<h1>` title, `.card-subtitle` type/topic/date and author, content in `.post-content`. Add a card to `pages/nav/workshop.html` with `data-tags` (type: `tutorial`/`resource`/`writeup`; topic: `art`/`music`/`design`/`code`). Tags are documented in a comment at the top of that file. Images go in `resources/workshop/`. Same rule as devlogs: only touch `index.html` if this is now the newest workshop post.

### Scripts (JS)

**`scripts/filter.js`**: used by all three nav pages. Cards need `data-tags="tag1 tag2"`; filter buttons use `data-filter="tagname"` (or `"all"`). Each `.filter-group` is independent, all active filters must match.

**`scripts/lightbox.js`**: click-to-enlarge for any `<img data-lightbox>`. Click overlay or press Escape to close.

**`scripts/game-embed.js`**: lazy-loads itch.io iframes. Use `<div class="game-embed-placeholder" data-src="..." data-width="..." data-height="...">` as placeholder.

## Design System

CSS custom properties in `:root` (`styles/styles.css:6-17`):
- Colors: dark navy bg (`--bg`, `--surface`, `--surface-2`), cyan accent (`--accent: #4fc3f7`)
- Fonts: `Press Start 2P` (headings/nav/buttons), `VT323` (body), both from Google Fonts
- Retro pixel aesthetic, keep new UI consistent

Key layout classes: `.container`, `.section`, `.grid`, `.grid-2`, `.grid-3`, `.card`, `.btn`, `.btn-grid`, `.btn-grid.grid-gap-small`, `.icon-btn.itch-btn`
