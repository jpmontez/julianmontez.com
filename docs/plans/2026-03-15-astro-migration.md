# Astro Migration Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate julianmontez.com from a custom Python SSG to Astro while producing a pixel-perfect 1:1 replica of the current site's UX, design, and image quality.

**Architecture:** Astro static site with Content Collections for posts (YAML frontmatter), `astro:assets` (sharp) for responsive image generation (AVIF/WebP/JPEG at 480/720/1080px + original resolution), global CSS inlined from the existing `theme.css`, and a client-side slideshow component ported from the current vanilla JS. Deployed to Cloudflare Pages via `@astrojs/cloudflare` adapter.

**Tech Stack:** Astro 5.x, TypeScript, sharp (via astro:assets), @astrojs/sitemap, @astrojs/rss, Cloudflare Pages

---

## Pre-Migration Reference

These are the critical design values and behaviors the Astro site must replicate exactly. Every task references this section.

### Design Tokens (from theme.css)

```
--bg: #ffffff (light) / #1a1a1a (dark)
--ink: #333333 / #e0e0e0
--muted: #757575 / #999999
--accent: #111111 / #f0f0f0
--shadow: 0 8px 28px rgba(0,0,0,0.11) / rgba(0,0,0,0.3)
```

- Font: `Menlo, "Andale Mono", "Courier New", monospace`, 11px, line-height 1.55
- Body text (post .body): `Helvetica, "Helvetica Neue", Arial, sans-serif`, 12.5px
- Header name: 13px, font-weight 600, letter-spacing 0.08em, uppercase
- Content max-width: 540px (`.page`)
- Photo max-width: 520px (`.post figure`)
- Post spacing: 96px margin-bottom
- Mobile font: 14px at ≤720px on touch/coarse devices

### Image Pipeline Spec

- Source: highest-resolution original JPG in `src/assets/` (never downsample the source)
- Responsive widths: 480, 720, 1080, plus original width for transcoded formats
- JPEG: quality 85, progressive, optimize (sharp equivalent: `quality: 85, progressive: true`)
- WebP: quality 80 (sharp: `quality: 80, effort: 6`)
- AVIF: quality 40 (sharp: `quality: 40`)
- `<picture>` element order: AVIF source → WebP source → native `<img>` fallback
- `sizes`: `(max-width: 720px) 100vw, 520px`
- LCP image: `fetchpriority="high"` + `<link rel="preload">` with AVIF imagesrcset
- First 2 images per page: `loading="eager"`, rest: `loading="lazy"`

### Slideshow Behavior

- Multi-image posts render a horizontal slideshow on the post detail page
- In the feed, only the first image of each post is shown (linked to the post page)
- Track: full viewport width, `display: flex`, `gap: 16px`, desktop padding 36px (28px ≤720px)
- Active slide: `opacity: 1; transform: scale(1)`, width `min(520px, 90vw)`
- Inactive slides: `opacity: 0.55; transform: scale(0.97)`
- Transition: `420ms cubic-bezier(0.22, 1, 0.36, 1)`
- Navigation: prev/next buttons (`‹` / `›`), counter (`1 / N`), click-on-slide, arrow keys, touch swipe (50px threshold, horizontal > vertical)
- On init/resize: `snapCenter()` — disable CSS transition, center slide, force reflow, restore transition
- CSS initial transforms pre-center slide 0 per breakpoint (prevents view-transition flicker):
  - Desktop (>720px): `translateX(calc(50vw - 296px))`
  - Mid (578–720px): `translateX(calc(50vw - 288px))`
  - Small (≤577px): `translateX(calc(5vw - 28px))`
- Wraps around: index modulo `slides.length`

### View Transitions

- `@view-transition { navigation: auto }` — CSS cross-document transitions
- `prefers-reduced-motion: reduce` → `animation: none` on transition pseudo-elements and slideshow

### Content Format (current → target)

Current (TOML `++++` delimiters):
```markdown
++++
date = 2026-02-21
images = [
  { src = "static/2026-02-21-DSC_0398.jpg", alt = "Alt text." },
]
layout = "photo"
++++
```

Target (YAML `---` delimiters):
```markdown
---
date: 2026-02-21
images:
  - src: ./2026-02-21-DSC_0398.jpg
    alt: "Alt text."
layout: photo
---
```

