# PageSpeed Insights Optimization — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix CLS (0.8 mobile → <0.1), improve LCP discovery, and optimize image delivery to raise mobile PageSpeed performance from 76 to 90+.

**Architecture:** Five targeted edits across CSS, component, config, and page files. CLS fix via deterministic figure sizing. LCP fix via eager loading all first-post images + `<link rel="preload">` in `<head>`. Image delivery fix via an additional 640px responsive width.

**Tech Stack:** Astro 5 static site, CSS (no framework), Sharp image pipeline.

**Spec:** `docs/superpowers/specs/2026-03-30-pagespeed-optimization-design.md`

---

### Task 1: Fix figure CSS sizing for CLS

**Files:**
- Modify: `src/styles/theme.css:172-177`

- [ ] **Step 1: Add `width: 100%` to `.post figure`**

In `src/styles/theme.css`, change the `.post figure` rule from:

```css
.post figure {
  margin: 0 auto 18px;
  max-width: 520px;
  box-shadow: var(--shadow);
  background: white;
}
```

to:

```css
.post figure {
  margin: 0 auto 18px;
  max-width: 520px;
  width: 100%;
  box-shadow: var(--shadow);
  background: white;
}
```

This ensures the browser resolves figure width before any images load. Combined with the inline `aspect-ratio` style on each `<figure>`, the browser can reserve the exact space needed, eliminating layout shift.

- [ ] **Step 2: Verify build**

Run: `npx astro build`
Expected: Clean build, no errors.

- [ ] **Step 3: Commit**

```bash
git add src/styles/theme.css
git commit -m "fix: add explicit width to .post figure to eliminate CLS"
```

---

### Task 2: Add 640w responsive width + fix img dimensions in PostImage

**Files:**
- Modify: `src/components/PostImage.astro:16-22,80-82,88,94-104,111-121`

- [ ] **Step 1: Add 640 to RESPONSIVE_WIDTHS and add DISPLAY_WIDTH constant**

In `src/components/PostImage.astro`, change lines 16-22 from:

```typescript
// Widths are derived from the max CSS display size (520px, see config.ts imageSizes):
//   520px = 1× desktop exact match
//   1040px = 2× desktop (Retina) exact match, also good for 2× mobile (~390–430px viewport)
const RESPONSIVE_WIDTHS = [520, 760, 1040];
const AVIF_QUALITY = 40;
const WEBP_QUALITY = 80;
const JPEG_QUALITY = 85;
```

to:

```typescript
// Widths are derived from the max CSS display size (520px, see config.ts imageSizes):
//   520px = 1× desktop exact match
//   640px = ~1.75× mobile (Moto G Power class devices, 390px × 1.75 DPR ≈ 614px)
//   760px = 2× mid-range mobile
//   1040px = 2× desktop (Retina) exact match
const RESPONSIVE_WIDTHS = [520, 640, 760, 1040];
const AVIF_QUALITY = 40;
const WEBP_QUALITY = 80;
const JPEG_QUALITY = 85;
const DISPLAY_WIDTH = 520; // matches max CSS display size (.post figure max-width)
```

- [ ] **Step 2: Replace fallbackWidth/fallbackHeight usage for img attributes**

Change lines 80-85 from:

```typescript
const fallbackWidth = fallback.attributes.width;
const fallbackHeight = Math.round(Number(fallbackWidth) * aspectRatio);

const sizes = siteConfig.imageSizes;
const loading = isEager ? 'eager' : 'lazy';
```

to:

```typescript
const displayHeight = Math.round(DISPLAY_WIDTH * aspectRatio);

const sizes = siteConfig.imageSizes;
const loading = isEager ? 'eager' : 'lazy';
```

- [ ] **Step 3: Update the figure aspect-ratio and both img tags**

Change line 88 from:

```html
<figure style={`aspect-ratio: ${fallbackWidth} / ${fallbackHeight};`}>
```

to:

```html
<figure style={`aspect-ratio: ${DISPLAY_WIDTH} / ${displayHeight};`}>
```

