# Project Snapshot
Static Tumblr-inspired microblog generator in Python (uv-managed). It builds a fully static site under `blog/dist` with paginated feeds and per-post pages. Current state is stable with sample content in place (20 posts) and a refreshed theme aligned to the `_refs` mocks.

# Current Status & Recent Work
- Generator: `blog/generate.py` parses TOML front matter (`+++`/`++++`), renders Markdown via Jinja2 templates, copies assets, and paginates (10 posts/page). Per-post pages live at `/YYYY/MM/slug/index.html`.
- Theme: `blog/theme.css` matches Tumblr-like monochrome layout—centered header/excerpts, left-aligned post bodies, 64px top padding on title, 36px gap to tagline. Footer shows `© {{ now.year }}`.
- Templates: `blog/templates/index.html` (feed) and `blog/templates/post.html` (post detail). Titles are not links; the meta/date links to the post page; photos are not clickable.
- Assets: Three base SVGs in `blog/static/`; Post 01 now has three images including a new portrait SVG (`2025-01-20-post-01-portrait.svg`) to show multi-image support.
- Sample content: 20 posts under `blog/posts/YYYY/MM/` with dated filenames; images randomized across the three SVGs.
- Tooling: Ruff added for lint/format; `uv run ruff format` and `uv run ruff check` succeed on the codebase.
- Packaging: Added Hatch build config and `tool.uv.package = true` with `blog/__init__.py` so `uv run generate-blog` installs its entrypoint correctly.
- CI/CD: GitHub Actions Pages workflow added at `.github/workflows/deploy.yml`; builds with uv and deploys `blog/dist` to Pages on `main`, PRs, schedule, and manual triggers.
- Favicon: `blog/favicon.png` is copied to `dist` and linked in `base.html`.
- URLs: Feed and post links omit `index.html`; posts publish as directory-style `YYYY/MM/slug/` (index.html inside). Back-to-feed/pagination use trailing slashes.
- Images now load lazily (`loading="lazy"`, `decoding="async"`) in index and post templates for performance.

# Open Challenges & Risks
- TODO.md tracks future work (gallery view for multi-photo posts). Gallery view is not implemented; current multi-image rendering simply stacks images.
- `tool.uv.dev-dependencies` is deprecated; expect to move to `dependency-groups.dev` in pyproject soon.

# Next Steps (Actionable)
1) Implement gallery/lightbox for multi-image posts on per-post pages (`blog/templates/post.html`, `blog/theme.css`, potentially JS if added). Reference TODO.md.
2) Migrate uv config to `dependency-groups.dev` in `pyproject.toml` to silence the warning.
3) Monitor the Pages workflow on first runs; verify the deployed site renders correctly and adjust caching/paths if needed.
Run `uv run generate-blog` after changes; check `blog/dist` output.

# Environment & Tooling
- Python 3.11+; package manager: uv (`uv sync`).
- Entrypoints: `uv run generate-blog` (or `uv run python blog/generate.py`).
- Lint/format: `uv run ruff format` then `uv run ruff check`.
- Config: `blog/config.toml` (title, tagline, description, optional `base_url` for correct asset linking when hosted).

# Data, Artifacts & Contracts
- Content: `blog/posts/YYYY/MM/*.md` with dated filenames (e.g., `2025-01-20-post-01.md`), TOML front matter with `title`, `date` (ISO), `images` (list of paths under `static/`), optional `excerpt`, `layout`.
- Assets: `blog/static/` (copied to `dist/static/`). New portrait SVG: `blog/static/2025-01-20-post-01-portrait.svg`.
- Output: `blog/dist/` (rebuilt by generator). Pagination lives under `blog/dist/page/N/`; posts under `blog/dist/YYYY/MM/slug/`.

# Testing & Quality
- No automated tests; rely on generator run and browser preview.
- Commands: `uv run generate-blog`; `uv run ruff format`; `uv run ruff check`.

# Gotchas & Conventions
- Front matter delimiter must be `+++` or `++++`; dates must be ISO (`YYYY-MM-DD`).
- Filenames for posts and images are date-prefixed (`YYYY-MM-DD-slug.{md,svg}`) and nested by `YYYY/MM/`.
- Titles are not clickable; only the date/meta links to the post page. Images are not links.
- Excerpts are centered in the feed; post bodies are left-aligned. Keep header spacing (64px top, 36px title-to-tagline) and centered layout unless intentionally changing the theme.
- If hosting under a subpath, set `base_url` in `blog/config.toml` so asset links resolve correctly.
