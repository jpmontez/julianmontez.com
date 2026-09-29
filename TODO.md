# TODO

- Keep monitoring mobile LCP as new content lands; a large first photo is the main risk to the 100 score (local Lighthouse mobile LCP 1.1s, 100 needs < ~1.55s).
- Optional: disable Cloudflare Web Analytics if unused; its `beacon.min.js` is the only remaining "legacy JavaScript" / short-cache flag in PageSpeed Insights.

## Cloudflare

Monitoring:
- Watch Security → Events for WAF false positives (feed readers, link previews, monitors, your own VPN) and tune `waf_custom_rules`.

Credentials:
- Revoke the old Pages deploy token (Cloudflare → My Profile → API Tokens; token ID `3e3095a2…`, still active and no longer used), then archive the 1Password item `Cloudflare API Token — julianmontez.com`.

Follow-ups:
- Move to Node 26 once it enters LTS: update `engines.node` in `package.json`.
- Unpin `cf` from `1.0.0-beta.5` when it reaches GA.
- Switch deploys from `wrangler deploy` to `cf deploy` once [cloudflare/cf#18](https://github.com/cloudflare/cf/issues/18) is fixed (fallback to the Wrangler assets path for detected frameworks); then replace `wrangler.jsonc` via `npx cf migrate` and re-run `cf deploy --dry-run`.
- Move zone config (DNS, settings) into `cf`'s declarative config once it supports zones; drop the matching `infra/` resources.