Key changes:
- TOML → YAML
- Image `src` paths change from `static/filename.jpg` to relative `./filename.jpg` (resolved by Astro's content collections from `src/content/posts/` against `src/assets/`)
- Images stored in `src/assets/photos/` (Astro processes them; `public/` images skip processing)

### URL Structure (must be preserved)

- Feed: `/`, `/page/2/`, `/page/3/`, ...
- Posts: `/YYYY/MM/YYYY-MM-DD-slug/`
- Feeds: `/feed.xml`, `/rss.xml`
- Sitemap: `/sitemap-index.xml` (Astro default, slightly different from current `/sitemap.xml`)
- Images: `/static/filename-480w.avif`, etc. (Astro manages `_astro/` output paths by default — we need to accept Astro's hashed image output paths rather than matching the exact current paths)

---

## Chunk 1: Project Scaffolding & Layout

### Task 1: Initialize Astro project alongside existing code

**Files:**
- Create: `astro.config.mjs`
- Create: `package.json`
- Create: `tsconfig.json`
- Create: `src/layouts/BaseLayout.astro`
- Create: `src/styles/theme.css` (copy from `blog/theme.css`)
- Modify: `.gitignore`

- [ ] **Step 1: Initialize Astro project**

```bash
cd /Users/julianmontez/Development/julianmontez.com
npm create astro@latest . -- --template minimal --no-install --no-git --typescript strict
```

If the interactive prompt interferes, manually create the files:

```bash
npm init -y
npm install astro @astrojs/sitemap @astrojs/rss @astrojs/cloudflare
```

- [ ] **Step 2: Configure astro.config.mjs**

```javascript
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import cloudflare from '@astrojs/cloudflare';

export default defineConfig({
  site: 'https://julianmontez.com',
  output: 'static',
  integrations: [sitemap()],
  image: {
    service: {
      entrypoint: 'astro/assets/services/sharp',
      config: {
        limitInputPixels: false,
      },
    },
  },
  vite: {
    build: {
      assetsInlineLimit: 0,
    },
  },
});
```

- [ ] **Step 3: Copy theme.css to src/styles/**

```bash
mkdir -p src/styles
cp blog/theme.css src/styles/theme.css
```

No modifications to the CSS — it must remain identical.

- [ ] **Step 4: Create BaseLayout.astro**

Port `blog/templates/base.html` to Astro. This layout must produce identical HTML structure.

```astro
---
import '../styles/theme.css';

interface Props {
  pageTitle: string;
  pageDescription: string;
  canonicalUrl: string;
  ogType?: string;
  ogImageUrl?: string;
  preloadImage?: {
    src: string;
    srcset?: string;
    avifSrcset?: string;
    sizes: string;
  };
  siteTitle: string;
  tagline: string;
  feedPrefix?: string;
  faviconUrl: string;
}

const {
  pageTitle,
  pageDescription,
  canonicalUrl,
  ogType = 'website',
  ogImageUrl,
  preloadImage,
  siteTitle,
  tagline,
  feedPrefix = '',
  faviconUrl,
} = Astro.props;

const pageUrl = canonicalUrl;
const currentYear = new Date().getFullYear();
---

<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{pageTitle}</title>
    <meta name="description" content={pageDescription} />
    <link rel="canonical" href={canonicalUrl} />
    <meta property="og:site_name" content={siteTitle} />
    <meta property="og:title" content={pageTitle} />
    <meta property="og:description" content={pageDescription} />
    <meta property="og:url" content={pageUrl} />
    <meta property="og:type" content={ogType} />
    {ogImageUrl && <meta property="og:image" content={ogImageUrl} />}
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content={pageTitle} />
    <meta name="twitter:description" content={pageDescription} />
    {ogImageUrl && <meta name="twitter:image" content={ogImageUrl} />}
    <link rel="alternate" type="application/atom+xml" title={siteTitle} href={`${feedPrefix}/feed.xml`} />
    <link rel="alternate" type="application/rss+xml" title={siteTitle} href={`${feedPrefix}/rss.xml`} />
    <link rel="icon" type="image/png" href={faviconUrl} />
    {preloadImage?.avifSrcset && (
      <link
        rel="preload"
        as="image"
        type="image/avif"
        fetchpriority="high"
        imagesrcset={preloadImage.avifSrcset}
        imagesizes={preloadImage.sizes}
      />
    )}
    {preloadImage && (
      <link
        rel="preload"
        as="image"
        href={preloadImage.src}
        fetchpriority="high"
        imagesrcset={preloadImage.srcset}
        imagesizes={preloadImage.sizes}
      />
    )}
    <slot name="head" />
  </head>
  <body>
    <a href="#main" class="skip-link">Skip to content</a>
    <div class="page">
      <header class="site">
        <span class="title"><a href="/">{siteTitle}</a></span>
        <span class="tagline">{tagline}</span>
      </header>
      <main id="main">
        <slot />
      </main>
      <footer class="footer">
        &copy; {currentYear}
      </footer>
    </div>
  </body>
</html>
```

- [ ] **Step 5: Update .gitignore**

Append Astro entries:

```
# Astro
node_modules/
dist/
.astro/
```

- [ ] **Step 6: Verify Astro dev server starts**

```bash
npx astro dev
```

Expected: dev server starts with no errors, shows the base layout at `http://localhost:4321`.

- [ ] **Step 7: Commit**

```bash
git add astro.config.mjs package.json package-lock.json tsconfig.json src/ .gitignore
git commit -m "feat: scaffold Astro project with base layout and theme CSS"
```

---

### Task 2: Create site config module

**Files:**
- Create: `src/config.ts`

The current site uses `blog/config.toml`. In Astro, we centralize config in a TypeScript module (Astro's `site` in `astro.config.mjs` handles the canonical URL; this module handles display values).

- [ ] **Step 1: Create src/config.ts**

```typescript
export const siteConfig = {
  title: 'Julian Montez',
  tagline: 'Brooklyn, NY',
  description: 'A topographical photoblog by Julian Montez',
  author: 'Julian Montez',
  postsPerPage: 10,
  eagerImages: 2,
  imageSizes: '(max-width: 720px) 100vw, 520px',
  feedMaxPosts: 25,
} as const;
```

- [ ] **Step 2: Commit**

```bash
git add src/config.ts
git commit -m "feat: add site config module"
```

---

## Chunk 2: Content Collections & Image Components

### Task 3: Set up content collection for posts

**Files:**
- Create: `src/content.config.ts`
- Create: `src/content/posts/` (directory)
- Create: conversion script `scripts/convert_posts.py`

- [ ] **Step 1: Define the content collection schema**

Create `src/content.config.ts`:

```typescript
import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const posts = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/posts' }),
  schema: ({ image }) =>
    z.object({
      date: z.coerce.date(),
      title: z.string().optional(),
      images: z
        .array(
          z.object({
            src: image(),
            alt: z.string().default('Photo'),
          })
        )
        .default([]),
      excerpt: z.string().optional(),
      layout: z.string().default('photo'),
      location: z
        .union([
          z.string(),
          z.object({
            name: z.string().optional(),
            lat: z.number().optional(),
            lon: z.number().optional(),
          }),
        ])
        .optional(),
    }),
});

export const collections = { posts };
```

- [ ] **Step 2: Write the post conversion script**

Create `scripts/convert_posts.py` — converts TOML frontmatter to YAML and adjusts image paths:

```python
"""Convert blog posts from TOML frontmatter to YAML for Astro content collections.

Reads posts from blog/posts/YYYY/MM/*.md, converts TOML frontmatter (++++ delimiters)
to YAML (--- delimiters), adjusts image src paths from "static/filename.jpg" to
relative references into src/assets/photos/, and writes to src/content/posts/.

Also copies source images from blog/static/ to src/assets/photos/.

Usage:
    python scripts/convert_posts.py
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS_SRC = ROOT / "blog" / "posts"
STATIC_SRC = ROOT / "blog" / "static"
POSTS_DST = ROOT / "src" / "content" / "posts"
ASSETS_DST = ROOT / "src" / "assets" / "photos"


def parse_toml_frontmatter(text: str) -> tuple[str, str]:
    """Return (frontmatter_body, markdown_body) from a ++++/+++-delimited post."""
    match = re.match(r"^\+{3,}\n(.*?)\n\+{3,}\n?(.*)", text, re.DOTALL)
    if not match:
        raise ValueError("No TOML frontmatter found")
    return match.group(1).strip(), match.group(2).strip()


def toml_to_yaml(toml_str: str) -> str:
    """Convert simple TOML frontmatter to YAML.

    Handles: date, title, layout, excerpt (scalars), images (array of tables),
    location (string or table with name/lat/lon).
    """
    lines: list[str] = []
    images: list[dict[str, str]] = []
    location_parts: dict[str, str] = {}
    in_images = False
    current_image: dict[str, str] = {}

    for raw_line in toml_str.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        # Detect images array
        if line.startswith("images"):
            in_images = True
            continue
        if in_images:
            if line == "]":
                if current_image:
                    images.append(current_image)
                    current_image = {}
                in_images = False
                continue
            # Parse { src = "...", alt = "..." }
            src_match = re.search(r'src\s*=\s*"([^"]*)"', line)
            alt_match = re.search(r'alt\s*=\s*"([^"]*)"', line)
            if src_match:
                src_val = src_match.group(1)
                # Convert static/filename.jpg -> ../../assets/photos/filename.jpg
                if src_val.startswith("static/"):
                    filename = src_val.split("/", 1)[1]
                    src_val = f"../../assets/photos/{filename}"
                current_image["src"] = src_val
            if alt_match:
                current_image["alt"] = alt_match.group(1)
            if line.rstrip().endswith("},") or line.rstrip().endswith("}"):
                if current_image:
                    images.append(current_image)
                    current_image = {}
            continue

        # Location as inline table
        loc_match = re.match(
            r'location\s*=\s*\{\s*name\s*=\s*"([^"]*)"'
            r'(?:,\s*lat\s*=\s*([\d.\-]+))?'
            r'(?:,\s*lon\s*=\s*([\d.\-]+))?\s*\}',
            line,
        )
        if loc_match:
            location_parts["name"] = loc_match.group(1)
            if loc_match.group(2):
                location_parts["lat"] = loc_match.group(2)
            if loc_match.group(3):
                location_parts["lon"] = loc_match.group(3)
            continue

        # Location as string
        loc_str_match = re.match(r'location\s*=\s*"([^"]*)"', line)
        if loc_str_match:
            location_parts["name"] = loc_str_match.group(1)
            continue

        # Simple key = value
        kv_match = re.match(r'(\w+)\s*=\s*(.*)', line)
        if kv_match:
            key = kv_match.group(1)
            val = kv_match.group(2).strip().strip('"')
            if key == "date":
                lines.append(f"date: {val}")
            elif key == "title":
                lines.append(f'title: "{val}"')
            elif key == "layout":
                lines.append(f"layout: {val}")
            elif key == "excerpt":
                lines.append(f'excerpt: "{val}"')

    # Emit images
    if images:
        lines.append("images:")
        for img in images:
            lines.append(f'  - src: {img.get("src", "")}')
            if "alt" in img:
                lines.append(f'    alt: "{img["alt"]}"')

    # Emit location
    if location_parts:
        if len(location_parts) == 1 and "name" in location_parts:
            lines.append(f'location: "{location_parts["name"]}"')
        else:
            lines.append("location:")
            if "name" in location_parts:
                lines.append(f'  name: "{location_parts["name"]}"')
            if "lat" in location_parts:
                lines.append(f"  lat: {location_parts['lat']}")
            if "lon" in location_parts:
                lines.append(f"  lon: {location_parts['lon']}")

    return "\n".join(lines)


def convert_all() -> None:
    POSTS_DST.mkdir(parents=True, exist_ok=True)
    ASSETS_DST.mkdir(parents=True, exist_ok=True)

    # Copy all source images to assets
    copied_images: set[str] = set()
    for img in STATIC_SRC.glob("*.jpg"):
        dst = ASSETS_DST / img.name
        if not dst.exists():
            shutil.copy2(img, dst)
            copied_images.add(img.name)
    for img in STATIC_SRC.glob("*.png"):
        dst = ASSETS_DST / img.name
        if not dst.exists():
            shutil.copy2(img, dst)
            copied_images.add(img.name)

    # Copy favicon
    favicon_src = ROOT / "blog" / "favicon.png"
    if favicon_src.exists():
        favicon_dst = Path(ROOT / "public" / "favicon.png")
        favicon_dst.parent.mkdir(parents=True, exist_ok=True)
        if not favicon_dst.exists():
            shutil.copy2(favicon_src, favicon_dst)

    # Convert posts
    converted = 0
    for md_file in sorted(POSTS_SRC.rglob("*.md")):
        text = md_file.read_text()
        try:
            toml_fm, body = parse_toml_frontmatter(text)
        except ValueError:
            print(f"  SKIP (no TOML frontmatter): {md_file}")
            continue

        yaml_fm = toml_to_yaml(toml_fm)
        output = f"---\n{yaml_fm}\n---\n"
        if body:
            output += f"\n{body}\n"

        # Write with same filename to flat directory
        dst = POSTS_DST / md_file.name
        dst.write_text(output)
        converted += 1
        print(f"  Converted: {md_file.name}")

    print(f"\nDone: {converted} posts converted, {len(copied_images)} images copied")


if __name__ == "__main__":
    convert_all()
```

- [ ] **Step 3: Run the conversion script**

```bash
python scripts/convert_posts.py
```

Expected: 11 posts converted, 13 images copied. Verify output:

```bash
ls src/content/posts/
ls src/assets/photos/
cat src/content/posts/2026-02-21-photos.md
```

Verify the converted post looks like:
```markdown
---
date: 2026-02-21
layout: photo
images:
  - src: ../../assets/photos/2026-02-21-DSC_0398.jpg
    alt: "Under a steel bridge beside a brown embankment with patchy snow and a distant skyline."
  - src: ../../assets/photos/2026-02-21-DSC_0391.jpg
    alt: "Rocky drainage area with winter grasses, scattered snow, and a small evergreen."
  - src: ../../assets/photos/2026-02-21-DSC_0390.jpg
    alt: "Blue outdoor courts in front of a long brick-and-glass apartment building on a cloudy day."
---
```

- [ ] **Step 4: Commit**

```bash
git add src/content.config.ts src/content/posts/ src/assets/photos/ public/favicon.png scripts/convert_posts.py
git commit -m "feat: add content collection schema and convert posts from TOML to YAML"
```

---

### Task 4: Create PostImage component

**Files:**
- Create: `src/components/PostImage.astro`

This replaces the `_macros.html` `render_post_image` macro. Must produce identical `<picture>` markup with AVIF/WebP sources and responsive srcset.

- [ ] **Step 1: Create PostImage.astro**

```astro
---
import { getImage } from 'astro:assets';
import type { ImageMetadata } from 'astro';
import { siteConfig } from '../config';

interface Props {
  image: ImageMetadata;
  alt: string;
  isEager?: boolean;
  isLcp?: boolean;
  linkHref?: string;
}

const { image, alt, isEager = false, isLcp = false, linkHref } = Astro.props;
const widths = [480, 720, 1080];
const sizes = siteConfig.imageSizes;

// Generate responsive variants — keeping originals as source, never upscaling
const effectiveWidths = widths.filter((w) => w < image.width);

// Native format variants (resized only, no format conversion)
const nativeVariants = await Promise.all(
  effectiveWidths.map((w) =>
    getImage({ src: image, width: w, quality: 85 })
  )
);
// Include original size as fallback
const nativeOriginal = await getImage({ src: image, width: image.width, quality: 85 });

// WebP variants (all sizes including original width)
const webpWidths = [...effectiveWidths, image.width];
const webpVariants = await Promise.all(
  webpWidths.map((w) =>
    getImage({ src: image, width: w, format: 'webp', quality: 80 })
  )
);

// AVIF variants (all sizes including original width)
const avifVariants = await Promise.all(
  webpWidths.map((w) =>
    getImage({ src: image, width: w, format: 'avif', quality: 40 })
  )
);

// Build srcset strings
const nativeSrcset = [
  ...nativeVariants.map((v) => `${v.src} ${v.attributes.width}w`),
  `${nativeOriginal.src} ${nativeOriginal.attributes.width}w`,
].join(', ');

const webpSrcset = webpVariants
  .map((v) => `${v.src} ${v.attributes.width}w`)
  .join(', ');

const avifSrcset = avifVariants
  .map((v) => `${v.src} ${v.attributes.width}w`)
  .join(', ');

const primarySrc = nativeOriginal.src;
const imgWidth = image.width;
const imgHeight = image.height;
---

<figure>
  {linkHref ? <a class="post-image-link" href={linkHref}> : null}
  <picture>
    <source type="image/avif" srcset={avifSrcset} sizes={sizes} />
    <source type="image/webp" srcset={webpSrcset} sizes={sizes} />
    <img
      src={primarySrc}
      alt={alt}
      loading={isEager ? 'eager' : 'lazy'}
      fetchpriority={isLcp ? 'high' : undefined}
      srcset={nativeSrcset}
      sizes={sizes}
      decoding="async"
      width={imgWidth}
      height={imgHeight}
    />
  </picture>
  {linkHref ? </a> : null}
</figure>
```

Note: The `<a>` tag conditional rendering in Astro requires a different pattern. Use Fragment approach:

```astro
<figure>
  {linkHref ? (
    <a class="post-image-link" href={linkHref}>
      <picture>
        <source type="image/avif" srcset={avifSrcset} sizes={sizes} />
        <source type="image/webp" srcset={webpSrcset} sizes={sizes} />
        <img
          src={primarySrc}
          alt={alt}
          loading={isEager ? 'eager' : 'lazy'}
          fetchpriority={isLcp ? 'high' : undefined}
          srcset={nativeSrcset}
          sizes={sizes}
          decoding="async"
          width={imgWidth}
          height={imgHeight}
        />
      </picture>
    </a>
  ) : (
    <picture>
      <source type="image/avif" srcset={avifSrcset} sizes={sizes} />
      <source type="image/webp" srcset={webpSrcset} sizes={sizes} />
      <img
        src={primarySrc}
        alt={alt}
        loading={isEager ? 'eager' : 'lazy'}
        fetchpriority={isLcp ? 'high' : undefined}
        srcset={nativeSrcset}
        sizes={sizes}
        decoding="async"
        width={imgWidth}
        height={imgHeight}
      />
    </picture>
  )}
</figure>
```

- [ ] **Step 2: Verify the component renders**

Create a temporary test page `src/pages/test-image.astro` that imports one photo and renders PostImage. Check the HTML output for correct `<picture>` structure. Delete the test page after verification.

- [ ] **Step 3: Commit**

```bash
git add src/components/PostImage.astro
git commit -m "feat: add PostImage component with AVIF/WebP/native responsive srcset"
```

---

### Task 5: Create Slideshow component

**Files:**
- Create: `src/components/Slideshow.astro`

Port the slideshow from `blog/templates/post.html` (lines 27–42 for markup, 88–217 for JS) and the CSS from `theme.css`. The JS must be identical in behavior.

- [ ] **Step 1: Create Slideshow.astro**

```astro
---
import PostImage from './PostImage.astro';
import type { ImageMetadata } from 'astro';

interface SlideImage {
  src: ImageMetadata;
  alt: string;
}

interface Props {
  images: SlideImage[];
  eagerCount?: number;
  lcpIndex?: number;
}

const { images, eagerCount = 2, lcpIndex = 0 } = Astro.props;
---

<section class="slideshow" aria-label="Post image slideshow" data-slideshow>
  <div class="slideshow-viewport">
    <div class="slideshow-track">
      {images.map((img, i) => (
        <div class={`slide${i === 0 ? ' is-active' : ''}`} data-slide>
          <PostImage
            image={img.src}
            alt={img.alt}
            isEager={i < eagerCount}
            isLcp={i === lcpIndex}
          />
        </div>
      ))}
    </div>
  </div>
  <div class="slideshow-nav" aria-label="Slideshow navigation">
    <button class="slideshow-control prev" type="button" aria-label="Previous photo">&#8249;</button>
    <span class="slideshow-counter" aria-live="polite">1 / {images.length}</span>
    <button class="slideshow-control next" type="button" aria-label="Next photo">&#8250;</button>
  </div>
</section>

<script>
  (function () {
    var slideshows = document.querySelectorAll("[data-slideshow]");
    if (!slideshows.length) {
      return;
    }
    var slideshowStates: any[] = [];
    var activeState: any = null;
    var isTypingTarget = function (target: any) {
      if (!target || !target.tagName) {
        return false;
      }
      if (target.isContentEditable) {
        return true;
      }
      var tag = target.tagName.toUpperCase();
      return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT";
    };
    slideshows.forEach(function (slideshow) {
      var viewport = slideshow.querySelector(".slideshow-viewport");
      var track = slideshow.querySelector(".slideshow-track") as HTMLElement;
      var slides = Array.prototype.slice.call(slideshow.querySelectorAll("[data-slide]"));
      if (slides.length <= 1) {
        return;
      }
      var prev = slideshow.querySelector(".slideshow-control.prev");
      var next = slideshow.querySelector(".slideshow-control.next");
      var state = { index: slides.findIndex(function (slide: any) {
        return slide.classList.contains("is-active");
      }), setActive: null as any };
      if (state.index < 0) {
        state.index = 0;
        slides[0].classList.add("is-active");
      }
      var centerSlide = function () {
        if (!viewport || !track) {
          return;
        }
        var slide = slides[state.index];
        var slideCenter = slide.offsetLeft + slide.offsetWidth / 2;
        var viewportCenter = (viewport as HTMLElement).clientWidth / 2;
        var translate = viewportCenter - slideCenter;
        track.style.transform = "translateX(" + translate + "px)";
      };
      var snapCenter = function () {
        track.style.transition = 'none';
        centerSlide();
        track.offsetHeight; /* force reflow */
        track.style.transition = '';
      };
      var counter = slideshow.querySelector(".slideshow-counter");
      var setActive = function (nextIndex: number) {
        slides[state.index].classList.remove("is-active");
        state.index = (nextIndex + slides.length) % slides.length;
        slides[state.index].classList.add("is-active");
        if (counter) {
          counter.textContent = (state.index + 1) + " / " + slides.length;
        }
        centerSlide();
      };
      state.setActive = setActive;
      slideshowStates.push(state);
      if (!activeState) {
        activeState = state;
      }
      var activateState = function () {
        activeState = state;
      };
      slideshow.addEventListener("pointerdown", activateState);
      slideshow.addEventListener("focusin", activateState);
      if (prev) {
        prev.addEventListener("click", function () {
          activateState();
          setActive(state.index - 1);
        });
      }
      if (next) {
        next.addEventListener("click", function () {
          activateState();
          setActive(state.index + 1);
        });
      }
      slides.forEach(function (slide: any, slideIndex: number) {
        slide.addEventListener("click", function () {
          activateState();
          setActive(slideIndex);
        });
      });
      slides.forEach(function (slide: any) {
        var img = slide.querySelector("img");
        if (img && !img.complete) {
          img.addEventListener("load", snapCenter);
        }
      });
      window.addEventListener("resize", snapCenter);
      var touchStartX = 0;
      var touchStartY = 0;
      slideshow.addEventListener("touchstart", function (e: TouchEvent) {
        touchStartX = e.changedTouches[0].clientX;
        touchStartY = e.changedTouches[0].clientY;
      }, { passive: true });
      slideshow.addEventListener("touchend", function (e: TouchEvent) {
        var dx = e.changedTouches[0].clientX - touchStartX;
        var dy = e.changedTouches[0].clientY - touchStartY;
        if (Math.abs(dx) < 50 || Math.abs(dy) > Math.abs(dx)) {
          return;
        }
        activateState();
        setActive(state.index + (dx < 0 ? 1 : -1));
      });
      snapCenter();
    });
    window.addEventListener("keydown", function (event) {
      if (event.defaultPrevented || event.metaKey || event.ctrlKey || event.altKey) {
        return;
      }
      if (isTypingTarget(event.target)) {
        return;
      }
      if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") {
        return;
      }
      var state = activeState || slideshowStates[0];
      if (!state || !state.setActive) {
        return;
      }
      event.preventDefault();
      state.setActive(state.index + (event.key === "ArrowRight" ? 1 : -1));
    });
  })();
