# TODO

- Fix mobile LCP and responsive images: verified via PageSpeed (100/100 Perf/Access/Best Practices/SEO). Keep an eye on future regressions.
  - Generator creates multiple widths for raster assets and emits `srcset`/`sizes`; non-LCP images remain lazy-loaded; LCP image prioritized (no preload).
  - Keep Lightroom workflow simple (single export); adjust widths/quality only if future audits regress.
- Add a gallery view for multi-photo posts.
  - This would only be utilized in a dedicated post page.
- Add sitemap.xml (with images).
- Add canonical/meta updates and per-post meta descriptions.

Completed (keep below active items):
- ~~Add intrinsic width/height/aspect-ratio for generated `<img>` tags (ideally using real image dimensions from static assets).~~
- ~~Ensure CSS preserves responsive scaling without layout shift.~~
- ~~Add a main landmark (`<main role="main">`) around primary content for accessibility.~~
- ~~Add robots.txt.~~
- ~~Add width/height or CSS aspect-ratio; ensure responsive sizing (max-width: 100%, height: auto).~~
- ~~Fix CLS from unsized images:~~
- ~~Automate Lightroom JPG exports and initial post skeleton creation/boilerplate~~
- ~~Add lazy-loading to images.~~
- ~~Cleanup the URL slugs so that `index.html` is not visible.~~
- ~~Implement a CI/CD pipeline~~
- ~~Implement the full GitHub Pages deployment~~
- ~~Add pagination support~~
- ~~Add formatting, linting support~~
