# Pipeline Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update `.github/workflows/deploy.yml` to eliminate redundant builds, remove vestigial schedule triggers, and adopt current action/runtime versions.

**Architecture:** All changes are confined to a single workflow file. The `validate` job builds once and uploads `dist/` as an artifact; the `deploy` job downloads that artifact and deploys without rebuilding. No other files are modified.

**Tech Stack:** GitHub Actions, Astro, Cloudflare Pages (`cloudflare/wrangler-action@v3`)

---

### Task 1: Update triggers and concurrency

**Files:**
- Modify: `.github/workflows/deploy.yml`

- [ ] **Step 1: Remove the `schedule` block**

Open `.github/workflows/deploy.yml`. Replace the `on:` block:

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:
```

The two `schedule` entries (`0 6 * * *` and `0 18 * * *`) are removed entirely.

- [ ] **Step 2: Set `cancel-in-progress: true`**

Replace the `concurrency:` block:

```yaml
concurrency:
  group: "pages"
  cancel-in-progress: true
```

- [ ] **Step 3: Validate YAML syntax**

Run:
```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/deploy.yml'))" && echo "YAML OK"
```

Expected: `YAML OK` with no errors.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/deploy.yml
git commit -m "ci: remove schedule triggers and enable cancel-in-progress"
```

---

### Task 2: Update the `validate` job

**Files:**
- Modify: `.github/workflows/deploy.yml`

- [ ] **Step 1: Update `setup-node` version and Node version**

Find the `Setup Node.js` step inside the `validate` job and replace it:

```yaml
      - name: Setup Node.js
        uses: actions/setup-node@v6
        with:
          node-version: 24
          cache: npm
```

- [ ] **Step 2: Replace the two build steps with `npm run build`**

Remove these two steps from the `validate` job:

```yaml
      - name: Check types
        run: npx astro check

      - name: Build site
        run: npx astro build
```

Replace them with a single step:

```yaml
      - name: Build site
        run: npm run build
```

(`npm run build` in `package.json` already chains `astro check && astro build`.)

- [ ] **Step 3: Add artifact upload step**

Append this step at the end of the `validate` job (after `Build site`):

```yaml
      - name: Upload artifact
        uses: actions/upload-artifact@v6
        with:
          name: dist
          path: dist/
          retention-days: 1
```

- [ ] **Step 4: Validate YAML syntax**

Run:
```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/deploy.yml'))" && echo "YAML OK"
```

Expected: `YAML OK` with no errors.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/deploy.yml
git commit -m "ci: consolidate validate job — setup-node@v6, node 24, npm run build, upload artifact"
```

---

### Task 3: Restructure the `deploy` job

**Files:**
- Modify: `.github/workflows/deploy.yml`

- [ ] **Step 1: Strip the `deploy` job down to two steps**

Replace the entire `deploy` job with:

```yaml
  deploy:
    needs: validate
    if: github.event_name != 'pull_request'
    runs-on: ubuntu-latest
    environment: cloudflare-pages
    steps:
      - name: Download artifact
        uses: actions/download-artifact@v8
        with:
          name: dist
          path: dist/

      - name: Deploy to Cloudflare Pages
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          command: pages deploy dist --project-name=${{ secrets.CLOUDFLARE_PROJECT_NAME }}
```

The `Checkout`, `Setup Node.js`, `Install dependencies`, and `Build site` steps are removed — `dist/` arrives via the artifact download.

- [ ] **Step 2: Verify the full file matches the expected final state**

The complete `.github/workflows/deploy.yml` should now read:

```yaml
name: Build and Deploy Blog

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  deployments: write

concurrency:
  group: "pages"
  cancel-in-progress: true

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v6

      - name: Setup Node.js
        uses: actions/setup-node@v6
        with:
          node-version: 24
          cache: npm

      - name: Install dependencies
        run: npm ci

      - name: Build site
        run: npm run build

      - name: Upload artifact
        uses: actions/upload-artifact@v6
        with:
          name: dist
          path: dist/
          retention-days: 1

  deploy:
    needs: validate
    if: github.event_name != 'pull_request'
    runs-on: ubuntu-latest
    environment: cloudflare-pages
    steps:
      - name: Download artifact
        uses: actions/download-artifact@v8
        with:
          name: dist
          path: dist/

      - name: Deploy to Cloudflare Pages
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          command: pages deploy dist --project-name=${{ secrets.CLOUDFLARE_PROJECT_NAME }}
```

- [ ] **Step 3: Validate YAML syntax**

Run:
```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/deploy.yml'))" && echo "YAML OK"
```

Expected: `YAML OK` with no errors.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/deploy.yml
git commit -m "ci: strip deploy job to artifact download + wrangler deploy"
```

- [ ] **Step 5: Push and verify the workflow runs successfully**

Push to `main` and confirm in the GitHub Actions UI that:
- The `validate` job completes and the `dist` artifact appears under the run's artifacts
- The `deploy` job downloads the artifact and deploys successfully without running a build
