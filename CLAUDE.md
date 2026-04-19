# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Static HTML/CSS website for Rat Haven Studios - a small indie game studio. No build system, no JavaScript framework, no package manager. Open `index.html` directly in a browser to preview.

## Architecture

### Page structure and path depths

```
index.html                             (root - depth 0)
pages/nav/games.html                   (depth 2 - ../../ to root)
pages/nav/devlogs.html                 (depth 2 - ../../ to root)
pages/nav/workshop.html                (depth 2 - ../../ to root)
pages/games/<game>.html                (depth 2 - ../../ to root)
pages/devlogs/YYYY-MM-DD_name.html     (depth 2 - ../../ to root)
pages/workshop/YYYY-MM-DD_name.html    (depth 2 - ../../ to root)
styles/styles.css
scripts/filter.js
scripts/lightbox.js
scripts/game-embed.js
resources/                             (images/GIFs used in cards)
resources/workshop/                    (images for workshop posts)
```

All pages at depth 2 use `../../` for root-relative assets (CSS, logo, resources). Nav links within `pages/nav/` point to sibling files (`games.html`, `devlogs.html`, `workshop.html`); nav links from `pages/games/`, `pages/devlogs/`, and `pages/workshop/` point to `../nav/games.html` etc.

### Adding new content

**New game page** (`pages/games/<name>.html`): copy an existing game page. Use the hero layout with `.container.hero` (two columns: text left, image right). Then add a card to `pages/nav/games.html` with appropriate `data-tags` (see filter tags comment in that file), and optionally add a featured card to `index.html#games`.

**New devlog** (`pages/devlogs/YYYY-MM-DD_shortname.html`): copy the devlog template - section with `.container`, `<h1>` title, `.card-subtitle` date, content, and a "Back to Devlogs" button. Add a card to `pages/nav/devlogs.html` with `data-tags`, and update the Latest Devlogs section in `index.html`.

**New workshop post** (`pages/workshop/YYYY-MM-DD_shortname.html`): similar structure to devlogs - `.container` with `<h1>` title, `.card-subtitle` type/topic/date and author, content in `.post-content`. Add a card to `pages/nav/workshop.html` with `data-tags` (type: `tutorial`/`resource`/`writeup`; topic: `art`/`music`/`design`/`code`). Workshop nav tags are documented in an HTML comment at the top of `pages/nav/workshop.html`. Images for workshop posts go in `resources/workshop/`.

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