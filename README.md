# julianmontez.com microblog

Static Tumblr-style microblog generated with Python and uv. The generator builds a fully static site into `blog/dist`, ready for Cloudflare Pages or any static host.

## Quick start
1. Install deps: `uv sync`
2. Generate the site: `uv run generate-blog`
3. Preview: open `blog/dist/index.html` (or serve `blog/dist` with any static server)
4. Lint/format: `uv run ruff format` then `uv run ruff check`

## Import Lightroom photos
- Run `uv run python scripts/import_lightroom.py` (default source: `~/Desktop`; expected names: `YYYYMMDD-DSC_NNNN.jpg`).
- The script copies exports into `blog/static/` as `YYYY-MM-DD-DSC_NNNN.jpg`, leaves the Desktop originals untouched, and scaffolds posts at `blog/posts/YYYY/MM/YYYY-MM-DD-<slug>.md` with photo front matter:
  ```
  ++++
  date = YYYY-MM-DD
  images = [
    "static/YYYY-MM-DD-DSC_NNNN.jpg",
    …
  ]
  layout = "photo"
  ++++
  ```
- If multiple photos share a date, you'll be prompted for a custom slug; if a destination image already exists, you'll be prompted to overwrite (or pass `--overwrite` to skip prompts). Use `--source /path/to/dir` to scan another folder.

## Architecture & layout
- Python 3.11+, uv for env/deps; Jinja2 for templating; Markdown for post bodies; Ruff for lint/format.
- Entrypoint: `blog/generate.py` (also exposed as the `generate-blog` script).
- Templates: `blog/templates/index.html` (feed with pagination) and `blog/templates/post.html` (per-post pages).
- Styling: `blog/theme.css` is inlined into each page on build (also emitted as `dist/style.css`, currently unused); monochrome/centered Tumblr-inspired layout with lazy-loaded images.
- Config: `blog/config.toml` (title, tagline, description, optional `base_url`).
- Content: `blog/posts/YYYY/MM/` Markdown with TOML front matter; assets in `blog/static/` are copied to `dist/static/`.
- Output: `blog/dist/` with `index.html`, paginated feeds (`/page/N/`), and per-post pages at `/YYYY/MM/slug/` (directory-style `index.html` inside each slug).

## Writing posts
Place Markdown files under `blog/posts/YYYY/MM/` using dated filenames like `2024-10-12-your-slug.md`:
```markdown
+++
title = "Brooklyn Night Rain"
date = 2024-10-12
images = ["static/2024-10-12-brooklyn-night-rain.svg"]  # one or many images
excerpt = "Optional short blurb for the index."
layout = "photo"
+++

Markdown body here. Multiple paragraphs and links are supported.
```
Posts are ordered reverse-chronologically. Titles are not links; the date/meta links to the per-post page. Multi-image posts are supported.

## Decisions / Notes
- Pagination is built in (10 posts per page).
- Tagline stays visible; footer shows `© {{ now.year }}` only.
- Layout: 64px top padding on the title, 36px spacing between title and tagline; feed excerpts centered, post bodies left-aligned. Images have a subtle shadow.
- Images use `loading="lazy"`; CSS is inlined to avoid render-blocking requests; Google Fonts import removed.

## CI/CD
- GitHub Actions builds on push/PR/schedule and deploys `blog/dist` to Cloudflare Pages via `cloudflare/wrangler-action@v3`. Configure secrets: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_PROJECT_NAME`.
