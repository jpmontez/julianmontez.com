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
- Theme styles live in `blog/theme.css` and are copied to `dist/style.css`.
- Layout is fully center-aligned, with the title 64px from the top and 36px above the tagline.