Change the first `<img>` (lines 94-104, inside the `linkHref` branch) from:

```html
        <img
          src={fallback.src}
          alt={alt}
          srcset={nativeSrcset}
          sizes={sizes}
          width={fallbackWidth}
          height={fallbackHeight}
          loading={loading}
          fetchpriority={isLcp ? 'high' : undefined}
          decoding="async"
        />
```

to:

```html
        <img
          src={fallback.src}
          alt={alt}
          srcset={nativeSrcset}
          sizes={sizes}
          width={DISPLAY_WIDTH}
          height={displayHeight}
          loading={loading}
          fetchpriority={isLcp ? 'high' : undefined}
          decoding="async"
        />
```

Change the second `<img>` (lines 111-121, the non-link branch) the same way — replace `width={fallbackWidth}` with `width={DISPLAY_WIDTH}` and `height={fallbackHeight}` with `height={displayHeight}`.

- [ ] **Step 4: Verify build**

Run: `npx astro build`
Expected: Clean build, no errors.

- [ ] **Step 5: Commit**

```bash
git add src/components/PostImage.astro
git commit -m "perf: add 640w responsive width and use display-size img dimensions"
```

---

### Task 3: Increase eagerImages in config

**Files:**
- Modify: `src/config.ts:8`

- [ ] **Step 1: Change eagerImages from 2 to 3**

In `src/config.ts`, change line 8 from:

```typescript
  eagerImages: 2,
```

to:

```typescript
  eagerImages: 3,
```

- [ ] **Step 2: Commit**

```bash
git add src/config.ts
git commit -m "perf: increase eagerImages from 2 to 3 for better above-fold coverage"
```

---

### Task 4: Fix LCP loading + add preload on index.astro

**Files:**
- Modify: `src/pages/index.astro:1-6,56,62-63,67-77`

- [ ] **Step 1: Add getImage import**

In `src/pages/index.astro`, change lines 1-5 from:

```typescript
---
import { getCollection, render } from 'astro:content';
import BaseLayout from '../layouts/BaseLayout.astro';
import PostImage from '../components/PostImage.astro';
import { siteConfig } from '../config';
```

to:

```typescript
---
import { getCollection, render } from 'astro:content';
import { getImage } from 'astro:assets';
import BaseLayout from '../layouts/BaseLayout.astro';
import PostImage from '../components/PostImage.astro';
import { siteConfig } from '../config';
```

- [ ] **Step 2: Add preload image generation**

After the `getLocationInfo` function (after line 53, before the closing `---`), add the preload generation code:

```typescript
// Generate preload data for the first post's first image (LCP candidate)
const firstImage = posts[0]?.data.images[0];
let preloadImage: {
  src: string;
  srcset?: string;
  avifSrcset?: string;
  sizes?: string;
} | undefined;
if (firstImage) {
  const WIDTHS = [520, 640, 760, 1040];
  const AVIF_Q = 40;
  const JPEG_Q = 85;
  const srcWidth = firstImage.src.width;
  const nativeFormat = firstImage.src.format === 'png' ? 'png' as const : 'jpg' as const;
  const [preloadAvif, preloadNative] = await Promise.all([
    Promise.all(
      WIDTHS.map((w) => getImage({ src: firstImage.src, width: w, format: 'avif', quality: AVIF_Q }))
    ),
    Promise.all(
      WIDTHS.filter((w) => w < srcWidth).map((w) =>
        getImage({ src: firstImage.src, width: w, format: nativeFormat, quality: JPEG_Q })
      )
    ),
  ]);
  const fallbackSrc = preloadNative.length > 0
    ? preloadNative[preloadNative.length - 1].src
    : preloadAvif[0].src;
  preloadImage = {
    src: fallbackSrc,
    avifSrcset: preloadAvif.map((v) => `${v.src} ${v.attributes.width}w`).join(', '),
    srcset: preloadNative.map((v) => `${v.src} ${v.attributes.width}w`).join(', '),
    sizes: siteConfig.imageSizes,
  };
}
```

