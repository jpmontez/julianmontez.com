# Design: Feed Stacked Images & Email Header

**Date:** 2026-03-30

## Overview

Two independent UI changes:

1. Replace the horizontal slideshow on feed pages with vertically stacked images for multi-image posts.
2. Add a mailto email link to the site header tagline.

---

## Feature 1: Stacked Images on Feed Pages

### Problem

Multi-image posts on the feed (homepage and paginated pages) currently render a `<Slideshow>` component. This is jarring in the context of a scrollable feed. The slideshow should be reserved for the individual post page.

### Solution

Replace the `<Slideshow>` branch in both feed pages with a `<div class="image-stack">` containing a loop of `<PostImage>` components. All images are rendered vertically with a small gap. Each image links to the post, consistent with single-image posts.

### Files Changed

- `src/pages/index.astro` — replace `<Slideshow>` branch with `<div class="image-stack">` + mapped `<PostImage>` loop
- `src/pages/page/[page].astro` — same change
- `src/styles/theme.css` — add `.image-stack` rule

### CSS

```css
.image-stack {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
```

### Eager loading

- `index.astro` carries over existing eager-loading logic: `eagerCount` and `lcpIndex` applied to the first post's images. For the stacked layout, only the first image of the first post gets `isEager` and `isLcp`; all others are lazy.
- `page/[page].astro` loads all images lazily (no eager logic currently).

### Slideshow unchanged

`src/components/Slideshow.astro` is not modified. It remains in use on the individual post page (`src/pages/[...slug].astro`).

---

## Feature 2: Email Link in Header

### Problem

The site has no contact mechanism. Adding an email link to the header gives visitors a direct way to reach Julian without requiring a separate contact page.

### Solution

Add `email` to `siteConfig` and render it inline with the tagline in `BaseLayout.astro`. The link uses a `mailto:` href. Styling matches the site's existing pattern for understated navigational links: no underline by default, underline on hover.

### Rendered output

```
JULIAN MONTEZ
Brooklyn, NY | Email
```

The separator `|` is wrapped in `aria-hidden="true"` so screen readers skip it.

### Files Changed

- `src/config.ts` — add `email: 'contact@julianmontez.com'`
- `src/layouts/BaseLayout.astro` — update tagline `<span>` to include separator and mailto link
- `src/styles/theme.css` — add link styles scoped to `header.site .tagline a`

### CSS

```css
header.site .tagline a {
  text-decoration: none;
}
header.site .tagline a:hover {
  text-decoration: underline;
}
```

---

## Out of Scope

- No changes to `Slideshow.astro` or individual post pages
- No new components or files beyond what is listed
- No changes to the RSS/Atom feed output
