# julianmontez.com

Static photoblog built with [Astro](https://astro.build). Deployed to Cloudflare Workers static assets with Wrangler; the rest of the Cloudflare setup (zone, DNS, settings, redirects, WAF, bot settings, analytics) is code in [`infra/`](infra/README.md). Everything runs on Cloudflare's free plan.

## Requirements

- **Node.js 24 LTS.** Pinned once in `package.json` (`engines.node`), and `.npmrc` sets `engine-strict=true`, so `npm install` fails on any other major. CI reads the same pin. On macOS: `brew install node@24` and put `/opt/homebrew/opt/node@24/bin` first on your `PATH`.
- **No global npm packages.** Build and deploy tools are pinned devDependencies run through npm scripts or `npx`. `cf` (inspection only) isn't installed; `npx cf …` fetches it on demand.
- **Infrastructure tools** (only to change the Cloudflare setup): `brew install opentofu terraform-docs` and, to adopt an existing zone, `brew install cloudflare/cloudflare/cf-terraforming`.

## Quick Start

```bash
npm install
npx astro dev        # dev server at http://localhost:4321
npx astro build      # build to dist/
npx astro check      # type-check
```

## Repository Layout

```
src/
  assets/photos/       # full-resolution source images
  content/posts/       # Markdown posts (YAML front matter)
  components/
    Feed.astro         # feed page body shared by index and page/[page]
    PostImage.astro    # responsive <picture> with AVIF/WebP srcset
    Slideshow.astro    # multi-image horizontal slideshow
  layouts/
    BaseLayout.astro   # base HTML layout
  pages/
    404.astro          # not-found page (served with a 404 status)
    index.astro        # paginated feed (page 1)
    page/[page].astro  # paginated feed (pages 2+)
    [...slug].astro    # post detail pages
    feed.xml.ts        # RSS feed
    rss.xml.ts         # same feed at a legacy URL
  styles/
    theme.css          # global stylesheet
  config.ts            # site config
  utils.ts             # post and image helpers
scripts/
  import_lightroom.py  # import Lightroom JPG exports
infra/                 # OpenTofu config for the Cloudflare zone (see infra/README.md)
wrangler.jsonc         # assets-only Worker config (name and domain come from env at deploy)
astro.config.mjs       # Astro config
.env.example           # local environment variables template
```

## Writing Posts

Create a Markdown file in `src/content/posts/`, for example `2024-10-12-my-post.md`:

```markdown
---
date: 2024-10-12
images:
  - src: ../../assets/photos/2024-10-12-photo.jpg
    alt: "Describe the photo."
---

Optional markdown body.
```

Place the source image in `src/assets/photos/`. Astro generates responsive variants (520/640/760/1040px in AVIF, WebP, and JPEG) at build time.

## Lightroom Import

```bash
uv run scripts/import_lightroom.py [--source DIR] [--overwrite]
```

Imports files matching `YYYYMMDD-DSC_NNNN.jpg` (default source: `~/Desktop`), copies them to `src/assets/photos/`, and scaffolds post files in `src/content/posts/` with alt text written by headless Claude Code (`claude -p`), billed to your Claude Code login rather than the API. `uv` provides Python 3.14+ from the script's inline metadata; the script has no other dependencies. Requires the `claude` CLI on your PATH, logged in. If alt text generation fails, the post is still written and a warning names the image to caption by hand.

## Deployment

How it fits together:

- **Site:** `npm run deploy` runs `wrangler deploy --name "$WORKER_NAME" --domain "$SITE_DOMAIN"`, uploading the static `dist/` to an assets-only Worker (no script, so no invocations to count) and attaching the custom domain. `wrangler.jsonc` sets trailing-slash handling and serves `404.html` for unknown URLs. `cf` (run on demand with `npx cf …`) is for inspection and admin; it will take over deploys once [cloudflare/cf#18](https://github.com/cloudflare/cf/issues/18) (Astro projects can't `cf deploy`) is fixed.
- **Everything else on the zone:** DNS, zone settings, the www→apex redirect, WAF custom rules, Bot Fight Mode and Web Analytics are OpenTofu in [`infra/`](infra/README.md). `tofu apply` is run locally; CI only checks for drift.

Each resource has one owner: Wrangler owns the Worker, its assets, its custom domain and the DNS record that domain creates; OpenTofu owns the rest.

### Deploy from your machine

```bash
cp .env.example .env         # fill in the values
set -a; source .env; set +a
npm run build && npm run deploy
npx cf auth whoami           # any other cf command, fetched on demand
```

### Deploy your own

1. **Fork** this repo and replace the content: posts in `src/content/posts/`, photos in `src/assets/photos/`, and site identity in `src/config.ts` and `site` in `astro.config.mjs`.
2. **Create credentials** — Cloudflare tokens, then GitHub secrets/variables — following [Credentials setup](#credentials-setup) steps 1–2.
3. **Create your local `.env`** ([Credentials setup](#credentials-setup) step 3).
4. **Describe your zone:** copy `infra/terraform.tfvars.example` to `infra/terraform.tfvars`, list your DNS records, and delete the committed `infra/terraform.tfstate` (it belongs to this site).
5. **Create the Cloudflare setup** from your machine: `cd infra && tofu init && tofu apply`. Commit `terraform.tfvars` and the new encrypted `terraform.tfstate`. If the zone already exists, follow [Adopting an existing zone](infra/README.md#adopting-an-existing-zone) instead.
6. **Push to `main`.** CI builds and deploys, and the Worker takes over your apex domain.

### CI/CD

GitHub Actions (`.github/workflows/deploy.yml`):

| Job | Runs on | Does |
|---|---|---|
| `validate` | PRs | `npm ci`, `astro check`, `astro build` |
| `infra` | PRs and pushes | `tofu fmt -check`, `tofu validate`, terraform-docs sync check, `tofu plan -detailed-exitcode` (fails on drift; skipped when the read token isn't set, e.g. on a fresh fork). Never applies |
| `deploy` | pushes to `main` | `npm ci`, `npm run build` (includes `astro check`), `npm run deploy` (`wrangler deploy`). Independent of `infra`, so zone drift never blocks a new post |

### Credentials setup

Do these in order. Nothing secret is committed anywhere: tokens live in Cloudflare, GitHub secrets and your gitignored `.env`, and OpenTofu encrypts its own state.

#### Step 1 — Create the Cloudflare API tokens

Go to **dash.cloudflare.com → My Profile (top right) → API Tokens → Create Token → Custom token → Get started**. Each permission row in the form has three dropdowns; the tables below list them left to right, exactly as labelled. Names come from Cloudflare's [API token permissions](https://developers.cloudflare.com/fundamentals/api/reference/permissions/) reference; required scopes were checked against the API reference and the Wrangler source.

For every token, set **Account Resources** to `Include` · *your account* and **Zone Resources** to `Include` · `Specific zone` · *your domain*. Never pick "All accounts" or "All zones".

**Token `<site>-tf-read`** (e.g. `julianmontez-com-tf-read`). Read-only; used by CI drift checks, adoption and `npx cf` inspection.

| Dropdown 1 | Dropdown 2 | Dropdown 3 | Why |
|---|---|---|---|
| Account | Account Settings | Read | Read the Web Analytics site |
| Zone | Zone | Read | Read the zone |
| Zone | DNS | Read | Read DNS records |
| Zone | Zone Settings | Read | Read zone settings |
| Zone | Single Redirect | Read | Read the www→apex redirect rule |
| Zone | Zone WAF | Read | Read the WAF custom rules |
| Zone | Bot Management | Read | Read Bot Fight Mode |

**Token `<site>-deploy`** (e.g. `julianmontez-com-deploy`). Used by `npm run deploy` (Wrangler) in CI and locally.

| Dropdown 1 | Dropdown 2 | Dropdown 3 | Why |
|---|---|---|---|
| Account | Workers Scripts | Edit | Upload the Worker and its assets; attach the custom domain |
| Zone | Zone | Read | Wrangler looks up the zone for the custom domain before deploying |
| Zone | Workers Routes | Read | Wrangler checks no other Worker already claims that hostname |

**Token `<site>-tf-apply`** (e.g. `julianmontez-com-tf-apply`). Used for every local `tofu apply`; created once and kept. Never stored in GitHub; keep it in your password manager and `.env` only. Optionally restrict it under **Client IP Address Filtering** to your home IP.

| Dropdown 1 | Dropdown 2 | Dropdown 3 | Why |
|---|---|---|---|
| Zone | DNS | Edit | Create/update/delete managed DNS records |
| Zone | Zone Settings | Edit | Change zone settings |
| Zone | Single Redirect | Edit | Create/update redirect rules |
| Zone | Zone WAF | Edit | Create/update WAF custom rules |
| Zone | Bot Management | Edit | Change Bot Fight Mode and AI bot settings |
| Zone | Zone | Read | Read the zone. Edit would also allow deleting the zone; it's only needed to create a brand-new zone |
| Account | Account Settings | Read | Read the Web Analytics site. Edit is account-wide (account resources and membership); raise it temporarily only to change Web Analytics options |

On **Continue to summary → Create Token**, Cloudflare shows the token once. Copy it straight into GitHub (step 2) and/or `.env` (step 3).

Your **Account ID** is on any zone's **Overview** page, bottom of the right-hand column (**API → Account ID**).

#### Step 2 — Add GitHub secrets and variables

On GitHub, open the repo → **Settings**.

**2a. Environment** — **Environments → New environment**, name `production`, **Configure environment**. Under **Environment secrets → Add environment secret**:

| Name | Value |
|---|---|
| `CLOUDFLARE_DEPLOY_TOKEN` | The `<site>-deploy` token |

**2b. Repository secrets** — **Secrets and variables → Actions → Secrets** tab → **New repository secret**:

| Name | Value | Used by job |
|---|---|---|
| `CLOUDFLARE_TF_READ_TOKEN` | The `<site>-tf-read` token | `infra` |
| `CLOUDFLARE_ACCOUNT_ID` | Your Account ID | `deploy`, `infra` (a job in an environment still reads repository secrets) |
| `TF_VAR_STATE_PASSPHRASE` | A random passphrase of 16+ characters; keep a copy in your password manager | `infra` |

**2c. Repository variables** — same page, **Variables** tab → **New repository variable**:

| Name | Value | Used by job |
|---|---|---|
| `SITE_DOMAIN` | Apex domain, e.g. `example.com` | `deploy`, `infra` |
| `WORKER_NAME` | Lowercase letters, digits, dashes, e.g. `example-com` | `deploy` |

#### Step 3 — Create `.env` for local work

`cp .env.example .env` (gitignored) and fill it in; the file documents each line. Load it with `set -a; source .env; set +a`. `CLOUDFLARE_API_TOKEN` (what every tool reads) defaults to the read-only token; name the write token per command:

```bash
CLOUDFLARE_API_TOKEN=$CLOUDFLARE_DEPLOY_TOKEN npm run deploy
CLOUDFLARE_API_TOKEN=$CLOUDFLARE_TF_APPLY_TOKEN tofu -chdir=infra apply
```
