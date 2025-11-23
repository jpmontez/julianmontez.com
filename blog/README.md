# Microblog Generator

Static, Tumblr-inspired microblog powered by a small Python generator. Output lives in `blog/dist`, ready to push to GitHub Pages.

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
images = ["static/my-photo.jpg"]
excerpt = "Optional short blurb for the index."
layout = "photo"
+++

Full Markdown body here. Links like [GitHub Pages](https://pages.github.com/) work as usual.
```

## Config
`blog/config.toml` controls site-level text and `base_url`. Set `base_url` if publishing under a subpath (e.g. `/julianmontez.com/blog`).

## Assets
- Place photos in `blog/static/`; they are copied to `dist/static/`.
- Theme styles live in `blog/theme.css` and are inlined into each page (also emitted as `dist/style.css`, currently unused). Google Fonts import removed to avoid render-blocking.
- Layout is fully center-aligned, with the title 64px from the top and 36px above the tagline.
- Images are lazy-loaded (`loading="lazy"`, `decoding="async"`). Posts render at `/YYYY/MM/slug/` (directory-style `index.html` inside).