- [ ] **Step 3: Pass preloadImage to BaseLayout**

Change line 56 from:

```html
<BaseLayout pageTitle={siteConfig.title}>
```

to:

```html
<BaseLayout pageTitle={siteConfig.title} preloadImage={preloadImage}>
```

- [ ] **Step 4: Fix LCP and eager props for the first post's image stack**

Change the multi-image branch (lines 67-78) from:

```html
        {post.data.images.length > 1 ? (
          <div class="image-stack">
            {post.data.images.map((img, i) => (
              <PostImage
                image={img.src}
                alt={img.alt}
                linkHref={postUrl}
                isEager={index === 0 ? isEager : (isEager && i === 0)}
                isLcp={isLcp && i === 0}
              />
            ))}
          </div>
```

to:

```html
        {post.data.images.length > 1 ? (
          <div class="image-stack">
            {post.data.images.map((img, i) => (
              <PostImage
                image={img.src}
                alt={img.alt}
                linkHref={postUrl}
                isEager={index === 0 ? isEager : (isEager && i === 0)}
                isLcp={isLcp}
              />
            ))}
          </div>
```

The only change: `isLcp={isLcp && i === 0}` becomes `isLcp={isLcp}`. This gives ALL images in the first post `fetchpriority="high"`, since any of them could be the actual LCP element depending on viewport.

- [ ] **Step 5: Verify build**

Run: `npx astro build`
Expected: Clean build, no errors.

- [ ] **Step 6: Commit**

```bash
git add src/pages/index.astro
git commit -m "perf: add LCP preload and fix fetchpriority for first post images"
```

---

### Task 5: Apply parity fixes to page/[page].astro

**Files:**
- Modify: `src/pages/page/[page].astro:1-5,29,77-78,84-95`

- [ ] **Step 1: Add getImage import and eager/LCP variables**

Change lines 1-5 from:

```typescript
---
import { getCollection, render } from 'astro:content';
import BaseLayout from '../../layouts/BaseLayout.astro';
import PostImage from '../../components/PostImage.astro';
import { siteConfig } from '../../config';
```

to:

```typescript
---
import { getCollection, render } from 'astro:content';
import { getImage } from 'astro:assets';
import BaseLayout from '../../layouts/BaseLayout.astro';
import PostImage from '../../components/PostImage.astro';
import { siteConfig } from '../../config';
```

- [ ] **Step 2: Add preload generation and eager/LCP setup**

After line 74 (`const hasOlder = pageNum < totalPages;`), before the closing `---`, add:

```typescript

// Generate preload data for the first post's first image
const firstImage = posts[0]?.data.images[0];
let preloadImage: {
  src: string;
  srcset?: string;
  avifSrcset?: string;
  sizes?: string;
} | undefined;
if (firstImage) {
  const WIDTHS = [520, 640, 760, 1040];
  const AVIF_Q = 40;
  const JPEG_Q = 85;
  const srcWidth = firstImage.src.width;
  const nativeFormat = firstImage.src.format === 'png' ? 'png' as const : 'jpg' as const;
  const [preloadAvif, preloadNative] = await Promise.all([
    Promise.all(
      WIDTHS.map((w) => getImage({ src: firstImage.src, width: w, format: 'avif', quality: AVIF_Q }))
    ),
    Promise.all(
      WIDTHS.filter((w) => w < srcWidth).map((w) =>
        getImage({ src: firstImage.src, width: w, format: nativeFormat, quality: JPEG_Q })
      )
    ),
  ]);
  const fallbackSrc = preloadNative.length > 0
    ? preloadNative[preloadNative.length - 1].src
    : preloadAvif[0].src;
  preloadImage = {
    src: fallbackSrc,
    avifSrcset: preloadAvif.map((v) => `${v.src} ${v.attributes.width}w`).join(', '),
    srcset: preloadNative.map((v) => `${v.src} ${v.attributes.width}w`).join(', '),
    sizes: siteConfig.imageSizes,
  };
}
```

