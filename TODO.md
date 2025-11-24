# TODO

- Fix mobile LCP: first image is now prioritized (eager + `fetchpriority="high"` with optional preload); verify results.
  - Re-run PageSpeed mobile after the change to confirm LCP improvement; adjust if still flagged.
  - Ensure the generator keeps tagging the first feed image (and per-post hero) as eager/high-priority while leaving others lazy.
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
