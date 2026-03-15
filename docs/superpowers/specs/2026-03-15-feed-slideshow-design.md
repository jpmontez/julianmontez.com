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

**Props:** Add `linkHref?: string` to the `Props` interface. Pass it to each `PostImage` inside the slideshow.

**`lcpIndex` default:** Change the prop default from `lcpIndex = 0` to `lcpIndex = -1`. Update the `isLcp` check passed to `PostImage` to `i === lcpIndex && lcpIndex >= 0`. This ensures omitting `lcpIndex` (or passing `undefined`) means no slide gets `fetchpriority="high"`, rather than slide 0 silently receiving it on every non-LCP feed post.

**JS click handler:** The existing handler has signature `function ()` with no parameter. Change it to `function (e)` and add a guard so clicks on `<a>` elements (or their descendants) are not intercepted — the link navigates normally, and `setActive` is skipped:

```js
slide.addEventListener("click", function (e) {
  if (e.target.closest && e.target.closest('a')) return;
  activateState();
  setActive(slideIndex);
});
```

`e.target.closest('a')` correctly walks up from `<img>` or `<picture>` to find the wrapping `<a>`. Individual post pages pass no `linkHref`, so the guard never fires there — behavior unchanged.

**Click UX on feed:** When `linkHref` is set, clicking any slide image (active or inactive) always navigates immediately to the post. There is no "activate-then-click-again" affordance — one tap on any slide navigates. Slide activation on the feed happens only via prev/next buttons and swipe. This matches the user requirement.

**Deduplication of window-level listeners:** `<script is:inline>` executes immediately as each component is parsed, so each script block sees only its own slideshow in the DOM at that moment. The per-slideshow initialization (`slideshows.forEach`) runs correctly for each instance. The problem is the `window.addEventListener("keydown", ...)` block at the bottom of the IIFE — it re-registers a global handler for every slideshow component on the page. Wrap only that registration with a guard:

```js
if (!window.__slideshowKeyListenerAdded) {
  window.__slideshowKeyListenerAdded = true;
  window.addEventListener("keydown", function (event) { ... });
}
```

Do NOT guard the entire IIFE — each run must still initialize its own slideshow instance. The `window.addEventListener("resize", snapCenter)` call is inside the per-slideshow `forEach` loop (one handler per slideshow). Handler accumulation across navigations is not a concern: this site uses CSS-only cross-document view transitions (`@view-transition { navigation: auto }`), which are full page reloads — scripts start fresh on each navigation.

### `index.astro`

Add `Slideshow` to the imports. Replace the existing image block with a three-way branch (preserve the outer `images.length > 0` guard):

```
images.length > 1
  ? <Slideshow images={images} linkHref={postUrl} eagerCount={isEager ? 1 : 0} lcpIndex={isLcp ? 0 : -1} />
  : images.length === 1
    ? <PostImage image={images[0].src} alt={images[0].alt} linkHref={postUrl} isEager={isEager} isLcp={isLcp} />
    : null
```

**`eagerCount={isEager ? 1 : 0}`** — intentionally 1 (not the Slideshow default of 2). On the feed, at most one image per post should eager-load, matching the current single-image behavior.

**`lcpIndex={isLcp ? 0 : -1}`** — explicitly pass `-1` for non-LCP posts (do not rely on the default). With the updated `lcpIndex = -1` default in `Slideshow.astro`, `-1` is now the correct documented sentinel meaning "no LCP slide."

### `page/[page].astro`

Add `Slideshow` to the imports. Same three-way branch, without `isEager`/`isLcp` logic:

```
images.length > 1
  ? <Slideshow images={images} linkHref={postUrl} />
  : images.length === 1
    ? <PostImage image={images[0].src} alt={images[0].alt} linkHref={postUrl} />
    : null
```

## Files Changed

| File | Change |
|---|---|
| `src/components/Slideshow.astro` | Add `linkHref` prop; change `lcpIndex` default to `-1`; update `isLcp` check; update click handler signature and guard; wrap keydown listener with deduplication guard |
| `src/pages/index.astro` | Add `Slideshow` import; replace image block with three-way branch |
| `src/pages/page/[page].astro` | Add `Slideshow` import; replace image block with three-way branch |

## Out of Scope

- No changes to `[...slug].astro` (already correct)
- No changes to `PostImage.astro`
- No CSS changes (slideshow styles already apply on the feed)
