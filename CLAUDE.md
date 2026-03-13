# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Orientation

Before starting any task, read these files in order (they are the single source of truth):
1. `README.md` — project overview, setup, make targets, content format
2. `HANDOFF.md` — current state, open challenges, next steps, data conventions
3. `TODO.md` — active task queue

After completing work: update `HANDOFF.md` (what you did and what's next) and `TODO.md` (mark done, add new). Only update `README.md` if user-facing setup or commands changed.

## Commands

> **Warning:** `make` is shadowed by a broken Prezto stub in Claude Code shell sessions — never use it. Use the `uv run` equivalents below instead.

```bash
# Build
uv run generate-blog

# Preview (build + serve at http://localhost:8080)
uv run generate-blog --site-url http://localhost:8080 --feed-self-url http://localhost:8080
uv run python -m http.server 8080 -d blog/dist

# Tests
uv run python -m unittest discover -s tests

# Format + lint
uv run ruff format && uv run ruff check

# Run a single test file
uv run python -m unittest tests/test_content.py

# Run a single test case
uv run python -m unittest tests.test_content.TestFrontMatter.test_parse_toml

# Regenerate golden snapshot files after intentional HTML changes
UPDATE_SNAPSHOTS=1 uv run python -m unittest tests/test_snapshots.py
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
models.py   → shared dataclasses (Post, ImageMeta, SiteConfig, BuildPaths, etc.)
```

**Key architectural facts:**
- CSS is inlined into HTML by default (`emit_style_file = false` in config); the stylesheet lives in `blog/theme.css`
- Post titles are intentionally hidden in rendered output; visible only in metadata/feeds
- Multi-image posts render as a horizontal slideshow; single-image posts keep the same click behavior (no file navigation)
- `blog/config.toml` controls `site_url` (canonical origin for absolute URLs), `eager_images` (LCP optimization), and `responsive_widths`

**View transitions & slideshow patterns (`blog/theme.css`, `blog/templates/post.html`):**
- Cross-document view transitions enabled via `@view-transition { navigation: auto }` (CSS only)
- `.slideshow-track` CSS initial `transform: translateX(calc(...))` — **do not remove it**. It pre-centers slide 0 so the view-transition snapshot is correct before JS runs; removing it causes a visible jump on crossfade.
- `snapCenter()` (inline JS in `post.html`) uses `transition: none` → `centerSlide()` → force reflow → restore transition. This pattern must be preserved for resize/load events; breakpoint formulas must exactly match the CSS initial transforms.

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