</script>
```

- [ ] **Step 2: Commit**

```bash
git add src/components/Slideshow.astro
git commit -m "feat: add Slideshow component with touch/keyboard/click navigation"
```

---

## Chunk 3: Pages & Routing

### Task 6: Create post detail page

**Files:**
- Create: `src/pages/[...slug].astro`

This generates pages at `/YYYY/MM/YYYY-MM-DD-slug/` matching the current URL structure.

- [ ] **Step 1: Create the dynamic route**

```astro
---
import { getCollection } from 'astro:content';
import BaseLayout from '../layouts/BaseLayout.astro';
import PostImage from '../components/PostImage.astro';
import Slideshow from '../components/Slideshow.astro';
import { siteConfig } from '../config';

export async function getStaticPaths() {
  const posts = await getCollection('posts');
  return posts.map((post) => {
    const date = new Date(post.data.date);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const slug = post.id.replace(/\.md$/, '');
    return {
      params: { slug: `${year}/${month}/${slug}` },
      props: { post },
    };
  });
}

const { post } = Astro.props;
const date = new Date(post.data.date);
const displayDate = date.toLocaleDateString('en-GB', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
});

const pageTitle = post.data.title
  ? `${post.data.title} — ${siteConfig.title}`
  : `${displayDate} — ${siteConfig.title}`;
