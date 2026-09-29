# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Orientation

Before starting any task, read these files in order (they are the single source of truth):
1. `README.md` — project overview, setup, commands, content format
2. `TODO.md` — active task queue

After completing work: update `TODO.md` (mark done, add new). Only update `README.md` if user-facing setup or commands changed.

## Commands

Node 24 LTS only (`engines.node` + `engine-strict=true` in `.npmrc`); locally use Homebrew `node@24`. No global npm installs; run tools with `npx`.

```bash
# Install dependencies
npm install

# Build (static output in dist/)
npx astro build

# Preview (dev server at http://localhost:4321)
npx astro dev

# Type check
npx astro check

# Deploy dist/ to Cloudflare Workers via wrangler (build first; needs .env loaded: set -a; source .env; set +a)
npm run deploy

# Cloudflare zone infrastructure (from infra/)
tofu fmt -recursive && tofu validate
tofu plan -out=change.tfplan && tofu apply change.tfplan
terraform-docs .        # refresh the generated section of infra/README.md
```

## Architecture

This is an **Astro static site** — a photo-centric microblog. The build pipeline:

```
astro.config.mjs        → Astro config (plain static output in dist/)
wrangler.jsonc          → assets-only Worker config (dist/, trailing slashes, 404 page); name/domain passed as deploy flags from WORKER_NAME/SITE_DOMAIN
infra/                  → OpenTofu config for the Cloudflare zone (see infra/README.md)
src/content.config.ts   → content collection schema (Zod) for posts
src/content/posts/      → Markdown posts with YAML front matter
src/assets/photos/      → full-resolution source images (processed at build time)
src/config.ts           → site config (title, pagination, image sizes)
src/utils.ts            → getPosts, postSlug, displayDate, imageSrcsets (shared responsive variants)
src/layouts/
  BaseLayout.astro      → base HTML layout (meta, OG, preload, feed link, skip link)
src/components/
  Feed.astro            → feed page body (posts, LCP preload, pagination nav)
  PostImage.astro       → responsive <picture> with AVIF/WebP/native srcset
  Slideshow.astro       → multi-image horizontal slideshow with JS nav
src/pages/
  404.astro             → not-found page (assets notFoundHandling: 404-page)
  index.astro           → paginated feed (page 1)
  page/[page].astro     → paginated feed (pages 2+)
  [...slug].astro       → individual post pages at /YYYY/MM/slug/
  feed.xml.ts           → RSS feed
  rss.xml.ts            → same feed at a legacy URL
src/styles/
  theme.css             → global stylesheet (inlined into all pages)
```

**Key architectural facts:**
- `src/styles/theme.css` is the single stylesheet — imported globally via BaseLayout
- Post titles are intentionally hidden in rendered output; visible only in metadata/feeds
- Multi-image posts render as a horizontal slideshow on post pages and a vertical stack in the feed
- The feed's LCP preload is AVIF-only and uses `imageSrcsets()` so its URLs match `PostImage` exactly
- `src/config.ts` controls title, tagline, pagination, image sizes
- Only the feed's first image loads eagerly. Extra eager images download alongside the LCP image on Lighthouse's throttled mobile profile and cost LCP points (1.8s → 1.1s when removed)
- The header email link ships XOR-encoded (`data-email`) and a tiny inline script in `BaseLayout.astro` builds the `mailto:` in the browser. Cloudflare Email Obfuscation doesn't apply to Worker responses, so never render the address as plain text anywhere in the HTML
- Images in `src/assets/photos/` are processed by Astro's sharp pipeline at build time
- Deploys use Wrangler, not `cf`, until [cloudflare/cf#18](https://github.com/cloudflare/cf/issues/18) is fixed. Don't add `@astrojs/cloudflare`: it moves output to `dist/client/` and adds a Worker script plus session KV and Images binding defaults this static site doesn't need

**View transitions & slideshow patterns (`src/styles/theme.css`, `src/components/Slideshow.astro`):**
- Cross-document view transitions enabled via `@view-transition { navigation: auto }` (CSS only)
- `.slideshow-track` CSS initial `transform: translateX(calc(...))` — **do not remove it**. It pre-centers slide 0 so the view-transition snapshot is correct before JS runs; removing it causes a visible jump on crossfade.
- `snapCenter()` (inline JS in `Slideshow.astro`) uses `transition: none` → `centerSlide()` → force reflow → restore transition. This pattern must be preserved for resize/load events; breakpoint formulas must exactly match the CSS initial transforms.

## Content Format

Posts live at `src/content/posts/YYYY-MM-DD-slug.md` with YAML front matter:

```markdown
---
date: 2024-10-12
title: "Optional title"
images:
  - src: ../../assets/photos/2024-10-12-photo.jpg
    alt: "Alt text."
---

Markdown body.
```

- Image `src` paths are relative from `src/content/posts/` to `src/assets/photos/`
- At least one image is required
- `title` is optional and intentionally not rendered on the page

## Deployment

Push to `main` triggers the GitHub Actions workflow in `.github/workflows/deploy.yml`:
- `validate` job (PRs only): `npm ci` + `npm run build` (`astro check` + `astro build`)
- `infra` job (PRs and pushes): `tofu fmt -check`, `tofu validate`, terraform-docs check, `tofu plan -detailed-exitcode` as a drift check. **CI never runs `tofu apply`**; apply locally and commit the encrypted `infra/terraform.tfstate`.
- `deploy` job (non-PR only, independent of `infra`): `npm ci` + `npm run build` + `npm run deploy` → `wrangler deploy --name "$WORKER_NAME" --domain "$SITE_DOMAIN"`: an assets-only Worker (no script) serving `dist/` per `wrangler.jsonc`

Ownership split — never manage a resource from both tools:
- Wrangler / `wrangler.jsonc` + deploy flags: the Worker, its assets, its custom domain and the DNS record Cloudflare creates for it
- `cf` (not installed; `npx` fetches it on demand) is for inspection/admin only (`npx cf dns records export`, `npx cf zones settings get …`)
- OpenTofu / `infra/`: zone, all other DNS records, zone settings, www→apex redirect rule, Web Analytics
- No personal values in `infra/*.tf` or `wrangler.jsonc`; site-specific data lives only in `infra/terraform.tfvars`, GitHub repo variables/secrets, and `.env` (gitignored)
