# TODO

- Re-export the 13 photos that are 2048px on the long edge at 2560px or more (only DSC_0411 is full size); on 2× screens landscapes currently display about 1.25× upscaled.
- Run Lighthouse mobile on `/` after the redesign deploys; local LCP is 1.4s with the larger photo variants, close to the ~1.55s limit for a 100 score.
- After deploy, check `/page/2/` redirects to `/index/` and an old photo URL (e.g. `/2026/02/2026-02-21-photos/`) redirects to its new one (Workers `_redirects`).
- Optional: drop Cloudflare Web Analytics if unused (delete `infra/analytics.tf`); its `beacon.min.js` is the only remaining "legacy JavaScript" / short-cache flag in PageSpeed Insights.

## SEO

- Link back to the site from the Instagram and GitHub profiles listed in `sameAs` (`src/config.ts`).
- Search Console: submit `sitemap-index.xml`; check Pages → "Crawled – currently not indexed". Import the site into Bing Webmaster Tools.
- After deploy, run Google's Rich Results Test on a photo URL and the homepage.

## Cloudflare

Monitoring:
- Watch Security → Events for WAF false positives (feed readers, link previews, monitors, your own VPN) and tune `waf_custom_rules`.

Credentials:
- Revoke the old Pages deploy token (Cloudflare → My Profile → API Tokens; token ID `3e3095a2…`, still active and no longer used), then archive the 1Password item `Cloudflare API Token — julianmontez.com`.

Follow-ups:
- Move to Node 26 once it enters LTS: update `engines.node` in `package.json`.
- Switch deploys from `wrangler deploy` to `cf deploy` once [cloudflare/cf#18](https://github.com/cloudflare/cf/issues/18) is fixed (fallback to the Wrangler assets path for detected frameworks); then replace `wrangler.jsonc` via `npx cf migrate` and re-run `cf deploy --dry-run`.
- Move zone config (DNS, settings) into `cf`'s declarative config once it supports zones; drop the matching `infra/` resources.
