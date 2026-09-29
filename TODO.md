# TODO

- Keep monitoring mobile LCP as new content lands; a large first photo is the main risk to the 100 score (local Lighthouse mobile LCP 1.1s, 100 needs < ~1.55s).
- Optional: disable Cloudflare Web Analytics if unused; its `beacon.min.js` is the only remaining "legacy JavaScript" / short-cache flag in PageSpeed Insights.

## Cloudflare `cf` + IaC migration (branch `feat/cf-iac`)

Finish the cutover (dashboard; the site already runs on the Worker):
- Remove the account-level Bulk Redirect: Manage account → Bulk Redirects → delete the rule, then delete the `redirect_www_to_domain_apex` list. The zone redirect rule in `infra/` already handles www→apex.
- Pages project `julianmontez-com`: disconnect its GitHub integration now; delete the project once the Worker has run for a while without issues. Rollback until then: detach the domain from the Worker, re-add it to Pages.
- GitHub: delete the `cloudflare-pages` environment and its secrets (`CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_PROJECT_NAME`).
- Push `feat/cf-iac`, open a PR, confirm the `validate` and `infra` jobs pass, merge.
- Confirm the Web Analytics beacon still loads in a browser (curl can't see it) and data arrives in Analytics → Web analytics.
- Watch Security → Events for WAF false positives (feed readers, link previews, monitors, your own VPN) and tune `waf_custom_rules`.

Credentials:
- 1Password (Personal vault), at the end of this migration: review and improve the six items suffixed `— julianmontez.com` using the 1Password CLI (`op item get/edit`, never printing secret values): `CLOUDFLARE_TF_READ_TOKEN`, `CLOUDFLARE_DEPLOY_TOKEN`, `CLOUDFLARE_TF_APPLY_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `TF_VAR_state_passphrase` and `Cloudflare API Token`. For each: a clear title, what it's for, the Cloudflare token name and exact permissions (README › Credentials setup), where it's stored (GitHub secret/environment name, `.env` variable), rotation guidance, and links to the Cloudflare API Tokens page and the repo's GitHub settings. `Cloudflare API Token` is likely the old Pages deploy token: confirm, then revoke it in Cloudflare and archive the item after cutover.

Accessibility:
- Fix Lighthouse's "Links rely on color to be distinguishable" (axe `link-in-text-block`, accessibility 92) for the header "Email" link: `header.site .tagline a` removes the underline, so the link differs from the surrounding tagline text only by color. Give it a non-color cue (e.g. underline) and re-run Lighthouse.

Follow-ups:
- Move to Node 26 once it enters LTS: update `engines.node` in `package.json`.
- Unpin `cf` from `1.0.0-beta.5` when it reaches GA.
- Switch deploys from `wrangler deploy` to `cf deploy` once [cloudflare/cf#18](https://github.com/cloudflare/cf/issues/18) is fixed (fallback to the Wrangler assets path for detected frameworks); then replace `wrangler.jsonc` via `npx cf migrate` and re-run `cf deploy --dry-run`.
- Move zone config (DNS, settings) into `cf`'s declarative config once it supports zones; drop the matching `infra/` resources.
- Run `npx cf auth logout` to revoke the broad (469-scope) OAuth login used during research.
