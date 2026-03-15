# Feed Slideshow Design

**Date:** 2026-03-15
**Status:** Approved

## Problem

Multi-image posts only display their first image on the feed (index and paginated pages). The individual post page already renders a full interactive slideshow via `Slideshow.astro`. The feed should match.

## Requirements

- Multi-image posts on the feed show a full slideshow (prev/next, swipe, keyboard nav)
- Clicking a slide image navigates to the post (same as the existing single-image link behavior)
- Prev/next buttons and swipe navigation work as they do on individual post pages
- Single-image posts are unaffected
- LCP and eager-load hints remain correct on the feed

## Design

### `Slideshow.astro`

Add `linkHref?: string` to the `Props` interface. Pass it to each `PostImage` inside the slideshow. In the inline JS click handler that calls `setActive(slideIndex)`, add a guard:

```js
slide.addEventListener("click", function (e) {
  if (e.target.closest && e.target.closest('a')) return;
  activateState();
  setActive(slideIndex);
});
```

This lets `<a>` clicks bubble and navigate normally (post link), while non-link clicks still center the slide. Individual post pages pass no `linkHref`, so their behavior is unchanged.

### `index.astro`

Replace the unconditional `<PostImage images[0] />` with the same branch used in `[...slug].astro`:

```
images.length > 1
  ? <Slideshow images={images} linkHref={postUrl} eagerCount={isEager ? 1 : 0} lcpIndex={isLcp ? 0 : -1} />
  : <PostImage image={images[0].src} alt={images[0].alt} linkHref={postUrl} isEager={isEager} isLcp={isLcp} />
```

`eagerCount={isEager ? 1 : 0}` ensures only the first slide of eager posts is eagerly loaded — equivalent to the current single-image behavior. `lcpIndex={isLcp ? 0 : -1}` preserves `fetchpriority="high"` on the first post's first slide only.

### `page/[page].astro`

Same change as `index.astro`, without the `isEager`/`isLcp` logic (pagination pages have no LCP designation). All images on paginated feeds use lazy loading.

## Files Changed

| File | Change |
|---|---|
| `src/components/Slideshow.astro` | Add `linkHref` prop; guard JS click handler |
| `src/pages/index.astro` | Multi-image branch with Slideshow + linkHref |
| `src/pages/page/[page].astro` | Same as index.astro |

## Out of Scope

- No changes to `[...slug].astro` (already correct)
- No changes to `PostImage.astro`
- No CSS changes (slideshow styles already apply on the feed)
