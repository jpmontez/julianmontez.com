# Cloudflare infrastructure

OpenTofu configuration for everything on the Cloudflare zone except the Worker
that serves the site. Fork the repo, edit `terraform.tfvars`, set a few
environment variables, and `tofu apply` recreates the whole setup on the free
plan.

## Architecture

```
GitHub push ─► Actions ─┬─ validate: npm ci, astro check, astro build
                        ├─ deploy:   npm run deploy (wrangler) ─► assets-only Worker + custom domain
                        └─ infra:    tofu fmt/validate/plan  ─► read-only drift check (no apply in CI)

Laptop ─────────────────── tofu apply ─► zone, DNS, zone settings, redirects, WAF, bots, Web Analytics
```

Each resource has exactly one owner. Never manage the same resource from both
tools ([Cloudflare's guidance](https://developers.cloudflare.com/terraform/advanced-topics/best-practices/)).

| Owner | Resources | Source of truth |
|---|---|---|
| Wrangler (`npm run deploy`) | Worker, its static assets, its custom domain and the DNS record Cloudflare creates for that domain | `wrangler.jsonc` + `WORKER_NAME`/`SITE_DOMAIN` |
| OpenTofu (this directory) | Zone, all other DNS records, zone settings, www→apex redirect rule, WAF custom rules, Bot Fight Mode, Web Analytics site | `*.tf` + `terraform.tfvars` |

| File | Contents |
|---|---|
| `versions.tf` | OpenTofu and provider pins, state/plan encryption |
| `provider.tf` | Cloudflare provider (token from `CLOUDFLARE_API_TOKEN`) |
| `variables.tf` | All inputs, typed and validated |
| `zone.tf`, `dns.tf`, `settings.tf`, `redirects.tf`, `waf.tf`, `bots.tf`, `analytics.tf` | One file per product |
| `imports.tf` | Import blocks driven by `var.adopt`; do nothing for a fresh setup |
| `outputs.tf` | Zone ID, nameservers, Web Analytics site tag |
| `terraform.tfvars` | **The only file with site-specific values.** Replace it with your own |
| `terraform.tfvars.example` | Commented template |
| `terraform.tfstate` | Encrypted state, committed on purpose (see [State](#state)) |

## Prerequisites

- [OpenTofu](https://opentofu.org) ≥ 1.12: `brew install opentofu`
- A Cloudflare account on any plan (everything here fits the free plan)
- Adopting an existing zone only: [cf-terraforming](https://github.com/cloudflare/cf-terraforming): `brew install cloudflare/cloudflare/cf-terraforming`

## Environment variables

Nothing below goes into a committed file. Locally, keep them in the gitignored
`.env` at the repo root and load it with `set -a; source ../.env; set +a`.

| Variable | Secret? | Purpose |
|---|---|---|
| `CLOUDFLARE_API_TOKEN` | yes | API token for the provider. Read-only for `plan`; edit rights (see below) for `apply` |
| `TF_VAR_account_id` | no | Cloudflare account ID (dashboard → any zone → Overview, or `npx cf accounts list`) |
| `TF_VAR_zone_name` | no | Apex domain, e.g. `example.com`. CI maps it from the `SITE_DOMAIN` repository variable |
| `TF_VAR_state_passphrase` | yes | ≥ 16 characters; encrypts state and plan files. Store it in a password manager |

API token permissions:
- **Token scopes:** exact dashboard permissions for `<site>-tf-read` (CI `plan`, adoption) and `<site>-tf-apply` (local `tofu apply` only) are in the root [README › Credentials setup](../README.md#credentials-setup).

## Fresh setup (new site)

1. Copy the template and describe your records:
   ```sh
   cp terraform.tfvars.example terraform.tfvars
   ```
   List every record except the apex site record; the Worker custom domain creates that one.
2. Delete the committed `terraform.tfstate` (it belongs to the original site and is encrypted with its passphrase).
3. Initialise and apply:
   ```sh
   tofu init
   tofu plan -out=site.tfplan
   tofu apply site.tfplan
   ```
4. Point your registrar at the `name_servers` output.
5. Commit `terraform.tfvars` and the new encrypted `terraform.tfstate`.
6. Set `zone_id` from the output as `CLOUDFLARE_ZONE_ID` wherever you run `cf`.

## Adopting an existing zone

Use this when the zone already exists and was configured in the dashboard.

1. Get IDs of what exists (read-only):
   ```sh
   export CLOUDFLARE_API_TOKEN=...   # read-only is enough
   cf-terraforming generate --zone "$ZONE_ID" --resource-type cloudflare_dns_record
   cf-terraforming import   --zone "$ZONE_ID" --resource-type cloudflare_dns_record \
     --modern-import-block --terraform-binary-path "$(command -v tofu)"
   cf-terraforming generate --zone "$ZONE_ID" --resource-type cloudflare_ruleset
   cf-terraforming generate --account "$TF_VAR_account_id" --resource-type cloudflare_web_analytics_site
   ```
   `npx cf dns records list` gives the same record IDs as JSON.
2. Translate the output into `terraform.tfvars`: records into `dns_records`, and IDs into `adopt`:
   ```hcl
   adopt = {
     zone_id               = "<zone id>"
     dns_records           = { mx_1 = "<record id>", spf = "<record id>" } # same keys as dns_records
     www_record_id         = "<id of the proxied www placeholder record>"
     redirect_ruleset_id   = "<http_request_dynamic_redirect entry point id>"
     web_analytics_site_id = "<site tag>"
   }
   ```
   Every key in `zone_settings` is imported when `adopt.zone_id` is set.
3. Iterate until adoption is exact:
   ```sh
   tofu plan   # goal: "N to import, 0 to add, 0 to change, 0 to destroy"
   ```
   Fix `terraform.tfvars` until nothing but imports remains, then `tofu apply` and commit the state.

Keep the `adopt` IDs after adoption. With them, a lost state is rebuilt by a single `tofu apply`.

## Everyday use

```sh
set -a; source ../.env; set +a
tofu init                          # once per checkout
tofu plan -out=change.tfplan       # review
tofu apply change.tfplan
git add terraform.tfstate && git commit -m "infra: <what changed>"
```

CI runs `tofu fmt -check`, `tofu validate` and `tofu plan -detailed-exitcode` on
every PR and push. A non-empty plan means the live zone drifted from the code,
or a change is waiting to be applied. CI never applies.

## State

State and plan files are encrypted client-side with OpenTofu's
[state encryption](https://opentofu.org/docs/language/state/encryption/)
(PBKDF2 → AES-GCM, `enforced = true`, so plaintext is never written). That makes
the state safe to commit: no remote backend, no R2 bucket, no cost. Without the
passphrase the file is useless.

Trade-off: two people applying at once would conflict in git. That's fine for a
single maintainer; switch to a locking backend if more people apply.

### Rotating the passphrase

1. In `versions.tf`, add the old key as a fallback:
   ```hcl
   key_provider "pbkdf2" "old" { passphrase = var.old_state_passphrase }
   method "aes_gcm" "old"      { keys = key_provider.pbkdf2.old }
   state {
     method   = method.aes_gcm.main
     enforced = true
     fallback { method = method.aes_gcm.old }
   }
   ```
   Declare `variable "old_state_passphrase" { sensitive = true }`.
2. Run with both `TF_VAR_old_state_passphrase` (current) and `TF_VAR_state_passphrase` (new), then `tofu apply` (an apply with no changes still rewrites the state with the new key).
3. Remove the fallback, commit, and update the `TF_VAR_state_passphrase` secret in GitHub.

## WAF custom rules

`waf_custom_rules` in `terraform.tfvars` is the zone's single custom-rules ruleset, evaluated top to bottom.

| # | Rule | Action | Why |
|---|---|---|---|
| 1 | Block SEO and foreign-search crawlers (Ahrefs, Semrush, MJ12, Yandex, Baidu, Sogou) | Block | Unwanted crawl load. Must come before rule 2, because several of these are verified bots |
| 2 | Allow verified bots, feeds and link previews | Skip: remaining custom rules (`ruleset = "current"`), rate limiting, managed rules, Browser Integrity Check | Verified bots, `/feed.xml`, `/rss.xml`, `/robots.txt`, sitemaps, `/favicon.png`, `/_astro/*` and link-preview fetchers (`facebookexternalhit`, `Mastodon/`) can't solve a challenge; these are public static files, so a spoofed user agent gains nothing |
| 3 | Block hosting networks | Block | Pure hosting/datacenter and proxy-seller ASNs where no one browses from. Before rules 4–5 because a challenge ends evaluation |
| 4 | Challenge automation user agents | Managed Challenge | Case-insensitive (`lower()`) match on bot/crawl/spider/scrap/`python-`/`go-http-client`/headless, or an empty user agent |
| 5 | Challenge cloud, VPN and Tor networks | Managed Challenge | Hyperscale clouds, VPN-exit hosts and Tor (`ip.src.country eq "T1"`, which also covers Cloudflare's onion-routed Tor traffic), where real people browse. Humans pass once and keep a `cf_clearance` cookie |

### ASN classification

Every ASN was checked against RIPEstat (holder, announced prefixes), PeeringDB and ipinfo (network type). Rule: **block** pure hosting/datacenter and proxy sellers; **challenge** hyperscale clouds, VPN-exit hosts and corporate egress; **leave out** ISPs, transit carriers and networks announcing no prefixes.

| Decision | ASNs |
|---|---|
| Block (rule 3) | 6724 Strato · 7393 Cybercon · 8560 IONOS · 11878 tzulo · 12876 Scaleway · 14061 DigitalOcean · 16125 Cherry Servers · 16276 OVH · 18450 WebNX · 19437, 20454 Secured Servers · 20473 Vultr · 20738 Heart Internet · 23033 Wowrack · 23470 ReliableSite · 24940, 213230 Hetzner · 25264 Afagh Andish Dadeh Pardis · 26347 DreamHost · 26496, 398101 GoDaddy · 27176 DataWagon · 30083 velia.net · 32244 Liquid Web · 32475 SingleHop · 36352 ColoCrossing · 36943 1-grid · 39020 Comvive · 46606 Unified Layer · 50673 Serverius · 51167 Contabo · 51540 DALNET · 53667 FranTech/BuyVM · 55293 A2 Hosting · 61317 Hivelocity · 63018 Dedicated.com · 63023 GTHost · 63949 Akamai/Linode · 197540 netcup · 198571 PlainProxies · 199610 Nitrado · 200373 3xK Tech · 201924 ENAHOST · 206575 DataBox · 208046 MALIEVA · 210558 1337 Services · 210920, 212047 Civo · 211252 Marushin · 264649 NUT HOST · 397630 Rayobyte · 398493 System In Place |
| Challenge (rule 5) | 2639 Zoho · 3214 xTom · 7203, 27411, 30633, 60781, 205544, 395954 Leaseweb · 7224, 14618, 16509 Amazon · 8075 Microsoft · 9009 M247 · 13238 Yandex · 31898 Oracle · 37963, 45102 Alibaba · 46562 Performive · 60068, 212238 Datacamp/CDN77 · 62240 Clouvider · 131199 Nexeon · 132203 Tencent · 136907 Huawei · 206074, 206092, 206150, 206164 F.N.S. Holdings · 207990 HostRoyale · 396507 Emerald Onion (Tor exits) · 396982 Google Cloud; plus Tor (`T1`) |
| Left out | 6939 Hurricane Electric (transit; IPv6 tunnel users) · 8100 Splice Internet (ISP) · 14178 Megacable (ISP) · 35540 OVH Telecom (ISP) · 21501, 31815, 57523 (not announced) · 15169 Google (Googlebot, PageSpeed Insights) |

Judgment calls: DigitalOcean, Vultr, Linode, Hetzner, OVH, Contabo, netcup and Scaleway also host some people's personal VPNs, who are blocked; move those ASNs to rule 5 to challenge them instead. Tor is challenged rather than blocked, so Tor users can still read the site.

Things to know:
- A skip rule only skips later **custom** rules if it sets `ruleset = "current"` (`skip_remaining_custom_rules = true`); `phases`/`products` only affect other features.
- `contains` is case-sensitive; wrap fields in `lower()` (available on Free). Regex (`matches`) is not available on Free.
- Challenges fail for non-browser clients (feed readers, image fetches, curl), which is why rule 2 exists. Point unverified uptime monitors at `/robots.txt` or `/feed.xml`.
- Bot Fight Mode can't be skipped by custom rules, so it is kept **off** (`bot_fight_mode = false`); it would challenge feed readers hosted on cloud providers.
- After changing rules, check **Security → Events** for false positives.
- ASNs change owners. Re-check them periodically (e.g. `https://stat.ripe.net/app/launchpad/AS<number>`).

Sources: [Custom rules](https://developers.cloudflare.com/waf/custom-rules/), [Skip options](https://developers.cloudflare.com/waf/custom-rules/skip/options/), [Phase order](https://developers.cloudflare.com/waf/feature-interoperability/), [Operators](https://developers.cloudflare.com/ruleset-engine/rules-language/operators/), [Functions](https://developers.cloudflare.com/ruleset-engine/rules-language/functions/), [`cf.client.bot`](https://developers.cloudflare.com/ruleset-engine/rules-language/fields/reference/cf.client.bot/), [Bot Fight Mode](https://developers.cloudflare.com/bots/get-started/bot-fight-mode/), [Challenge pages](https://developers.cloudflare.com/cloudflare-challenges/challenge-types/challenge-pages/).

## Free-tier limits that apply here

| Feature | Free plan | Used |
|---|---|---|
| Single Redirect rules | 10 per zone | 1 |
| WAF custom rules | 5 per zone | 5 |
| DNS records | 1,000 per zone (varies by zone age) | ~10 |
| Web Analytics | Free, unlimited sites | 1 |
| Workers static asset requests | Free, unlimited | all site traffic |
| Worker script invocations | 100,000/day | 0 (assets only) |
| Static assets per version | 20,000 files, 25 MiB each | ~200 files |

## Reference

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
| ---- | ------- |
| terraform | >= 1.12 |
| cloudflare | ~> 5.26 |

## Providers

| Name | Version |
| ---- | ------- |
| cloudflare | ~> 5.26 |

## Modules

No modules.

## Resources

| Name | Type |
| ---- | ---- |
| [cloudflare_bot_management.this](https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/bot_management) | resource |
| [cloudflare_dns_record.this](https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/dns_record) | resource |
| [cloudflare_dns_record.www](https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/dns_record) | resource |
| [cloudflare_ruleset.redirects](https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/ruleset) | resource |
| [cloudflare_ruleset.waf_custom](https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/ruleset) | resource |
| [cloudflare_web_analytics_site.this](https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/web_analytics_site) | resource |
| [cloudflare_zone.this](https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/zone) | resource |
| [cloudflare_zone_setting.this](https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/zone_setting) | resource |

## Inputs

| Name | Description | Type | Default | Required |
| ---- | ----------- | ---- | ------- | :------: |
| account\_id | Cloudflare account ID. Set via TF\_VAR\_account\_id (it is an identifier, not a secret). | `string` | n/a | yes |
| state\_passphrase | Passphrase that encrypts state and plan files (min. 16 characters). Set via TF\_VAR\_state\_passphrase; keep it in a password manager. | `string` | n/a | yes |
| zone\_name | Apex domain of the site, e.g. example.com. CI sets it from the SITE\_DOMAIN repository variable via TF\_VAR\_zone\_name. | `string` | n/a | yes |
| adopt | IDs of existing resources to import instead of creating. Leave empty ({}) for a fresh<br/>setup. When `zone_id` is set, every entry in `zone_settings` is imported too.<br/>Get the IDs with cf-terraforming or `cf` (see infra/README.md). | <pre>object({<br/>    zone_id               = optional(string)<br/>    dns_records           = optional(map(string), {}) # dns_records key => record ID<br/>    www_record_id         = optional(string)<br/>    redirect_ruleset_id   = optional(string)<br/>    web_analytics_site_id = optional(string)<br/>    waf_custom_ruleset_id = optional(string)<br/>  })</pre> | `{}` | no |
| bot\_fight\_mode | Bot Fight Mode (Security → Settings). It cannot be skipped by WAF custom rules, so leave it<br/>off when custom rules exempt feeds and verified bots. Other bot settings are left as-is. | `bool` | `false` | no |
| bot\_settings | Other bot settings to pin; null leaves a setting unmanaged. Values:<br/>ai\_bots\_protection "block" \| "disabled" \| "only\_on\_ad\_pages" (Block AI bots);<br/>crawler\_protection "enabled" \| "disabled" (AI Labyrinth);<br/>ai\_training: robots.txt policy for AI training crawlers (e.g. "disallow");<br/>enable\_js: invisible JavaScript detections. | <pre>object({<br/>    ai_bots_protection = optional(string)<br/>    crawler_protection = optional(string)<br/>    ai_training        = optional(string)<br/>    enable_js          = optional(bool)<br/>  })</pre> | `{}` | no |
| dns\_records | DNS records to manage, keyed by a stable label of your choice. `name` is relative<br/>to the zone ("@" for the apex). Do not list the apex record for the site itself:<br/>the Worker custom domain (owned by Wrangler, `npm run deploy`) creates it. | <pre>map(object({<br/>    type     = string<br/>    name     = string<br/>    content  = string<br/>    ttl      = optional(number, 1) # 1 = automatic<br/>    proxied  = optional(bool, false)<br/>    priority = optional(number)<br/>    comment  = optional(string)<br/>  }))</pre> | `{}` | no |
| redirect\_www\_to\_apex | Create a proxied placeholder `www` record and a zone redirect rule sending www.<zone> to the apex with a 301, keeping path and query string. | `bool` | `true` | no |
| waf\_custom\_rules | WAF custom rules, evaluated in list order. Free plan: at most 5 rules.<br/>`skip_remaining_custom_rules` (ruleset "current"), `skip_phases`, `skip_products` and<br/>`logging` apply only when `action = "skip"`. | <pre>list(object({<br/>    description                 = string<br/>    expression                  = string<br/>    action                      = string<br/>    enabled                     = optional(bool, true)<br/>    logging                     = optional(bool, true)<br/>    skip_remaining_custom_rules = optional(bool, false)<br/>    skip_phases                 = optional(list(string))<br/>    skip_products               = optional(list(string))<br/>  }))</pre> | `[]` | no |
| web\_analytics | Enable Cloudflare Web Analytics with automatic beacon injection for the zone. | `bool` | `true` | no |
| web\_analytics\_exclude\_eu | Web Analytics "lite" mode: don't collect data from EU visitors. | `bool` | `false` | no |
| zone\_settings | Zone settings to pin, as { setting\_id = value }, e.g. { ssl = "strict", min\_tls\_version = "1.2" }.<br/>List only settings that differ from Cloudflare's defaults. Setting IDs:<br/>https://developers.cloudflare.com/api/resources/zones/subresources/settings/ | `any` | `{}` | no |

## Outputs

| Name | Description |
| ---- | ----------- |
| name\_servers | Cloudflare nameservers to set at your registrar. |
| web\_analytics\_site\_tag | Web Analytics site tag, or null when disabled. |
| zone\_id | Zone ID. Export as CLOUDFLARE\_ZONE\_ID for `cf` commands. |
<!-- END_TF_DOCS -->
