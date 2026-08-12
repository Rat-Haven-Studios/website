# Rat Haven Studios

Static HTML/CSS site for Rat Haven Studios, an indie game studio. No build step, no framework, just open any `.html` file directly in a browser. Deploys via GitHub Actions on push to `main`.

## Scripts

- **`build.py`**: copies the top 3 devlog/workshop cards into `index.html`.
- **`update_components.py`**: re-injects `components/header.html` / `footer.html` into every page.
- **`lint.py`**: checks the site for broken links and other issues.

Run `python <script>.py` from the project root. See `CLAUDE.md` for when each one actually needs to run.
