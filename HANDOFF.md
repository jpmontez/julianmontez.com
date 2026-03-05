# Project Snapshot
Static Tumblr-style microblog generator in Python (uv-managed), publishing static output to `blog/dist` for Cloudflare Pages.

Last updated: 2026-03-05

# Current State
- Generator architecture is modular:
  - `blog/generate.py` (CLI orchestration)
  - `blog/config.py`, `blog/content.py`, `blog/images.py`, `blog/render.py`, `blog/feeds.py`, `blog/seo.py`, `blog/urls.py`, `blog/assets.py`, `blog/models.py`
- CSS is inlined by default; external `dist/style.css` is optional via `emit_style_file`.
- Responsive image variants, sitemap, robots, Atom, and RSS are generated during build.
- Raster images now render via `<picture>` with AVIF/WebP sources and original-format fallback.
- Posts now support optional `location` metadata (name + lat/lon), rendered on feed and post pages with map links.
- Mobile typography now increases base `body` size only under a coarse-pointer small-screen media query.
- Post body text now uses a Helvetica-first sans-serif stack (while global UI/meta typography remains monospace).
- Feed/post visuals intentionally hide post title headings; navigation relies on date/meta and image links.
- Multi-image posts render as a horizontal strip slideshow with left/right arrow controls that center the active image.
- In slideshow mode, clicking an image now selects/centers that image instead of navigating to the source file.
- Single-image post pages now match slideshow behavior: clicking an image no longer opens the source file directly.
- Keyboard arrow keys (`←`/`→`) now navigate the active slideshow using the same centering behavior.
- Site header typography intentionally matches the original visual style.
- Site title in the header now links to the homepage (`{{ assets_prefix }}/`) from every page.
- CI workflow split:
  - `validate` job runs test/lint/build.
  - `deploy` job runs on non-PR events and deploys to Cloudflare Pages.

# Verified Commands
- `make test`: pass
- `uv run ruff check`: pass
- `uv run generate-blog`: pass
- `make preview`: pass (uses `uv run python -m http.server`)

# Recent Changes
- Fixed intermittent slideshow flicker on view-transition navigation (Mar 2026): added CSS initial transforms to `.post .slideshow-track` in `theme.css` so the browser's view-transition "new" snapshot captures the correctly-centered slide 0 position before JS runs. Three breakpoints with exact formulas verified against `snapCenter()` output.
- Visual design polish pass (Mar 2026): header name larger (13px) with letter-spacing and tagline demoted to muted color; reduced header dead zone; increased box-shadow opacity; inactive slideshow slides dim to opacity 0.55 + scale(0.97) to focus the active image; feed image hover opacity feedback; larger slideshow arrow hit-area; date metadata margin; footer closer to nav. All with `prefers-reduced-motion` overrides.

# Open Challenges & Risks
- Gallery UX is still basic horizontal scrolling; no dedicated lightbox/zoom flow yet.
- LCP heuristics may need retuning as content changes.
- `site_url` must remain accurate for canonical/OG/sitemap correctness.
- Build time and output size may increase with larger photo libraries due JPG + WebP + AVIF variant generation.

# Next Steps
1. Decide whether to add a full lightbox interaction for multi-image posts.
2. Add snapshot-style tests for generated HTML output to catch template regressions.
3. Tune body typography against the new lorem-ipsum sample post and decide final desktop/mobile scales.
4. Backfill location metadata for existing posts where known.
5. Monitor CI deploy runs and production performance after content additions.

# Data & Conventions
- Posts live under `blog/posts/YYYY/MM/*.md`.
- Front matter delimiters must match (`+++...+++` or `++++...++++`).
- Dates must be ISO (`YYYY-MM-DD`).
- `location` can be either a string or `{ name, lat, lon }` table.
- Assets live in `blog/static/` and copy to `blog/dist/static/`.
- Keep `README.md`, `blog/README.md`, `HANDOFF.md`, and `TODO.md` aligned after significant changes.
