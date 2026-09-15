# julianmontez.com

Static photoblog built with [Astro](https://astro.build). Deployed to Cloudflare Pages.

## Quick Start

```bash
npm install
npx astro dev        # dev server at http://localhost:4321
npx astro build      # build to dist/
npx astro check      # type-check
```

## Repository Layout

```
src/
  assets/photos/       # full-resolution source images
  content/posts/       # Markdown posts (YAML front matter)
  components/
    Feed.astro         # feed page body shared by index and page/[page]
    PostImage.astro    # responsive <picture> with AVIF/WebP srcset
    Slideshow.astro    # multi-image horizontal slideshow
  layouts/
    BaseLayout.astro   # base HTML layout
  pages/
    index.astro        # paginated feed (page 1)
    page/[page].astro  # paginated feed (pages 2+)
    [...slug].astro    # post detail pages
    feed.xml.ts        # RSS feed
    rss.xml.ts         # same feed at a legacy URL
  styles/
    theme.css          # global stylesheet
  config.ts            # site config
  utils.ts             # post and image helpers
scripts/
  import_lightroom.py  # import Lightroom JPG exports
```

## Writing Posts

Create a Markdown file in `src/content/posts/`, for example `2024-10-12-my-post.md`:

```markdown
---
date: 2024-10-12
images:
  - src: ../../assets/photos/2024-10-12-photo.jpg
    alt: "Describe the photo."
---

Optional markdown body.
```

Place the source image in `src/assets/photos/`. Astro generates responsive variants (520/640/760/1040px in AVIF, WebP, and JPEG) at build time.

## Lightroom Import

```bash
uv run scripts/import_lightroom.py [--source DIR] [--overwrite]
```

Imports files matching `YYYYMMDD-DSC_NNNN.jpg` (default source: `~/Desktop`), copies them to `src/assets/photos/`, and scaffolds post files in `src/content/posts/` with alt text written by headless Claude Code (`claude -p`), billed to your Claude Code login rather than the API. `uv` provides Python 3.14+ from the script's inline metadata; the script has no other dependencies. Requires the `claude` CLI on your PATH, logged in. If alt text generation fails, the post is still written and a warning names the image to caption by hand.

## CI/CD

GitHub Actions (`.github/workflows/deploy.yml`):
- `validate`: install, type-check, build
- `deploy`: deploys `dist/` to Cloudflare Pages on non-PR pushes

Required secrets: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_PROJECT_NAME`