const pageDescription = post.data.excerpt || post.data.title || siteConfig.description;
const canonicalUrl = `${Astro.site}${Astro.params.slug}/`;
const ogImageUrl = post.data.images.length > 0
  ? `${Astro.site}${post.data.images[0].src.src}` // Will need adjustment for processed image paths
  : undefined;

const isGallery = post.data.images.length > 1;

// Location handling
let locationName: string | undefined;
let locationLat: number | undefined;
let locationLon: number | undefined;
if (post.data.location) {
  if (typeof post.data.location === 'string') {
    locationName = post.data.location;
  } else {
    locationName = post.data.location.name;
    locationLat = post.data.location.lat;
    locationLon = post.data.location.lon;
  }
}
---

<BaseLayout
  pageTitle={pageTitle}
  pageDescription={pageDescription}
  canonicalUrl={canonicalUrl}
  ogType="article"
  ogImageUrl={ogImageUrl}
  siteTitle={siteConfig.title}
  tagline={siteConfig.tagline}
  faviconUrl="/favicon.png"
>
  <Fragment slot="head">
    <script type="application/ld+json" set:html={JSON.stringify({
      "@context": "https://schema.org",
      "@type": "Article",
      headline: post.data.title || displayDate,
      datePublished: date.toISOString().split('T')[0],
      author: { "@type": "Person", name: siteConfig.author },
      description: pageDescription,
      mainEntityOfPage: { "@type": "WebPage", "@id": canonicalUrl },
    })} />
  </Fragment>

  <article class={`post ${post.data.layout}`}>
    {post.data.images.length > 0 && (
      isGallery ? (
        <Slideshow
          images={post.data.images.map((img) => ({ src: img.src, alt: img.alt }))}
          eagerCount={siteConfig.eagerImages}
          lcpIndex={0}
        />
      ) : (
        post.data.images.map((img, i) => (
          <PostImage
            image={img.src}
            alt={img.alt}
            isEager={true}
            isLcp={i === 0}
          />
        ))
      )
    )}

    {post.data.excerpt && (
      <div class="excerpt">
        <p>{post.data.excerpt}</p>
      </div>
    )}

    {post.body && (
      <div class="body">
        <Fragment set:html={post.rendered?.html} />
      </div>
    )}

    {(locationName || (locationLat != null && locationLon != null)) && (
      <p class="location">
        {locationName && <span class="location-name">{locationName}</span>}
        {locationName && locationLat != null && <span aria-hidden="true"> &middot; </span>}
        {locationLat != null && locationLon != null && (
          <a
            href={`https://maps.google.com/?q=${locationLat},${locationLon}`}
            class="location-coords"
            aria-label="View on Google Maps"
            rel="noopener"
          >
            {locationLat.toFixed(5)}, {locationLon.toFixed(5)}
          </a>
        )}
      </p>
    )}

    <p class="meta">
      <time datetime={date.toISOString().split('T')[0]}>{displayDate}</time>
    </p>
  </article>

  <nav class="feed-nav" aria-label="Post navigation">
    <a href="/">Back to feed</a>
  </nav>
