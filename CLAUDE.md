# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Orientation

Before starting any task, read these files in order (they are the single source of truth):
1. `README.md` — project overview, setup, commands, content format
2. `TODO.md` — active task queue

After completing work: update `TODO.md` (mark done, add new). Only update `README.md` if user-facing setup or commands changed.

## Commands

Node 26 LTS only (`engines.node` + `engine-strict=true` in `.npmrc`); locally use Homebrew `node`. No global npm installs; run tools with `npx`.

```bash
# Install dependencies
npm install

# Build (static output in .cloudflare/output/v0/workers/default/assets/)
npx astro build

# Preview (dev server at http://localhost:4321)
npx astro dev

# Type check
npx astro check

# Build and deploy to Cloudflare Workers via `cf deploy` (needs .env loaded: set -a; source .env; set +a)
npm run deploy

# Cloudflare zone infrastructure (from infra/)
tofu fmt -recursive && tofu validate
tofu plan -out=change.tfplan && tofu apply change.tfplan
terraform-docs .        # refresh the generated section of infra/README.md
```

## Architecture

This is an **Astro static site** — a photo-centric microblog. The build pipeline:

```
astro.config.mjs        → Astro config (static output; @astrojs/cloudflare adapter, Sharp at build time, sessions off)
cloudflare.config.ts    → assets-only Worker config for `cf` (trailing slashes, 404 page, custom domain); name/domain from WORKER_NAME/SITE_DOMAIN
infra/                  → OpenTofu config for the Cloudflare zone (see infra/README.md)
src/content.config.ts   → content collection schema (Zod) for posts
src/content/posts/      → Markdown posts with YAML front matter
src/assets/photos/      → full-resolution source images (processed at build time)
src/config.ts           → site config (title, email, description, feed size)
src/slug.mjs            → photoPath: post file name → URL path (shared by utils.ts and astro.config.mjs sitemap dates)
src/utils.ts            → getPosts, postSlug, fullDate/shortDate, caption, dateline, postDescription, imageSrcsets, photoSizes, thumbnail, emailKey/encodedEmail
src/layouts/
  BaseLayout.astro      → base HTML layout (meta, OG, preload, feed link, skip link, header with Index/Info/Email)
src/components/
  PhotoPage.astro       → photo page: one photo, caption, Previous/n of total/Next, arrow keys, next-image preload
  ContactSheet.astro    → contact sheet: numbered thumbnail grid, label, Previous/Sheet n of N/Next/Close, ?from= and keys
src/pages/
  404.astro             → not-found page (assets notFoundHandling: 404-page)
  index.astro           → newest photo (PhotoPage)
  index/index.astro     → /index/: every photo grouped by year, with thumbnails
  info.astro            → /info/: birth year and place, where based, email
  [...slug].astro       → each photo's page at /YYYY/MM/dsc-0391/ (PhotoPage; the whole path comes from the post's file name, never from `date:`)
  contact-sheet/[sheet].astro → /contact-sheet/N/: 36 frames per sheet (ContactSheet)
  feed.xml.ts           → RSS feed
  rss.xml.ts            → same feed at a legacy URL
src/styles/
  theme.css             → global stylesheet (inlined into all pages)
```

