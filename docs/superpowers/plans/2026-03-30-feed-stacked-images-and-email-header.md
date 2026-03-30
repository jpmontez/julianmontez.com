# Feed Stacked Images & Email Header Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace multi-image slideshows on all feed pages with vertically stacked images, and add a mailto email link to the site header.

**Architecture:** Both feed pages (`index.astro` and `page/[page].astro`) inline-loop `<PostImage>` inside a new `.image-stack` wrapper div instead of rendering `<Slideshow>`. The email link is added to `siteConfig` and rendered in `BaseLayout.astro` alongside the existing tagline. All styling lives in `theme.css`.

**Tech Stack:** Astro 5, TypeScript, CSS (no framework)

---

## File Map

| File | Change |
|------|--------|
| `src/config.ts` | Add `email` field |
| `src/layouts/BaseLayout.astro` | Add email link to tagline span |
| `src/styles/theme.css` | Add `.image-stack` rules + tagline link styles |
| `src/pages/index.astro` | Replace `<Slideshow>` with `.image-stack` loop; remove Slideshow import |
| `src/pages/page/[page].astro` | Replace `<Slideshow>` with `.image-stack` loop; remove Slideshow import |

`src/components/Slideshow.astro` is **not touched** — it stays in use on `[...slug].astro`.

---

## Verification command

After each task, run:

```bash
npx astro check
```

Expected: `Found 0 errors.` (warnings are acceptable)

---

## Task 1: Add email to siteConfig and BaseLayout

**Files:**
- Modify: `src/config.ts`
- Modify: `src/layouts/BaseLayout.astro`

- [ ] **Step 1: Add `email` to `siteConfig` in `src/config.ts`**

Replace:
```ts
export const siteConfig = {
  title: 'Julian Montez',
  tagline: 'Brooklyn, NY',
  description: 'A topographical photoblog by Julian Montez',
```
With:
```ts
export const siteConfig = {
  title: 'Julian Montez',
  tagline: 'Brooklyn, NY',
  email: 'contact@julianmontez.com',
  description: 'A topographical photoblog by Julian Montez',
```

- [ ] **Step 2: Update tagline in `src/layouts/BaseLayout.astro`**

Replace:
```astro
        <span class="tagline">{siteConfig.tagline}</span>
```
With:
```astro
        <span class="tagline">
          {siteConfig.tagline}
          <span aria-hidden="true"> | </span>
          <a href={`mailto:${siteConfig.email}`}>Email</a>
        </span>
```

- [ ] **Step 3: Run type check**

```bash
npx astro check
```

Expected: `Found 0 errors.`

- [ ] **Step 4: Commit**

```bash
git add src/config.ts src/layouts/BaseLayout.astro
git commit -m "feat(header): add email contact link to tagline"
```

---

## Task 2: Add CSS for tagline link and image stack

**Files:**
- Modify: `src/styles/theme.css`

- [ ] **Step 1: Add tagline link styles after `header.site .tagline` block**

In `theme.css`, locate:
```css
header.site .tagline {
  text-transform: initial;
  color: var(--muted);
}
```

Insert immediately after:
```css
header.site .tagline a {
  text-decoration: none;
}

header.site .tagline a:hover {
  text-decoration: underline;
}
```

- [ ] **Step 2: Add `.image-stack` rules after `header.site .tagline a:hover` block**

Insert immediately after the block added in Step 1:
```css
.image-stack {
  max-width: 520px;
  margin: 0 auto 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.image-stack figure {
  margin: 0;
}
```

**Why `margin: 0` on `.image-stack figure`:** `.post figure` has `margin: 0 auto 18px`. Inside the flex stack, gap handles spacing between images; the stack wrapper itself carries the `18px` bottom margin. Without this override, each figure would add an extra `18px` below itself, doubling the gap.

- [ ] **Step 3: Run type check**

```bash
npx astro check
```

Expected: `Found 0 errors.`

- [ ] **Step 4: Commit**

```bash
git add src/styles/theme.css
git commit -m "feat(styles): add image-stack and tagline email link styles"
```

---

## Task 3: Replace Slideshow with stacked images in `index.astro`

**Files:**
- Modify: `src/pages/index.astro`