</BaseLayout>
```

- [ ] **Step 2: Verify a post renders correctly**

```bash
npx astro dev
```

Navigate to `http://localhost:4321/2026/02/2026-02-21-photos/` and verify:
- Slideshow renders with 3 images
- Navigation works (click, arrows)
- Date and "Back to feed" link appear
- HTML structure matches current site

- [ ] **Step 3: Commit**

```bash
git add src/pages/\[...slug\].astro
git commit -m "feat: add post detail page with slideshow and single-image support"
```

---

### Task 7: Create feed index page with pagination

**Files:**
- Create: `src/pages/index.astro`
- Create: `src/pages/page/[page].astro`

- [ ] **Step 1: Create index.astro (page 1)**

```astro
---
import { getCollection } from 'astro:content';
import BaseLayout from '../layouts/BaseLayout.astro';
import PostImage from '../components/PostImage.astro';
import { siteConfig } from '../config';

const allPosts = await getCollection('posts');
const sorted = allPosts.sort(
  (a, b) => new Date(b.data.date).getTime() - new Date(a.data.date).getTime()
);

const totalPages = Math.ceil(sorted.length / siteConfig.postsPerPage);
const posts = sorted.slice(0, siteConfig.postsPerPage);

let imageIndex = 0;
---

<BaseLayout
  pageTitle={siteConfig.title}
  pageDescription={siteConfig.description}
  canonicalUrl={`${Astro.site}`}
  siteTitle={siteConfig.title}
  tagline={siteConfig.tagline}
  faviconUrl="/favicon.png"
>
  {posts.map((post) => {
    const date = new Date(post.data.date);
    const displayDate = date.toLocaleDateString('en-GB', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const slug = post.id.replace(/\.md$/, '');
    const postUrl = `/${year}/${month}/${slug}/`;
    const firstImage = post.data.images[0];
    const isEager = imageIndex < siteConfig.eagerImages;
    const isLcp = imageIndex === 0;
    imageIndex++;

    const locationName = typeof post.data.location === 'string'
      ? post.data.location
      : post.data.location?.name;
    const locationLat = typeof post.data.location === 'object' ? post.data.location?.lat : undefined;
    const locationLon = typeof post.data.location === 'object' ? post.data.location?.lon : undefined;

    return (
      <article class={`post ${post.data.layout}`}>
        {firstImage && (
          <PostImage
            image={firstImage.src}
            alt={firstImage.alt}
            isEager={isEager}
            isLcp={isLcp}
            linkHref={postUrl}
          />
        )}

        {post.data.excerpt ? (
          <div class="excerpt">
            <p>{post.data.excerpt}</p>
          </div>
        ) : post.body ? (
          <div class="body">
            <Fragment set:html={post.rendered?.html} />
          </div>
        ) : null}

        {(locationName || (locationLat != null && locationLon != null)) && (
          <p class="location">
            {locationName && <span class="location-name">{locationName}</span>}
            {locationName && locationLat != null && <span aria-hidden="true"> &middot; </span>}
            {locationLat != null && locationLon != null && (
              <a
                href={`https://maps.google.com/?q=${locationLat},${locationLon}`}
                class="location-coords"
                aria-label="View on Google Maps"
                rel="noopener"
              >
                {locationLat.toFixed(5)}, {locationLon.toFixed(5)}
              </a>
            )}
          </p>
        )}

        <div class="meta">
          <a href={postUrl}>
            <time datetime={date.toISOString().split('T')[0]}>{displayDate}</time>
          </a>
        </div>
      </article>
    );
  })}

  {totalPages > 1 && (
    <nav class="feed-nav" aria-label="Feed pagination">
      <a href="/page/2/">Older</a>
      <div class="meta">Page 1 of {totalPages}</div>
    </nav>
  )}
