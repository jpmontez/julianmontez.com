# Microblog Generator

This folder contains the static site generator and site source files for the photoblog.

## Requirements
- Python `>=3.11`
- [uv](https://github.com/astral-sh/uv)

## Local Workflow
1. Install dependencies:
   `uv sync`
2. Generate site:
   `uv run generate-blog`
3. Run tests:
   `make test`
4. Run lint:
   `uv run ruff check`
5. Preview:
   `make preview`

## Generator Architecture
- `generate.py`: CLI orchestration
- `config.py`: typed site config loading/validation
- `content.py`: Markdown/front matter parsing
- `images.py`: dimension lookup, `srcset` variants, LCP selection helpers
- `render.py`: Jinja environment, page rendering, pagination build
- `feeds.py`: Atom + RSS generation
- `seo.py`: sitemap generation + robots sitemap rewrite
- `urls.py`: canonical/base/feed URL logic
- `assets.py`: dist cleanup + asset copying
- `models.py`: shared dataclasses (`SiteConfig`, `Post`, `ImageMeta`, etc.)

## Templates and Theme
- `templates/base.html`: global metadata/head, site header/footer shell
- `templates/index.html`: feed page
- `templates/post.html`: post detail page
- `templates/_macros.html`: shared image rendering macro
- `theme.css`: inlined into each generated page by default

Behavior notes:
- Header typography intentionally matches the original site style.
- Post titles are intentionally not rendered as visible headings in feed/post pages.
- Feed images and date/meta links are primary navigation affordances.
- Multi-image posts render as a horizontal strip slideshow; controls, image clicks, and keyboard arrow keys (`←`/`→`) center the active image.
- Single-image posts keep direct image linking behavior.

## Config Reference
Config file: `config.toml`

- `title`
- `tagline`
- `description`
- `author`
- `site_url`
- `base_url`
- `eager_images`
- `posts_per_page`
- `responsive_widths`
- `image_sizes`
- `feed_max_posts`
- `feed_self_url`
- `emit_style_file`

## Content and Assets
- Posts: `posts/YYYY/MM/*.md`
- Static source assets: `static/`
- Generated output: `dist/`

Front matter expectations:
- Delimiter `+++` or `++++` (matching open/close)
- ISO date (`YYYY-MM-DD`)
- `images` supports either string paths or objects with `src`/`alt`

## Output Artifacts
`dist/` contains:
- `index.html`
- `page/N/`
- `YYYY/MM/slug/`
- `static/`
- `feed.xml`
- `rss.xml`
- `sitemap.xml`
- `robots.txt`

## Deployment
CI workflow at `../.github/workflows/deploy.yml`:
- Validates on push/PR/schedule/manual
- Deploys on non-PR events to Cloudflare Pages