**Key architectural facts:**
- `src/styles/theme.css` is the single stylesheet — imported globally via BaseLayout
- Post titles are intentionally hidden in rendered output; visible only in metadata/feeds
- Every post is exactly one photo (`images` has `.max(1)`); order is newest first, same-day posts by file name descending. "Next" goes older; the ends show grey text (#6b6b6b) instead of wrapping
- Three plain `<a href>` click zones overlay the photo (box sized to the image): top third → its contact sheet frame (`?from=` + `#frame-N`), bottom-left → Previous, bottom-right → Next. On desktop, hovering/focusing the top third reveals a grey "Contact sheet" label centred in the header (`.zone-label`, BaseLayout `sheetLabel`); phones get a "Contact sheet" link in the bottom nav instead. Navigation works without JS; the inline script only adds arrow keys, swipe left/right on touch screens, and preloads the next image
- The photo `<img>` gets an explicit CSS width from inline `--w`/`--ratio` matching `photoSizes()`, so its box is final before the image loads (no layout shift)
- The photo page's LCP preload is AVIF-only and uses `imageSrcsets()` + `photoSizes()` so its URLs match the `<picture>` exactly. `photoSizes()` must match the `.photo img` max-width/max-height in `theme.css`
- `/page/*` (the old paginated feed) redirects to `/index/` via `public/_redirects`
- Email links ship XOR-encoded (`data-email`, from `utils.ts`) and a tiny inline script in `BaseLayout.astro` builds the `mailto:` in the browser; `data-email-text` also makes the link show the address (Info page). Cloudflare Email Obfuscation doesn't apply to Worker responses, so never render the address as plain text anywhere in the HTML
- Favicon: `public/favicon.png` is a 96px "JM" in Times New Roman Bold (Google needs a square that's a multiple of 48px); `public/apple-touch-icon.png` is 180px in Regular. Both are rendered from the font outlines, not screenshots
- Images in `src/assets/photos/` are processed by Astro's sharp pipeline at build time
- Deploys use `cf deploy` through `@astrojs/cloudflare` (pinned beta, 15.0.0-beta.5: the first adapter that supports `cf`). Keep `imageService: 'custom'`, `prerenderEnvironment: 'node'` and `session: false`: otherwise the adapter swaps out Sharp and adds session KV and Images bindings this static site doesn't need. The Worker must stay assets-only (`cf deploy --dry-run` lists only `env.ASSETS`)

**Design tokens (`src/styles/theme.css`):** Times stack only (no webfonts), 15px/1.4 (16px at ≥1600px, 17px at ≤600px); colors #fff, #000, #6b6b6b (secondary, dead-end nav text), #e4e4e4 (rules only; fails contrast as text) and nothing else. Dark mode follows the system via `color-scheme: light dark` (meta in BaseLayout + `:root`) and `light-dark()` tokens: #000 bg, #fff ink, #949494 secondary, #1f1f1f rules; in dark mode photos get a 1px `--rule` hairline (low-key photos otherwise dissolve into black) and text uses `-webkit-font-smoothing: antialiased`; this also keeps Safari's Adaptive Dark Mode from recolouring the page. Never hard-code a colour outside the four tokens. Links underline on hover only. Every tap target is ≥44px tall via vertical padding. Cross-document page fade via `@view-transition { navigation: auto }` (CSS only).

## Content Format

Posts live at `src/content/posts/YYYY-MM-DD-slug.md` with YAML front matter:

```markdown
---
date: 2024-10-12
title: "Optional, e.g. Crown Heights North"
images:
  - src: ../../assets/photos/2024-10-12-photo.jpg
    alt: "Alt text."
---
```

Post bodies aren't rendered; the photo and its caption are the whole page.

- The file name sets the URL (`2026-02-21-DSC_0391.md` → `/2026/02/dsc-0391/`); `date:` sets the order and the shown date. Renaming a live post's file changes its URL, so add the old path to `public/_redirects` (the build fails if a redirect target doesn't exist)
- Image `src` paths are relative from `src/content/posts/` to `src/assets/photos/`
- Exactly one image per post
- `title` is optional; it's shown before the date ("Crown Heights North, 16 May 2026" in the caption and `<title>`, `Crown Heights North | 16 May 2026` in RSS), names the photo in the index and contact sheet, and leads the meta description. Usually a neighbourhood or a short name for the photo; never exact coordinates

## Deployment

Push to `main` triggers the GitHub Actions workflow in `.github/workflows/deploy.yml`:
- `validate` job (PRs only): `npm ci` + `npm run build` (`astro check` + `astro build`)
- Both build jobs restore Astro's encoded images (`node_modules/.astro/assets`) with `actions/cache`, keyed on `src/assets/photos/**`, so only new photos are encoded. A cold build is ~1,000 CPU-seconds and already uses every core
- `infra` job (PRs and pushes): `tofu fmt -check`, `tofu validate`, terraform-docs check, `tofu plan -detailed-exitcode` as a drift check. **CI never runs `tofu apply`**; apply locally and commit the encrypted `infra/terraform.tfstate`.
- `deploy` job (non-PR only, independent of `infra`): `npm ci` + `npm run build` + `npm run deploy` → `cf deploy`: an assets-only Worker (no script) per `cloudflare.config.ts`

Ownership split — never manage a resource from both tools:
- `cf deploy` / `cloudflare.config.ts` + WORKER_NAME/SITE_DOMAIN: the Worker, its assets, its custom domain and the DNS record Cloudflare creates for it
- `cf` (pinned devDependency) also handles inspection/admin (`npx cf dns records export`, `npx cf zones settings get …`)
- OpenTofu / `infra/`: zone, all other DNS records, zone settings, www→apex redirect rule, Web Analytics
- No personal values in `infra/*.tf` or `cloudflare.config.ts`; site-specific data lives only in `infra/terraform.tfvars`, GitHub repo variables/secrets, and `.env` (gitignored)