- [ ] **Step 1: Remove the `Slideshow` import**

Remove this line from the frontmatter imports:
```astro
import Slideshow from '../components/Slideshow.astro';
```

- [ ] **Step 2: Replace the Slideshow branch with an image-stack loop**

Locate this block (inside the `rendered.map(...)` return):
```astro
        {post.data.images.length > 1 ? (
          <Slideshow
            images={post.data.images}
            linkHref={postUrl}
            eagerCount={isEager ? 1 : 0}
            lcpIndex={isLcp ? 0 : -1}
          />
        ) : post.data.images.length === 1 ? (
          <PostImage
            image={post.data.images[0].src}
            alt={post.data.images[0].alt}
            linkHref={postUrl}
            isEager={isEager}
            isLcp={isLcp}
          />
        ) : null}
```

Replace with:
```astro
        {post.data.images.length > 1 ? (
          <div class="image-stack">
            {post.data.images.map((img, i) => (
              <PostImage
                image={img.src}
                alt={img.alt}
                linkHref={postUrl}
                isEager={isEager && i === 0}
                isLcp={isLcp && i === 0}
              />
            ))}
          </div>
        ) : post.data.images.length === 1 ? (
          <PostImage
            image={post.data.images[0].src}
            alt={post.data.images[0].alt}
            linkHref={postUrl}
            isEager={isEager}
            isLcp={isLcp}
          />
        ) : null}
```

**Eager/LCP notes:**
- `isEager && i === 0` — only the first image of an eager post loads eagerly; subsequent images in the stack are lazy.
- `isLcp && i === 0` — only the first image of the first post gets `fetchpriority="high"`.

- [ ] **Step 3: Run type check**

```bash
npx astro check
```

Expected: `Found 0 errors.`

- [ ] **Step 4: Commit**

```bash
git add src/pages/index.astro
git commit -m "feat(feed): replace slideshow with stacked images on page 1"
```

---

## Task 4: Replace Slideshow with stacked images in `page/[page].astro`

**Files:**
- Modify: `src/pages/page/[page].astro`

- [ ] **Step 1: Remove the `Slideshow` import**

Remove this line from the frontmatter imports:
```astro
import Slideshow from '../../components/Slideshow.astro';
```

- [ ] **Step 2: Replace the Slideshow branch with an image-stack loop**

Locate this block (inside the `rendered.map(...)` return):
```astro
        {post.data.images.length > 1 ? (
          <Slideshow
            images={post.data.images}
            linkHref={postUrl}
          />
        ) : post.data.images.length === 1 ? (
          <PostImage
            image={post.data.images[0].src}
            alt={post.data.images[0].alt}
            linkHref={postUrl}
          />
        ) : null}
```

Replace with:
```astro
        {post.data.images.length > 1 ? (
          <div class="image-stack">
            {post.data.images.map((img) => (
              <PostImage
                image={img.src}
                alt={img.alt}
                linkHref={postUrl}
              />
            ))}
          </div>
        ) : post.data.images.length === 1 ? (
          <PostImage
            image={post.data.images[0].src}
            alt={post.data.images[0].alt}
            linkHref={postUrl}
          />
        ) : null}
```

**Note:** No eager/LCP props here — paginated pages have no eager-loading logic, matching the existing behavior.

- [ ] **Step 3: Run type check**

```bash
npx astro check
```

Expected: `Found 0 errors.`

- [ ] **Step 4: Commit**

```bash
git add src/pages/page/\[page\].astro
git commit -m "feat(feed): replace slideshow with stacked images on paginated pages"
```

---

## Task 5: Final build verification

- [ ] **Step 1: Run full build**

```bash
npx astro build
```

Expected: Build completes with no errors. Output written to `dist/`.

- [ ] **Step 2: Spot-check locally**

```bash
npx astro dev
```

Open `http://localhost:4321` and verify:
- Multi-image posts on the homepage show images stacked vertically with a small gap
- The header shows `Brooklyn, NY | Email` with the email as a plain link (no underline at rest, underline on hover)
- Navigating to an individual multi-image post still shows the slideshow
- Paginated pages (e.g. `/page/2/`) also show stacked images for multi-image posts
