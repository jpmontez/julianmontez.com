# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Orientation

Before starting any task, read these files in order (they are the single source of truth):
1. `README.md` — project overview, setup, commands, content format
2. `TODO.md` — active task queue

After completing work: update `TODO.md` (mark done, add new). Only update `README.md` if user-facing setup or commands changed.

## Commands

```bash
# Install dependencies
npm install

# Build
npx astro build

# Preview (build + serve at http://localhost:4321)
npx astro dev

# Type check
npx astro check

# Serve built output
npx serve dist
```

## Architecture

This is an **Astro static site** — a photo-centric microblog. The build pipeline:

```
src/content.config.ts   → content collection schema (Zod) for posts
src/content/posts/      → Markdown posts with YAML front matter
src/assets/photos/      → full-resolution source images (processed at build time)
src/config.ts           → site config (title, pagination, image sizes)
src/layouts/
  BaseLayout.astro      → base HTML layout (meta, OG, preload, feeds, skip link)
src/components/
  PostImage.astro       → responsive <picture> with AVIF/WebP/native srcset
  Slideshow.astro       → multi-image horizontal slideshow with JS nav
src/pages/
  index.astro           → paginated feed (page 1)
  page/[page].astro     → paginated feed (pages 2+)
  [...slug].astro       → individual post pages at /YYYY/MM/slug/
  feed.xml.ts           → Atom/RSS feed
  rss.xml.ts            → RSS feed
src/styles/
  theme.css             → global stylesheet (inlined into all pages)
```

**Key architectural facts:**
- `src/styles/theme.css` is the single stylesheet — imported globally via BaseLayout
- Post titles are intentionally hidden in rendered output; visible only in metadata/feeds
- Multi-image posts render as a horizontal slideshow; single-image posts show a single figure
- `src/config.ts` controls title, tagline, pagination, eager image count, image sizes
- Images in `src/assets/photos/` are processed by Astro's sharp pipeline at build time

**View transitions & slideshow patterns (`src/styles/theme.css`, `src/components/Slideshow.astro`):**
- Cross-document view transitions enabled via `@view-transition { navigation: auto }` (CSS only)
- `.slideshow-track` CSS initial `transform: translateX(calc(...))` — **do not remove it**. It pre-centers slide 0 so the view-transition snapshot is correct before JS runs; removing it causes a visible jump on crossfade.
- `snapCenter()` (inline JS in `Slideshow.astro`) uses `transition: none` → `centerSlide()` → force reflow → restore transition. This pattern must be preserved for resize/load events; breakpoint formulas must exactly match the CSS initial transforms.

## Content Format

Posts live at `src/content/posts/YYYY-MM-DD-slug.md` with YAML front matter:

```markdown
---
date: 2024-10-12
title: "Optional title"
images:
  - src: ../../assets/photos/2024-10-12-photo.jpg
    alt: "Alt text."
location:
  name: "Prospect Park, Brooklyn, NY"
  lat: 40.66020
  lon: -73.96900
---

Markdown body.
```

- Image `src` paths are relative from `src/content/posts/` to `src/assets/photos/`
- `location` accepts a plain string or `{ name, lat, lon }` object
- `title` is optional and intentionally not rendered on the page

## Deployment

Push to `main` triggers the GitHub Actions workflow in `.github/workflows/deploy.yml`:
- `validate` job: `npm ci` + `astro check` + `astro build`
- `deploy` job: deploys `dist/` to Cloudflare Pages (non-PR events only)
