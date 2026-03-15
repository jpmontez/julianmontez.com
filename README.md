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
    PostImage.astro    # responsive <picture> with AVIF/WebP srcset
    Slideshow.astro    # multi-image horizontal slideshow
  layouts/
    BaseLayout.astro   # base HTML layout
  pages/
    index.astro        # paginated feed (page 1)
    page/[page].astro  # paginated feed (pages 2+)
    [...slug].astro    # post detail pages
    feed.xml.ts        # Atom feed
    rss.xml.ts         # RSS feed
  styles/
    theme.css          # global stylesheet
  config.ts            # site config
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
excerpt: "Optional excerpt."
location:
  name: "Prospect Park, Brooklyn, NY"
  lat: 40.66020
  lon: -73.96900
---

Optional markdown body.
```

Place the source image in `src/assets/photos/`. Astro generates responsive variants (480/720/1080px in AVIF, WebP, and JPEG) at build time.

## Lightroom Import

```bash
python scripts/import_lightroom.py [LIGHTROOM_EXPORT_DIR]
```

Imports files matching `YYYYMMDD-DSC_NNNN.jpg`, copies them to `src/assets/photos/`, and scaffolds post files in `src/content/posts/`.

## CI/CD

GitHub Actions (`.github/workflows/deploy.yml`):
- `validate`: install, type-check, build
- `deploy`: deploys `dist/` to Cloudflare Pages on non-PR pushes

Required secrets: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_PROJECT_NAME`
