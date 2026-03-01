# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Orientation

Before starting any task, read these files in order (they are the single source of truth):
1. `README.md` — project overview, setup, make targets, content format
2. `HANDOFF.md` — current state, open challenges, next steps, data conventions
3. `TODO.md` — active task queue

After completing work: update `HANDOFF.md` (what you did and what's next) and `TODO.md` (mark done, add new). Only update `README.md` if user-facing setup or commands changed.

## Commands

```bash
make build          # install deps + generate site
make preview        # build with preview URL overrides + serve on http://localhost:8080
make test           # run unit tests
make check          # format + lint (ruff)
make regen          # clean dist + rebuild
make import         # import Lightroom JPG exports (see README)

# Run a single test file
uv run python -m unittest tests/test_content.py

# Run a single test case
uv run python -m unittest tests.test_content.TestFrontMatter.test_parse_toml
```

## Architecture

This is a **pure Python static site generator** — no web framework. The build pipeline runs in `blog/generate.py` and calls modules in sequence:

```
config.py   → load + validate blog/config.toml
content.py  → parse Markdown posts with TOML front matter from blog/posts/YYYY/MM/*.md
images.py   → generate responsive variants (AVIF/WebP/original) using Pillow; incremental via .image-manifest.json
render.py   → render Jinja2 templates (blog/templates/) into blog/dist/ with pagination
feeds.py    → generate feed.xml (Atom) and rss.xml
seo.py      → generate sitemap.xml and robots.txt
assets.py   → copy blog/static/ → blog/dist/static/
urls.py     → shared helpers for canonical URL composition
models.py   → shared dataclasses (Post, ImageVariant, etc.)
```

**Key architectural facts:**
- CSS is inlined into HTML by default (`emit_style_file = false` in config); the stylesheet lives in `blog/theme.css`
- Post titles are intentionally hidden in rendered output; visible only in metadata/feeds
- Multi-image posts render as a horizontal slideshow; single-image posts keep the same click behavior (no file navigation)
- `blog/config.toml` controls `site_url` (canonical origin for absolute URLs), `eager_images` (LCP optimization), and `responsive_widths`

## Content Format

Posts live at `blog/posts/YYYY/MM/YYYY-MM-DD-slug.md` with TOML front matter:

```markdown
+++
date = 2024-10-12
title = "Optional title"
images = [
  { src = "static/2024-10-12-photo.jpg", alt = "Alt text." },
]
location = { name = "Prospect Park, Brooklyn, NY", lat = 40.66020, lon = -73.96900 }
+++

Markdown body.
```

- Front matter delimiter must match: `+++` or `++++`
- `location` accepts a plain string or `{ name, lat, lon }` table
- Image assets live in `blog/static/` and are referenced from front matter as `static/filename.jpg`

## Testing

Tests use Python's built-in `unittest`. Test files mirror module names (`tests/test_images.py` → `blog/images.py`). `tests/test_snapshots.py` does golden-file HTML regression testing against `tests/snapshots/`.

## Deployment

Push to `main` triggers the GitHub Actions workflow in `.github/workflows/deploy.yml`:
- `validate` job: test + lint + build
- `deploy` job: deploys `blog/dist/` to Cloudflare Pages (non-PR events only)
