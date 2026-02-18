# julianmontez.com microblog

Static Tumblr-style photoblog generator built with Python and uv. The site is generated into `blog/dist` and deployed as static files.

## Quick Start
1. Install dependencies:
   `uv sync`
2. Build the site:
   `uv run generate-blog`
3. Run checks:
   `make test` and `uv run ruff check`
4. Preview locally:
   `make preview` (serves `blog/dist` on `http://localhost:8080` by default)

## Make Targets
- `make install`: `uv sync`
- `make build`: install + generate site
- `make preview`: generate with preview URL overrides and serve with `uv run python -m http.server`
- `make test`: run unit tests
- `make format`: run Ruff formatter
- `make lint`: run Ruff lint checks
- `make check`: format + lint
- `make import [LIGHTROOM_EXPORT_DIR=...]`: import Lightroom JPG exports
- `make clean`: remove `blog/dist`
- `make distclean`: remove `blog/dist`, `.uv`, `.venv`
- `make regen`: clean + build

## Repository Layout
- `blog/generate.py`: CLI entrypoint (`generate-blog`)
- `blog/config.py`: config loading/validation + CLI overrides
- `blog/content.py`: post/front matter parsing
- `blog/images.py`: image metadata + responsive variant generation
- `blog/render.py`: template rendering + pagination build
- `blog/feeds.py`: Atom/RSS generation
- `blog/seo.py`: sitemap + robots rewrite
- `blog/urls.py`: URL composition helpers
- `blog/assets.py`: dist setup + static asset copy
- `blog/templates/`: Jinja templates
- `blog/static/`: source static assets
- `blog/posts/YYYY/MM/*.md`: content files
- `tests/`: unit tests

## Writing Posts
Create Markdown files under `blog/posts/YYYY/MM/`, for example `blog/posts/2024/10/2024-10-12-my-post.md`:

```markdown
+++
title = "Optional metadata title"
date = 2024-10-12
images = [
  { src = "static/2024-10-12-photo.jpg", alt = "Describe the photo." },
]
excerpt = "Optional excerpt."
layout = "photo"
+++

Markdown body content.
```

Notes:
- Front matter delimiter must be `+++` or `++++` with matching start/end.
- Dates must be ISO `YYYY-MM-DD`.
- Post titles are intentionally hidden in rendered page content; they are still used for metadata/feed context.

## Configuration
`blog/config.toml` supports:
- `title`, `tagline`, `description`, `author`
- `site_url`: canonical public origin for absolute URLs
- `base_url`: optional subpath prefix
- `eager_images`: count of above-the-fold eager-loaded images
- `posts_per_page`: feed pagination size
- `responsive_widths`: generated raster widths
- `image_sizes`: responsive `sizes` attribute value
- `feed_max_posts`: max Atom/RSS items (`0` disables entries)
- `feed_self_url`: optional feed self-link base override
- `emit_style_file`: emit `dist/style.css` in addition to inline CSS

## Lightroom Import
`scripts/import_lightroom.py` imports files matching `YYYYMMDD-DSC_NNNN.jpg`:
- Copies photos into `blog/static/` as `YYYY-MM-DD-DSC_NNNN.jpg`
- Scaffolds post files in `blog/posts/YYYY/MM/`
- Prompts for slug on same-day multi-image imports
- Prompts before overwrite unless `--overwrite` is passed

## Generated Output
`blog/dist/` includes:
- `index.html`
- `page/N/` pagination
- `YYYY/MM/slug/` post pages
- `static/` assets
- `feed.xml` (Atom) and `rss.xml`
- `sitemap.xml`
- `robots.txt`

## CI/CD
GitHub Actions workflow `.github/workflows/deploy.yml`:
- `validate` job: install, test, lint, build
- `deploy` job: runs only on non-PR events and deploys `blog/dist` to Cloudflare Pages

Required secrets:
- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`
- `CLOUDFLARE_PROJECT_NAME`