</BaseLayout>
```

- [ ] **Step 2: Create paginated pages**

Create `src/pages/page/[page].astro`:

```astro
---
import { getCollection } from 'astro:content';
import BaseLayout from '../../layouts/BaseLayout.astro';
import PostImage from '../../components/PostImage.astro';
import { siteConfig } from '../../config';

export async function getStaticPaths() {
  const allPosts = await getCollection('posts');
  const sorted = allPosts.sort(
    (a, b) => new Date(b.data.date).getTime() - new Date(a.data.date).getTime()
  );
  const totalPages = Math.ceil(sorted.length / siteConfig.postsPerPage);

  // Page 1 is handled by index.astro, generate page 2+
  return Array.from({ length: totalPages - 1 }, (_, i) => ({
    params: { page: String(i + 2) },
    props: {
      posts: sorted.slice(
        (i + 1) * siteConfig.postsPerPage,
        (i + 2) * siteConfig.postsPerPage
      ),
      currentPage: i + 2,
      totalPages,
      // Track global image index for eager loading (only page 1 gets eager)
      globalImageOffset: (i + 1) * siteConfig.postsPerPage,
    },
  }));
}

const { posts, currentPage, totalPages } = Astro.props;
const prevUrl = currentPage === 2 ? '/' : `/page/${currentPage - 1}/`;
const nextUrl = currentPage < totalPages ? `/page/${currentPage + 1}/` : null;
---

<BaseLayout
  pageTitle={`Page ${currentPage} — ${siteConfig.title}`}
  pageDescription={siteConfig.description}
  canonicalUrl={`${Astro.site}page/${currentPage}/`}
  siteTitle={siteConfig.title}
  tagline={siteConfig.tagline}
  faviconUrl="/favicon.png"
