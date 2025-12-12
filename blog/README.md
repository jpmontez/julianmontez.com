# Microblog Generator

Static, Tumblr-inspired microblog powered by a small Python generator. Output lives in `blog/dist`, ready for Cloudflare Pages or any static host.

## Requirements
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) for dependency management

Install dependencies:
```bash
uv sync
```

Generate the site:
```bash
uv run generate-blog
```

Preview locally:
```bash
cd blog/dist && python -m http.server 8000
```

Deploy: CI builds with GitHub Actions and deploys `blog/dist` to Cloudflare Pages via `cloudflare/wrangler-action@v3` (secrets: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_PROJECT_NAME`).

## Writing posts
Add Markdown files under `blog/posts/YYYY/MM/slug.md` with TOML front matter wrapped by `++++` lines:
```markdown
+++
title = "Brooklyn Night Rain"
date = 2024-10-12
images = [
  { src = "static/my-photo.jpg", alt = "Describe the photo." },
]
excerpt = "Optional short blurb for the index."
layout = "photo"
+++

Full Markdown body here. Links like [GitHub Pages](https://pages.github.com/) work as usual.
```

## Config
`blog/config.toml` controls site-level text plus:
- `site_url` (optional): your public origin (e.g. `https://julianmontez.com`) to emit absolute canonical/OG URLs and absolute sitemap locs.
- `base_url` (optional): a path prefix if publishing under a subpath (e.g. `/julianmontez.com/blog`).
- `eager_images` (optional, default: 2): how many top-of-page images load eagerly; the generator applies `fetchpriority="high"` + preload to the likely mobile LCP image among them.

## Assets
- Place photos in `blog/static/`; they are copied to `dist/static/`.
- Generator auto-creates responsive raster variants (480/720/1080 widths when smaller than the source) and emits `srcset`/`sizes`; it eagerly loads the first `eager_images` images (default: 2) and applies `fetchpriority="high"` + a preload directive to the likely mobile LCP image among them.
- Theme styles live in `blog/theme.css` and are inlined into each page (also emitted as `dist/style.css`, currently unused). Google Fonts import removed to avoid render-blocking.
- Layout is fully center-aligned, with the title 64px from the top and 36px above the tagline.
- Images below the fold are lazy-loaded (`loading="lazy"`, `decoding="async"`). Posts render at `/YYYY/MM/slug/` (directory-style `index.html` inside).
- Generator writes `dist/sitemap.xml` and ensures `dist/robots.txt` points at it.
