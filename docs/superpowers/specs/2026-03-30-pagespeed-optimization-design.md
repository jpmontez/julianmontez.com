# PageSpeed Insights Optimization — Design Spec

## Problem

PageSpeed Insights reports for `julianmontez.com` (Mar 30, 2026) show:

| Metric | Mobile | Desktop |
|--------|--------|---------|
| Performance | 76 | 89 |
| CLS | **0.8** (red) | **0.232** (orange) |
| FCP | 0.8s (green) | 0.2s (green) |
| LCP | 2.0s (green) | 0.5s (green) |
| TBT | 0ms | 0ms |
| Speed Index | 1.1s | 0.3s |

CLS is the dominant issue, dragging the mobile performance score from ~95 to 76.

## Root Cause Analysis

### 1. CLS: Layout shift from image figures (0.8 mobile / 0.232 desktop)

PSI identifies multiple `<figure>` and `<article class="post photo">` elements as layout shift culprits.

Each `PostImage.astro` renders a `<figure>` with an inline `aspect-ratio` style and an `<img>` with explicit `width`/`height` attributes. However, the `<figure>` CSS (`.post figure`) uses `max-width: 520px` without an explicit `width`. In flex/block layout contexts (especially inside `.image-stack`), the figure's actual width before image load may not be fully resolved, causing the `aspect-ratio` to produce an incorrect initial height. When the image loads and the figure resolves to its final width, content below shifts.

Additionally, PSI flags every image as "Unsized image element" despite `width`/`height` attributes. This occurs because the `<img>` declared dimensions (1040x832, the fallback size) don't match the actual rendered dimensions on mobile (~350x280). Setting `width`/`height` to the CSS display size (the fallback max — 520px) instead of the source/fallback size will fix this diagnostic.

**Fix:** Add `width: 100%` to `.post figure` so the browser resolves figure width deterministically before image load, allowing `aspect-ratio` to compute the correct height. Also set `<img>` `width`/`height` attributes to the display size (520px-based) rather than the fallback source size (1040px).

### 2. LCP: Wrong image identified as LCP candidate (mobile only)

PSI flags the LCP image (DSC_0391) with:
- "lazy load not applied" (image has `loading="lazy"`)
- "fetchpriority=high should be applied" (missing `fetchpriority`)

On the feed page, the first post has 2 stacked images. The code at `index.astro:75` passes `isLcp={isLcp && i === 0}`, so only image i=0 gets `fetchpriority="high"`. But Lighthouse identifies the *second* image (i=1) in the stack as the actual LCP element on mobile — the one that occupies the most viewport area.

For posts at index >= 1, the eager logic (`isEager={index === 0 ? isEager : (isEager && i === 0)}`) only makes the first image of each post eager. The second image in any multi-image post gets `loading="lazy"` even if it's above the fold.

**Fix:** For the first post on the feed, mark ALL images as both eager and LCP candidates (all get `fetchpriority="high"`). Increase `eagerImages` from 2 to 3 to cover more above-fold content.

### 3. LCP: No `<link rel="preload">` on feed pages

`BaseLayout.astro` supports a `preloadImage` prop that generates `<link rel="preload" as="image" type="image/avif" fetchpriority="high">` in `<head>`. Neither `index.astro` nor `page/[page].astro` pass this prop. The LCP image is only discovered when the browser parses the `<img>` tag in the body.

**Fix:** Generate preload data for the first post's first image on both feed pages and pass it to `BaseLayout`.

### 4. Image delivery: Mobile images slightly oversized (13 KiB savings)

Current responsive widths are [520, 760, 1040]. On a Moto G Power (390px viewport, 1.75 DPR), `90vw` = 351px CSS, needing ~614 device pixels. The browser selects 760w. A 640w variant would be a closer fit.

**Fix:** Add a 640px width to `RESPONSIVE_WIDTHS` — [520, 640, 760, 1040]. This serves a better match for mid-DPR mobile devices without adding excessive build variants.

### 5. Cache lifetimes (out of scope)

Only affects Cloudflare-injected scripts (beacon.min.js, email-decode.min.js). User will address via Cloudflare configuration separately.