>
  {posts.map((post: any) => {
    const date = new Date(post.data.date);
    const displayDate = date.toLocaleDateString('en-GB', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const slug = post.id.replace(/\.md$/, '');
    const postUrl = `/${year}/${month}/${slug}/`;
    const firstImage = post.data.images[0];

    const locationName = typeof post.data.location === 'string'
      ? post.data.location
      : post.data.location?.name;
    const locationLat = typeof post.data.location === 'object' ? post.data.location?.lat : undefined;
    const locationLon = typeof post.data.location === 'object' ? post.data.location?.lon : undefined;

    return (
      <article class={`post ${post.data.layout}`}>
        {firstImage && (
          <PostImage
            image={firstImage.src}
            alt={firstImage.alt}
            linkHref={postUrl}
          />
        )}

        {post.data.excerpt ? (
          <div class="excerpt"><p>{post.data.excerpt}</p></div>
        ) : post.body ? (
          <div class="body"><Fragment set:html={post.rendered?.html} /></div>
        ) : null}

        {(locationName || (locationLat != null && locationLon != null)) && (
          <p class="location">
            {locationName && <span class="location-name">{locationName}</span>}
            {locationName && locationLat != null && <span aria-hidden="true"> &middot; </span>}
            {locationLat != null && locationLon != null && (
              <a
                href={`https://maps.google.com/?q=${locationLat},${locationLon}`}
                class="location-coords"
                aria-label="View on Google Maps"
                rel="noopener"
              >
                {locationLat.toFixed(5)}, {locationLon.toFixed(5)}
              </a>
            )}
          </p>
        )}

        <div class="meta">
          <a href={postUrl}>
            <time datetime={date.toISOString().split('T')[0]}>{displayDate}</time>
          </a>
        </div>
      </article>
    );
  })}

  {totalPages > 1 && (
    <nav class="feed-nav" aria-label="Feed pagination">
      <a href={prevUrl}>Newer</a>
      {nextUrl && <> &bull; <a href={nextUrl}>Older</a></>}
      <div class="meta">Page {currentPage} of {totalPages}</div>
    </nav>
  )}
</BaseLayout>
```

- [ ] **Step 3: Verify feed renders**

```bash
npx astro dev
```

Navigate to `http://localhost:4321/`. Verify:
- Posts listed in reverse chronological order
- Only first image per post shown in feed
- Images link to post detail pages
- Date below each post
- Pagination appears if >10 posts

- [ ] **Step 4: Commit**

```bash
git add src/pages/index.astro src/pages/page/
git commit -m "feat: add feed index page with pagination"
```

---

## Chunk 4: Feeds, SEO & Deployment

### Task 8: Add Atom and RSS feeds

**Files:**
- Create: `src/pages/feed.xml.ts`
- Create: `src/pages/rss.xml.ts`

- [ ] **Step 1: Create Atom feed**

Create `src/pages/feed.xml.ts`:

```typescript
import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import { siteConfig } from '../config';
import type { APIContext } from 'astro';

export async function GET(context: APIContext) {
  const posts = await getCollection('posts');
  const sorted = posts
    .sort((a, b) => new Date(b.data.date).getTime() - new Date(a.data.date).getTime())
    .slice(0, siteConfig.feedMaxPosts);

  return rss({
    title: siteConfig.title,
    description: siteConfig.description,
    site: context.site!.toString(),
    items: sorted.map((post) => {
      const date = new Date(post.data.date);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const slug = post.id.replace(/\.md$/, '');
      return {
        title: post.data.title || date.toLocaleDateString('en-GB', {
          day: '2-digit', month: 'short', year: 'numeric',
        }),
        pubDate: date,
        link: `/${year}/${month}/${slug}/`,
        description: post.data.excerpt || post.data.title || '',
      };
    }),
    customData: `<language>en-us</language>`,
  });
}
```

Note: `@astrojs/rss` generates RSS by default. For an Atom feed, you may need to generate it manually or accept that both `/feed.xml` and `/rss.xml` produce RSS 2.0. If exact Atom format is required, write a custom XML generator. For now, use `@astrojs/rss` for both endpoints with RSS 2.0 format, which is widely compatible.

- [ ] **Step 2: Create RSS feed**

Create `src/pages/rss.xml.ts` with identical content to `feed.xml.ts` (or import shared logic).

- [ ] **Step 3: Verify feeds**

```bash
npx astro build && cat dist/feed.xml | head -20
```

Expected: valid RSS/Atom XML with post entries.

- [ ] **Step 4: Commit**

```bash
git add src/pages/feed.xml.ts src/pages/rss.xml.ts
git commit -m "feat: add Atom and RSS feed endpoints"
```

---

### Task 9: Add robots.txt

**Files:**
- Create: `public/robots.txt`

- [ ] **Step 1: Create robots.txt**

```
User-agent: *
Allow: /

Sitemap: https://julianmontez.com/sitemap-index.xml
```

Note: `@astrojs/sitemap` generates `sitemap-index.xml` by default (not `sitemap.xml`). Update the robots.txt reference accordingly.

- [ ] **Step 2: Commit**

```bash
git add public/robots.txt
git commit -m "feat: add robots.txt with sitemap reference"
```

---

### Task 10: Update CI/CD for Astro

**Files:**
- Modify: `.github/workflows/deploy.yml`

- [ ] **Step 1: Rewrite deploy.yml for Astro**

```yaml
name: Build and Deploy Blog

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: "0 6 * * *"
    - cron: "0 18 * * *"
  workflow_dispatch:

permissions:
  contents: read
  deployments: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v6

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm

      - name: Install dependencies
        run: npm ci

      - name: Check types
        run: npx astro check

      - name: Build site
        run: npx astro build

  deploy:
    needs: validate
    if: github.event_name != 'pull_request'
    runs-on: ubuntu-latest
    environment: cloudflare-pages
    steps:
      - name: Checkout
        uses: actions/checkout@v6

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm

      - name: Install dependencies
        run: npm ci

      - name: Build site
        run: npx astro build

      - name: Deploy to Cloudflare Pages
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          command: pages deploy dist --project-name=${{ secrets.CLOUDFLARE_PROJECT_NAME }}
```

Key changes:
- Node.js replaces Python/uv
- `npx astro build` replaces `uv run generate-blog`
- `npx astro check` replaces ruff lint + unittest
- Output dir changes from `blog/dist/` to `dist/`

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/deploy.yml
git commit -m "feat: update CI/CD workflow for Astro build"
```

---

### Task 11: Update import script for Astro content format

**Files:**
- Modify: `scripts/import_lightroom.py`

- [ ] **Step 1: Update import_lightroom.py**

The import script needs to:
1. Copy images to `src/assets/photos/` (not `blog/static/`)
2. Generate YAML frontmatter (not TOML)
3. Write posts to `src/content/posts/` (not `blog/posts/YYYY/MM/`)

Read the current script and update the output paths and frontmatter format. The key changes:

- `STATIC_DIR` → `src/assets/photos/`
- `POSTS_DIR` → `src/content/posts/`
- Frontmatter: `---` delimiters, YAML syntax
- Image src: `../../assets/photos/filename.jpg`

- [ ] **Step 2: Verify with a dry run**

Test by running the script with a sample file (or in dry-run mode if available).

- [ ] **Step 3: Commit**

```bash
git add scripts/import_lightroom.py
git commit -m "feat: update import script for Astro content format"
```

---

## Chunk 5: Visual Verification & Cleanup

### Task 12: Full build and visual comparison

**Files:** None (verification only)

- [ ] **Step 1: Build the Astro site**

```bash
npx astro build
```

Expected: clean build, no errors.

- [ ] **Step 2: Serve and compare**

```bash
npx astro preview
```

Open `http://localhost:4321/` and compare against `https://julianmontez.com`:

Verification checklist:
- [ ] Header: "JULIAN MONTEZ" uppercase, 13px, 600 weight, 0.08em spacing
- [ ] Tagline: "Brooklyn, NY" in muted color
- [ ] Feed: photos centered, 520px max, box shadow, 96px spacing
- [ ] Feed: only first image per multi-image post, linked to detail page
- [ ] Feed: date below each post in muted color
- [ ] Feed: images have hover opacity 0.88
- [ ] Post detail (single image): photo with shadow, date, "Back to feed"
- [ ] Post detail (slideshow): full-width track, active slide at full opacity, inactive at 0.55/0.97 scale
- [ ] Slideshow: prev/next buttons, counter, click-on-slide, arrow keys, touch swipe
- [ ] Slideshow: CSS pre-centering (no jump on page load)
- [ ] View transitions: smooth crossfade between pages
- [ ] Dark mode: toggle OS preference, verify colors match tokens
- [ ] Mobile (414px): images full width, larger font, slideshow fills viewport
- [ ] Responsive image variants: check network tab for AVIF/WebP delivery
- [ ] `<picture>` element: AVIF source → WebP source → native fallback
- [ ] LCP image: check for preload link in `<head>`
- [ ] Feed XML: valid at `/feed.xml` and `/rss.xml`
- [ ] Sitemap: valid at `/sitemap-index.xml`
- [ ] JSON-LD: present on post pages (check page source)
- [ ] OG/Twitter meta tags: present with correct values
- [ ] Copyright footer: shows current year
- [ ] Accessibility: skip link works, focus outlines visible

- [ ] **Step 3: Fix any visual discrepancies**

Address any differences found in the comparison. Common issues:
- CSS specificity differences (Astro scopes styles by default — ensure `theme.css` is imported as global)
- Image path differences in OG meta tags
- Date formatting differences

- [ ] **Step 4: Commit fixes**

```bash
git add -A
git commit -m "fix: visual parity adjustments from comparison with current site"
```

---

### Task 13: Clean up old Python SSG (deferred)

**Do NOT execute this task until the Astro site is deployed and verified in production.**

This task removes the old Python SSG code once the Astro migration is confirmed working.

**Files to remove:**
- `blog/` directory (except `blog/static/` source images — already copied to `src/assets/photos/`)
- `pyproject.toml`
- `uv.lock`
- Python test files in `tests/`

**Files to update:**
- `CLAUDE.md` — update all commands and architecture docs for Astro
- `README.md` — update setup and build instructions

- [ ] **Step 1: Confirm production deployment works**
- [ ] **Step 2: Remove old Python code**
- [ ] **Step 3: Update CLAUDE.md and README.md**
- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: remove Python SSG after successful Astro migration"
```

---

## Summary of Astro Project Structure

```
julianmontez.com/
├── astro.config.mjs
├── package.json
├── tsconfig.json
├── public/
│   ├── favicon.png
│   └── robots.txt
├── src/
│   ├── config.ts
│   ├── content.config.ts
│   ├── assets/
│   │   └── photos/          # Full-resolution source images
│   │       ├── 2024-10-12-DSC_0146.jpg
│   │       └── ...
│   ├── content/
│   │   └── posts/            # Markdown posts (YAML frontmatter)
│   │       ├── 2024-10-12-DSC_0146.md
│   │       └── ...
│   ├── components/
│   │   ├── PostImage.astro
│   │   └── Slideshow.astro
│   ├── layouts/
│   │   └── BaseLayout.astro
│   ├── pages/
│   │   ├── index.astro
│   │   ├── [...slug].astro
│   │   ├── feed.xml.ts
│   │   ├── rss.xml.ts
│   │   └── page/
│   │       └── [page].astro
│   └── styles/
│       └── theme.css
├── scripts/
│   ├── convert_posts.py      # One-time migration script
│   └── import_lightroom.py   # Updated for Astro format
├── blog/                     # Old Python SSG (removed in Task 13)
└── .github/workflows/
    └── deploy.yml
```

---

## Pro/Con Summary: Astro vs Current Site

### Pros of Astro

1. **Community-maintained infrastructure** — feeds, sitemap, image processing maintained by Astro team + ecosystem; you maintain only content and design
2. **Superior image pipeline** — sharp is faster than Pillow, with built-in responsive srcset, format negotiation, and caching; no custom manifest needed
3. **View transitions as first-class feature** — reduces custom CSS/JS hacks for snapshot pre-centering
4. **Content Collections** — typed frontmatter with Zod validation, draft support, `getCollection()` API; more robust than custom TOML parsing
5. **Analytics ready** — drop-in integrations (Plausible, Fathom, etc.) without custom code
6. **TypeScript** — type safety across templates and config
7. **Hot reload** — faster dev feedback loop than rebuild-and-serve
8. **Built-in pagination** — replaces custom pagination logic
9. **Growing ecosystem** — lightbox, search, CMS integrations available when needed later

### Cons of Astro

1. **Migration effort** — real work to port templates, convert content, update CI/CD, and verify visual parity (estimated: 1-2 focused sessions)
2. **Heavier toolchain** — `node_modules/` (~200MB+) replaces the lean `uv` setup
3. **Less image quality control** — sharp exposes `quality` but not all options (e.g., WebP `method`, JPEG progressive); visual parity needs verification
4. **Slideshow is still custom** — Astro provides no carousel; the JS ports 1:1 but is the same maintenance burden
5. **Loss of test suite** — 1,560 lines of Python tests are discarded; Astro has no built-in test story for content sites; rebuilding equivalent coverage requires Playwright or similar
6. **TOML → YAML conversion** — one-time but adds a migration step; import script needs updating
7. **Framework lock-in** — trading sole-maintainer risk for framework-dependency risk
8. **Overengineering** — 11-post photoblog now depends on a full JS build toolchain; the current ~1,500 lines of Python does the job
9. **Astro's image output paths** — uses hashed filenames (`_astro/photo-abc123.avif`) instead of your current predictable names; RSS/email image URLs become less readable
