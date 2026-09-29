# TODO

- Keep monitoring mobile LCP as new content lands; a large first photo is the main risk to the 100 score (local Lighthouse mobile LCP 1.1s, 100 needs < ~1.55s).
- Optional: disable Cloudflare Web Analytics if unused; its `beacon.min.js` is the only remaining "legacy JavaScript" / short-cache flag in PageSpeed Insights.

## Cloudflare `cf` + IaC migration (branch `feat/cf-iac`)

Cutover (with the site owner present):
1. Deploy the Worker and verify it on `*.workers.dev` (routes, trailing slashes, feeds, sitemap, `/_astro/*` cache headers, 404 on a bogus path).
2. Remove `julianmontez.com` from the Pages project and delete the apex CNAME to `julianmontez-com.pages.dev`.
3. `npm run deploy` so Wrangler attaches the custom domain to the Worker.
4. `tofu apply` the zone-level www→apex redirect, verify the 301, then remove the account-level Bulk Redirect ruleset and the `redirect_www_to_domain_apex` list.
5. Disconnect the Pages project's GitHub integration.
6. Delete the Pages project after ~1 week of soak. Rollback until then: re-add the domain and CNAME to Pages.
- Re-verify Lighthouse mobile LCP (still 100) after cutover.
- Confirm the Web Analytics beacon and Cloudflare Email Obfuscation still inject.
- Set `ssl = "strict"` (Full (strict)) in `zone_settings` (currently `flexible`) and apply.
- Watch Security → Events for WAF false positives (feed readers, link previews, monitors, your own VPN) and tune `waf_custom_rules`.

Credentials:
- 1Password (Personal vault), at the end of this migration: review and improve the six items suffixed `— julianmontez.com` using the 1Password CLI (`op item get/edit`, never printing secret values): `CLOUDFLARE_TF_READ_TOKEN`, `CLOUDFLARE_DEPLOY_TOKEN`, `CLOUDFLARE_TF_APPLY_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `TF_VAR_state_passphrase` and `Cloudflare API Token`. For each: a clear title, what it's for, the Cloudflare token name and exact permissions (README › Credentials setup), where it's stored (GitHub secret/environment name, `.env` variable), rotation guidance, and links to the Cloudflare API Tokens page and the repo's GitHub settings. `Cloudflare API Token` is likely the old Pages deploy token: confirm, then revoke it in Cloudflare and archive the item after cutover.

Follow-ups:
- Move to Node 26 once it enters LTS: update `engines.node` in `package.json`.
- Unpin `cf` from `1.0.0-beta.5` when it reaches GA.
- Switch deploys from `wrangler deploy` to `cf deploy` once [cloudflare/cf#18](https://github.com/cloudflare/cf/issues/18) is fixed (fallback to the Wrangler assets path for detected frameworks); then replace `wrangler.jsonc` via `npx cf migrate` and re-run `cf deploy --dry-run`.
- Move zone config (DNS, settings) into `cf`'s declarative config once it supports zones; drop the matching `infra/` resources.
- Run `npx cf auth logout` to revoke the broad (469-scope) OAuth login used during research.
