# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Static HTML/CSS website for Rat Haven Studios - a small indie game studio. Uses a lightweight Python build system (`build.py`) that injects shared components and auto-populates dynamic sections. Source lives in `src/`; built output goes to `dist/`. GitHub Actions builds and deploys on every push to `main`.

## Build System

```
python build.py          # build src/ → dist/
# requires: pip install beautifulsoup4  (or use .venv/bin/python build.py)
```

**Source templates** live in `src/`. **Never edit files in `dist/`** — they are overwritten on every build.

### Placeholders in source templates

| Placeholder | What it becomes |
|---|---|
| `<!-- {{header}} -->` | Shared header from `src/components/header.html` |
| `<!-- {{footer}} -->` | Shared footer from `src/components/footer.html` |
| `{{root}}` | `""` for `src/index.html`, `"../../"` for all depth-2 pages |
| `<!-- {{latest-devlogs}} -->` | Top 3 `.card` elements from `src/pages/nav/devlogs.html` (index.html only) |

### nav-active
The build script automatically adds `class="nav-active"` to the correct header nav link by inferring which section a page belongs to from its path. Do **not** add `nav-active` manually in source templates.

### Architecture

```
src/
  components/
    header.html                        (shared header — uses {{root}} and data-nav="…")
    footer.html                        (shared footer — uses {{root}})
  index.html                           (depth 0 — {{root}} = "")
  pages/
    nav/games.html                     (depth 2 — {{root}} = "../../")
    nav/devlogs.html                   (depth 2 — top-3 cards here auto-populate homepage)
    nav/workshop.html
    nav/developers.html
    games/<game>.html
    devlogs/YYYY-MM-DD_name.html
    workshop/YYYY-MM-DD_name.html
    developers/<name>.html
  styles/styles.css
  scripts/filter.js  lightbox.js  game-embed.js  gdscript-highlight.js
  resources/                           (images/GIFs)
  resources/workshop/                  (images for workshop posts)
  CNAME
dist/                                  (generated — gitignored)
build.py
requirements.txt
.github/workflows/deploy.yml
```

### GitHub Pages setup
Pages source must be set to **GitHub Actions** (not a branch):  
Repo Settings → Pages → Build and deployment → Source → **GitHub Actions**

### Adding new content

**New game page** (`src/pages/games/<name>.html`): copy an existing game page. Use the hero layout with `.container.hero` (two columns: text left, image right). Use `<!-- {{header}} -->` / `<!-- {{footer}} -->` and `{{root}}` for asset paths. Add a card to `src/pages/nav/games.html` with appropriate `data-tags` (see filter tags comment in that file), and optionally add a featured card to `src/index.html#games`.

**New devlog** (`src/pages/devlogs/YYYY-MM-DD_shortname.html`): copy an existing devlog template — `<!-- {{header}} -->`, section with `.container`, `<h1>` title, `.card-subtitle` date, content, `<!-- {{footer}} -->`. Use `{{root}}` for any asset paths. Add a card to `src/pages/nav/devlogs.html` (newest first) with `data-tags`. **That's it — `index.html` Latest Devlogs auto-updates on the next build.**

**New workshop post** (`src/pages/workshop/YYYY-MM-DD_shortname.html`): similar structure to devlogs — `.container` with `<h1>` title, `.card-subtitle` type/topic/date and author, content in `.post-content`. Use `<!-- {{header}} -->` / `<!-- {{footer}} -->` and `{{root}}` for asset paths. Add a card to `src/pages/nav/workshop.html` with `data-tags` (type: `tutorial`/`resource`/`writeup`; topic: `art`/`music`/`design`/`code`). Workshop nav tags are documented in an HTML comment at the top of that file. Images go in `src/resources/workshop/`.

### Scripts

**`scripts/filter.js`** — used by all three nav pages (`games.html`, `devlogs.html`, `workshop.html`). Cards need `data-tags="tag1 tag2"`; filter buttons use `data-filter="tagname"` (or `"all"`). Each `.filter-group` is independent — all active filters must match. Tags are documented in HTML comments at the top of each nav page.

**`scripts/lightbox.js`** — adds click-to-enlarge to any `<img data-lightbox>` element. Click the overlay or press Escape to close.

**`scripts/game-embed.js`** — lazy-loads itch.io iframes. Use a `<div class="game-embed-placeholder" data-src="..." data-width="..." data-height="...">` as the placeholder; clicking it replaces the div with the iframe.

## Design System

CSS custom properties in `:root` (`styles/styles.css:6-17`):
- Colors: dark navy bg (`--bg`, `--surface`, `--surface-2`), cyan accent (`--accent: #4fc3f7`)
- Fonts: `Press Start 2P` (headings/nav/buttons), `VT323` (body) - both from Google Fonts
- Retro pixel aesthetic - keep new UI consistent

Key layout classes: `.container`, `.section`, `.grid`, `.grid-2`, `.grid-3`, `.card`, `.btn`, `.btn-grid`, `.btn-grid.grid-gap-small`, `.icon-btn.itch-btn`