## Changes

### A. `src/styles/theme.css` — Fix figure sizing for CLS

Add `width: 100%` to `.post figure`:

```css
.post figure {
  margin: 0 auto 18px;
  max-width: 520px;
  width: 100%;              /* NEW: resolve width before image loads */
  box-shadow: var(--shadow);
  background: white;
}
```

This ensures the figure's width is deterministic. Combined with the inline `aspect-ratio`, the browser can reserve the exact space needed before any images load.

### B. `src/components/PostImage.astro` — Fix img dimensions and add 640w variant

1. Change `<img>` `width`/`height` to use the CSS display width (520px) instead of the fallback variant width (1040px). The aspect ratio stays the same.

2. Add 640 to `RESPONSIVE_WIDTHS`:
```typescript
const RESPONSIVE_WIDTHS = [520, 640, 760, 1040];
```

3. Compute display-size dimensions for the `<img>` tag:
```typescript
const DISPLAY_WIDTH = 520; // matches max CSS display size
const displayHeight = Math.round(DISPLAY_WIDTH * aspectRatio);
```

Use `DISPLAY_WIDTH` and `displayHeight` for the `<img>` `width`/`height` attributes. Keep `fallback.src` as the `src` attribute (still the largest native variant).

### C. `src/pages/index.astro` — Fix LCP loading + add preload

1. **LCP images:** For the first post (index === 0), pass `isLcp={true}` to ALL images in the stack (not just i === 0). This gives all above-fold images `fetchpriority="high"`.

2. **Preload:** Generate preload data for the first post's first image and pass to `BaseLayout`:
```typescript
// At top of frontmatter, after getting posts:
const firstImage = posts[0]?.data.images[0];
let preloadImage;
if (firstImage) {
  // Generate AVIF and native variants for preload srcset
  const preloadAvif = await Promise.all(
    [520, 640, 760, 1040].map(w =>
      getImage({ src: firstImage.src, width: w, format: 'avif', quality: 40 })
    )
  );
  const preloadNative = await Promise.all(
    [520, 640, 760, 1040].filter(w => w < firstImage.src.width).map(w =>
      getImage({ src: firstImage.src, width: w, format: 'jpg', quality: 85 })
    )
  );
  preloadImage = {
    src: preloadNative[preloadNative.length - 1]?.src || preloadAvif[0].src,
    avifSrcset: preloadAvif.map(v => `${v.src} ${v.attributes.width}w`).join(', '),
    srcset: preloadNative.map(v => `${v.src} ${v.attributes.width}w`).join(', '),
    sizes: siteConfig.imageSizes,
  };
}
```

Pass to BaseLayout: `<BaseLayout pageTitle={siteConfig.title} preloadImage={preloadImage}>`

### D. `src/config.ts` — Increase eagerImages

```typescript
eagerImages: 3,  // was 2
```

This ensures more above-fold images on the feed get `loading="eager"`.

### E. `src/pages/page/[page].astro` — Parity with index.astro

Apply the same eager/LCP improvements as index.astro (items C.1 and C.2) for consistency across paginated feed pages. Page 2+ may not need preloading as aggressively, but the first image on each page should still be eager and high-priority.

## Files Modified

1. `src/styles/theme.css` — add `width: 100%` to `.post figure`
2. `src/components/PostImage.astro` — add 640w variant, use display-size img dimensions
3. `src/pages/index.astro` — fix LCP loading, add preload
4. `src/config.ts` — increase eagerImages to 3
5. `src/pages/page/[page].astro` — parity LCP/eager fixes

## Expected Impact

| Metric | Before (Mobile) | Expected After |
|--------|-----------------|----------------|
| CLS | 0.8 | < 0.1 |
| LCP | 2.0s | ~1.5s |
| Performance | 76 | 90+ |

CLS fix alone should recover ~15-20 performance points. LCP preloading and eager loading should add a few more.

## Verification

After implementation:
1. `npx astro build` — ensure no build errors
2. `npx astro dev` — visual verification that layout looks identical
3. Re-run PageSpeed Insights on both mobile and desktop
4. Verify no CLS via Chrome DevTools Performance panel (local)
