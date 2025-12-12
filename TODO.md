# TODO

- Fix mobile LCP and responsive images: verified via PageSpeed (100/100 Perf/Access/Best Practices/SEO). Keep an eye on future regressions.
  - Generator creates multiple widths for raster assets and emits `srcset`/`sizes`; non-LCP images remain lazy-loaded; LCP image prioritized (no preload).
  - Keep Lightroom workflow simple (single export); adjust widths/quality only if future audits regress.
- Add a gallery view for multi-photo posts.
  - This would only be utilized in a dedicated post page.

Completed (keep below active items):
- ~~Fix canonical URLs to be absolute (set `site_url` in `blog/config.toml`) to satisfy the Lighthouse/PageSpeed `rel=canonical` audit.~~
- ~~Add per-image alt text support (front matter + templates) and populate alts for existing posts.~~
- ~~Fix `attach_image_meta()` caching for repeated image paths (was reusing a stale `candidate` and could generate incorrect `primary_src`).~~
- ~~Enable Jinja2 autoescape in `blog/generate.py` and ensure templates only mark trusted HTML as safe.~~
- ~~Fix deep-page asset links (e.g., favicon) to use `assets_prefix`.~~
- ~~Fix `blog/robots.txt` sitemap URL (was pointing to an unrelated external sitemap).~~
- ~~Add sitemap.xml (with images).~~
- ~~Add canonical/meta updates and per-post meta descriptions.~~
- ~~Move `ruff` to a dev dependency group and update CI to install only runtime deps for deploy.~~
- ~~Add `.gitignore` entries for local env/caches (e.g., `.venv`, `.uv*`, `.ruff_cache`).~~
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
