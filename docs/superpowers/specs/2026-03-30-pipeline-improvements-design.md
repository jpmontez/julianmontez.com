# Pipeline Improvements Design

**Date:** 2026-03-30
**Status:** Approved

## Overview

Improve the GitHub Actions pipeline for `julianmontez.com` for speed, consistency, and simplicity while demonstrating CI best practices. The pipeline validates and deploys an Astro static site to Cloudflare Pages.

## Problems with Current Pipeline

1. **Double build.** `dist/` is built in `validate`, discarded, then rebuilt from scratch in `deploy`. Every non-PR push builds twice.
2. **Vestigial schedule triggers.** Two daily cron runs were intended for a future S3 image-source feature that was never implemented. Images are stored in-repo; scheduled rebuilds serve no purpose.
3. **`cancel-in-progress: false`.** Rapid pushes queue up redundant runs rather than cancelling the stale one.
4. **Raw `npx` commands instead of npm script.** `package.json` already defines a `build` script that chains `astro check && astro build`. Using `npm run build` is more consistent and avoids divergence.
5. **Outdated action versions.** `actions/setup-node@v4` should be `actions/setup-node@v6`.

## Design

### Triggers

Remove both `schedule` entries. Keep `push` (branches: main), `pull_request` (branches: main), and `workflow_dispatch`.

### Concurrency

```yaml
concurrency:
  group: "pages"
  cancel-in-progress: true
```

`cancel-in-progress: true` ensures that when a new push lands mid-run, the stale run is cancelled. Safe for a static site where the latest build is always correct.

### `validate` job

| Step | Change |
|---|---|
| Checkout | `actions/checkout@v6` — unchanged |
| Setup Node.js | `actions/setup-node@v6` (was v4) |
| Install dependencies | `npm ci` — unchanged |
| Build | `npm run build` — replaces separate `npx astro check` + `npx astro build` |
| Upload artifact | **New.** Upload `dist/` via `actions/upload-artifact@v6`, retention 1 day |

### `deploy` job

Stripped down to two steps — no checkout, no Node setup, no `npm ci`, no build.

| Step | Change |
|---|---|
| Download artifact | **New.** Download `dist/` via `actions/download-artifact@v8` |
| Deploy to Cloudflare Pages | `cloudflare/wrangler-action@v3` — unchanged |

`needs: validate` and `if: github.event_name != 'pull_request'` are preserved.

## Artifact Passing

- **Name:** `dist`
- **Path:** `dist/`
- **Retention:** 1 day — only needs to survive the current workflow run
- Upload action: `actions/upload-artifact@v6`
- Download action: `actions/download-artifact@v8`

## Non-Changes

- `actions/checkout@v6` — confirmed valid, no change needed
- `cloudflare/wrangler-action@v3` — unchanged
- Node version — updated from `22` to `24` (latest LTS)
- `npm` cache in setup-node — unchanged
- All secrets references — unchanged
- `permissions`, `environment` blocks — unchanged
