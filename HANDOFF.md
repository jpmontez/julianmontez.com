# Project Snapshot
Static Tumblr-inspired microblog generator in Python (uv-managed). It builds a fully static site under `blog/dist` with paginated feeds, per-post pages, and basic SEO primitives (canonical/OG tags + sitemap). Current state is stable with sample content in place (10 posts).

# Current Status & Recent Work
- Generator: `blog/generate.py` parses TOML front matter (`+++`/`++++`), renders Markdown via Jinja2 templates, copies assets, and paginates (10 posts/page). Per-post pages live at `/YYYY/MM/slug/index.html`.
- Theme: `blog/theme.css` matches Tumblr-like monochrome layout—centered header/excerpts, left-aligned post bodies, 64px top padding on title, 36px gap to tagline. Footer shows `© {{ now.year }}`.
- Templates: `blog/templates/index.html` (feed) and `blog/templates/post.html` (post detail). Titles are not links; the meta/date links to the post page; photos are not clickable.
- Sample content: 10 photo posts under `blog/posts/YYYY/MM/` with dated filenames and matching JPGs in `blog/static/`.
- Tooling: Ruff is available via uv (dev dependency group); `uv run ruff format` and `uv run ruff check` succeed on the codebase.
- Packaging: Added Hatch build config and `tool.uv.package = true` with `blog/__init__.py` so `uv run generate-blog` installs its entrypoint correctly.
- Generator now reads static image dimensions (JPEG/PNG via Pillow) and emits width/height on `<img>` tags in index/post templates; `<main role="main">` added around primary content to satisfy accessibility/landmark checks.
- Generator now creates responsive raster variants (480/720/1080 widths where applicable) and emits `srcset`/`sizes`; the first `eager_images` images (default: 2) load eagerly, and the generator picks the likely mobile LCP image among them for `fetchpriority="high"` + a preload directive.
- Generator enables Jinja2 autoescape and emits canonical + basic OpenGraph meta tags on pages; it also writes `dist/sitemap.xml` and keeps `dist/robots.txt` pointed at it.
- `blog/config.toml` now sets `site_url` to emit fully-qualified canonical/OG URLs and absolute sitemap locs (fixes PageSpeed/Lighthouse `rel=canonical` absolute-URL audit).
- Generator now ensures the `Sitemap:` directive in `dist/robots.txt` is always absolute (or omitted if an absolute base URL can't be determined), to satisfy Lighthouse/PageSpeed validation.
- Posts can define per-image alt text via TOML front matter (e.g. `images = [{ src = "static/...", alt = "..." }]`); templates use it for `<img alt="">`.
- CI/CD: GitHub Actions workflow at `.github/workflows/deploy.yml` builds with uv and deploys `blog/dist` to Cloudflare Pages via `cloudflare/wrangler-action@v3` (secrets: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_PROJECT_NAME`); runs on main, PRs, schedule, and manual triggers.
- Favicon: `blog/favicon.png` is copied to `dist` and linked in `base.html`.
- Robots: `blog/robots.txt` added with Cloudflare content-signal directives, bot blocks, and /lp,/feedback,/langtest disallows; generator copies it to the dist root.
- URLs: Feed and post links omit `index.html`; posts publish as directory-style `YYYY/MM/slug/` (index.html inside). Back-to-feed/pagination use trailing slashes.
- Images now load lazily (`loading="lazy"`, `decoding="async"`) in index and post templates for performance.
- CSS is now inlined from `theme.css` (and Google Fonts import removed) to avoid render-blocking requests; `style.css` is still written but not referenced.
- Helper script: `scripts/import_lightroom.py` scans `~/Desktop` for Lightroom JPG exports (`YYYYMMDD-DSC_NNNN.jpg`), copies them into `blog/static/`, and scaffolds `blog/posts/YYYY/MM/*.md` with the photo front matter; prompts for a custom slug when multiple photos share a date; prompts before overwriting an existing asset (pass `--overwrite` to force); uses logging; originals on Desktop stay untouched.

# Open Challenges & Risks
- TODO.md tracks future work (gallery view for multi-photo posts). Gallery view is not implemented; current multi-image rendering simply stacks images.
- PageSpeed (mobile): monitor for LCP regressions as new photos/content change which above-the-fold image becomes LCP; generator now applies eager loading + `fetchpriority` + preload to the likely LCP image.
- New dependency: Pillow for reading intrinsic image dimensions during generation; ensure environments install it (`uv sync`) before running the generator.
- Ensure `site_url` remains accurate for the canonical domain (used for canonical/OG tags and sitemap locs).

# Next Steps (Actionable)
1) Implement gallery/lightbox for multi-image posts on per-post pages (`blog/templates/post.html`, `blog/theme.css`, potentially JS if added). Reference TODO.md.
2) If hosting under a subpath, set `base_url` in `blog/config.toml` so asset links resolve correctly.
3) Monitor the Pages workflow on first runs; verify the deployed site renders correctly and adjust caching/paths if needed.
Run `uv run generate-blog` after changes; check `blog/dist` output.

# Environment & Tooling
- Python 3.11+; package manager: uv (`uv sync`).
- Entrypoints: `uv run generate-blog` (or `uv run python blog/generate.py`).
- Lint/format: `uv run ruff format` then `uv run ruff check`.
- Config: `blog/config.toml` (title, tagline, description, optional `site_url` for absolute canonical/sitemap URLs, optional `base_url` for correct asset linking when hosted).
- Makefile: `make install` (uv sync), `make build` (install + generate), `make preview` (serve `blog/dist` on :8080 after build), `make clean`/`distclean` (remove `blog/dist`; `distclean` also removes `.uv`/`.venv`), `make import [LIGHTROOM_EXPORT_DIR=~/Desktop]` (run import script), `make format`/`lint`/`check` (Ruff), `make regen` (clean + build).

# Data, Artifacts & Contracts
- Content: `blog/posts/YYYY/MM/*.md` with dated filenames (e.g., `2025-01-20-post-01.md`), TOML front matter with `title`, `date` (ISO), `images` (list of paths under `static/`), optional `excerpt`, `layout`.
- Assets: `blog/static/` (copied to `dist/static/`).
- Output: `blog/dist/` (rebuilt by generator). Pagination lives under `blog/dist/page/N/`; posts under `blog/dist/YYYY/MM/slug/`.

# Testing & Quality
- No automated tests; rely on generator run and browser preview.
- Commands: `uv run generate-blog`; `uv run ruff format`; `uv run ruff check`.

# Gotchas & Conventions
- Front matter delimiter must be `+++` or `++++`; dates must be ISO (`YYYY-MM-DD`).
- Filenames for posts and images are date-prefixed (`YYYY-MM-DD-slug.{md,jpg,png}`) and nested by `YYYY/MM/`.
- Titles are not clickable; only the date/meta links to the post page. Images are not links.
- Excerpts are centered in the feed; post bodies are left-aligned. Keep header spacing (64px top, 36px title-to-tagline) and centered layout unless intentionally changing the theme.
- If hosting under a subpath, set `base_url` in `blog/config.toml` so asset links resolve correctly.