- [ ] **Step 3: Pass preloadImage to BaseLayout and add eager/LCP to render loop**

Change line 77 from:

```html
<BaseLayout pageTitle={`Page ${pageNum} — ${siteConfig.title}`}>
```

to:

```html
<BaseLayout pageTitle={`Page ${pageNum} — ${siteConfig.title}`} preloadImage={preloadImage}>
```

Change the render loop (line 78) from:

```html
  {rendered.map(({ post, Content }: any) => {
    const postUrl = getPostUrl(post);
    const { display, iso } = formatDate(post.data.date);
    const { name: locationName, lat, lon } = getLocationInfo(post.data.location);
    const hasLocation = locationName || (lat != null && lon != null);
```

to:

```html
  {rendered.map(({ post, Content }: any, index: number) => {
    const postUrl = getPostUrl(post);
    const { display, iso } = formatDate(post.data.date);
    const { name: locationName, lat, lon } = getLocationInfo(post.data.location);
    const hasLocation = locationName || (lat != null && lon != null);
    const isEager = index < siteConfig.eagerImages;
    const isLcp = index === 0;
```

- [ ] **Step 4: Add isEager and isLcp props to PostImage calls**

Change the multi-image branch (lines 86-95) from:

```html
        {post.data.images.length > 1 ? (
          <div class="image-stack">
            {post.data.images.map((img: any) => (
              <PostImage
                image={img.src}
                alt={img.alt}
                linkHref={postUrl}
              />
            ))}
          </div>
```

to:

```html
        {post.data.images.length > 1 ? (
          <div class="image-stack">
            {post.data.images.map((img: any, i: number) => (
              <PostImage
                image={img.src}
                alt={img.alt}
                linkHref={postUrl}
                isEager={index === 0 ? isEager : (isEager && i === 0)}
                isLcp={isLcp}
              />
            ))}
          </div>
```

Change the single-image branch (lines 96-102) from:

```html
        ) : post.data.images.length === 1 ? (
          <PostImage
            image={post.data.images[0].src}
            alt={post.data.images[0].alt}
            linkHref={postUrl}
          />
```

to:

```html
        ) : post.data.images.length === 1 ? (
          <PostImage
            image={post.data.images[0].src}
            alt={post.data.images[0].alt}
            linkHref={postUrl}
            isEager={isEager}
            isLcp={isLcp}
          />
```

- [ ] **Step 5: Verify build**

Run: `npx astro build`
Expected: Clean build, no errors.

- [ ] **Step 6: Commit**

```bash
git add src/pages/page/[page].astro
git commit -m "perf: add LCP preload and eager loading to paginated feed pages"
```

---

### Task 6: Full build verification + type check

- [ ] **Step 1: Run type check**

Run: `npx astro check`
Expected: No errors. Warnings are acceptable.

- [ ] **Step 2: Run full build**

Run: `npx astro build`
Expected: Clean build. Confirm the built output includes the new 640w image variants in `dist/_astro/`.

- [ ] **Step 3: Visual spot-check**

Run: `npx astro dev`
Open `http://localhost:4321` in a browser. Verify:
- Feed page images display at the same size and position as before
- Image-stack posts show all images stacked vertically
- No visible layout shift on page load (images should appear in place, not jump)
- Navigate to a single post page — verify slideshow and single images still work

- [ ] **Step 4: Inspect preload in HTML**

View source on `http://localhost:4321/`. Confirm:
- A `<link rel="preload" as="image" type="image/avif" ...>` tag exists in `<head>`
- A second `<link rel="preload" as="image" ...>` tag exists for the native fallback
- Both have `fetchpriority="high"` and `imagesrcset` with 4 widths (520w, 640w, 760w, 1040w)

- [ ] **Step 5: Inspect first post images**

Right-click the first image on the feed → Inspect. Confirm:
- `loading="eager"` (not `lazy`)
- `fetchpriority="high"`
- `width="520"` and `height` matches the 520-based aspect ratio
- For multi-image first post: ALL images in the stack have `loading="eager"` and `fetchpriority="high"`
