# Python Refactoring Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Apply 7 code quality improvements to the blog generator — eliminating duplication, consolidating caches, making `Post` immutable, and splitting an oversized function — with no behavior changes.

**Architecture:** Bottom-up order: `models.py` first (makes `Post` frozen), then `images.py` (depends on the new Post API), then `config.py`, `feeds.py`, and `render.py` (independent cleanups). Single commit at the end.

**Tech Stack:** Python 3.12+, dataclasses, typing.NamedTuple, Pillow, Jinja2, unittest

---

## Baseline

Before touching any code, confirm all tests pass:

```bash
uv run python -m unittest discover -s tests
```

Expected: all tests pass with 0 errors.

---

## Task 1: Make `Post` frozen

**Files:**
- Modify: `blog/models.py`
- Modify: `blog/images.py`
- Modify: `blog/generate.py`
- Modify: `tests/test_images.py`

### Step 1: Update `blog/models.py`

Change `@dataclass` to `@dataclass(frozen=True)` on `Post`. No field changes needed — `images_meta: list[ImageMeta] = field(default_factory=list)` still works as the default for newly-parsed posts.

```python
# blog/models.py — change line ~33
@dataclass(frozen=True)
class Post:
    source: Path
    title: str | None
    date: dt.date
    images: list[str]
    image_alts: list[str | None]
    excerpt: str | None
    layout: str
    body_html: str
    display_date: str
    url: str
    slug: str
    location_name: str | None = None
    location_latitude: float | None = None
    location_longitude: float | None = None
    images_meta: list[ImageMeta] = field(default_factory=list)
```

### Step 2: Update `blog/images.py` — `attach_image_meta`

Add `import dataclasses` at the top of `images.py`.

Change `attach_image_meta` to:
1. Accumulate new posts in `updated_posts: list[Post] = []`
2. Replace `post.images_meta = metas` with `updated_posts.append(dataclasses.replace(post, images_meta=metas))`
3. Change the return type annotation from `dict[str, str]` to `tuple[list[Post], dict[str, str]]`
4. Return `(updated_posts, updated_manifest)` at the end

```python
# blog/images.py — full updated signature and return
def attach_image_meta(
    posts: list[Post],
    *,
    root: Path,
    dist_dir: Path,
    responsive_widths: tuple[int, ...],
    image_manifest: dict[str, str] | None = None,
) -> tuple[list[Post], dict[str, str]]:
    ...
    updated_posts: list[Post] = []
    ...
    # Inside the per-post loop, replace:
    #   post.images_meta = metas
    # with:
    #   updated_posts.append(dataclasses.replace(post, images_meta=metas))
    ...
    return updated_posts, updated_manifest
```

### Step 3: Update `blog/generate.py`

Find the call to `attach_image_meta` and unpack the tuple:

```python
# blog/generate.py — before
new_manifest = attach_image_meta(
    posts,
    root=PATHS.root,
    dist_dir=PATHS.dist_dir,
    responsive_widths=site.responsive_widths,
    image_manifest=prev_manifest,
)

# after
posts, new_manifest = attach_image_meta(
    posts,
    root=PATHS.root,
    dist_dir=PATHS.dist_dir,
    responsive_widths=site.responsive_widths,
    image_manifest=prev_manifest,
)
```

### Step 4: Update `tests/test_images.py`

Six tests call `attach_image_meta`. All need to unpack the returned tuple and reference the returned posts (not the original variable, which is now stale after the call).

For tests that only check `post.images_meta` (not the manifest):
```python
# OLD pattern
attach_image_meta([post], root=root, dist_dir=dist_dir, responsive_widths=(...))
meta = post.images_meta[0]

# NEW pattern
posts, _ = attach_image_meta([post], root=root, dist_dir=dist_dir, responsive_widths=(...))
meta = posts[0].images_meta[0]
```

For tests that check both `images_meta` and the returned manifest:
```python
# OLD
new_manifest = attach_image_meta([post], ..., image_manifest=manifest)
post.images_meta  # checked separately

# NEW
posts, new_manifest = attach_image_meta([post], ..., image_manifest=manifest)
posts[0].images_meta  # if needed
```

Apply this pattern to all 6 tests:
- `test_attach_image_meta_generates_responsive_variants`: unpack, use `posts[0].images_meta`
- `test_attach_image_meta_no_images`: unpack, compare `posts[0].images_meta == []`
- `test_all_widths_larger_than_source`: unpack, use `posts[0].images_meta[0]`
- `test_missing_image_file`: unpack, use `posts[0].images_meta[0]`
- `test_manifest_cache_hit_skips_regeneration`: unpack as `posts, new_manifest = ...`
- `test_manifest_cache_miss_regenerates`: unpack as `posts, new_manifest = ...`

### Step 5: Run tests

```bash
uv run python -m unittest discover -s tests
```

Expected: all tests pass.

---

## Task 2: Consolidate variant caches with `_VariantSet`

**Files:**
- Modify: `blog/images.py`

### Step 1: Add `_VariantSet` NamedTuple

Add to `blog/images.py` near the top (after imports, before functions):

```python
from typing import NamedTuple

class _VariantSet(NamedTuple):
    """Holds the three responsive variant lists for a single source image.
    Each list contains (relative_path, width) tuples for use in srcset attributes."""
    native: list[tuple[str, int]]  # resized in source format (JPEG/PNG/WebP)
    webp: list[tuple[str, int]]    # transcoded to WebP
    avif: list[tuple[str, int]]    # transcoded to AVIF
```

### Step 2: Replace the three caches with one

In `attach_image_meta`, replace:
```python
variants_cache: dict[str, list[tuple[str, int]]] = {}
webp_variants_cache: dict[str, list[tuple[str, int]]] = {}
avif_variants_cache: dict[str, list[tuple[str, int]]] = {}
```

With:
```python
variants_cache: dict[str, _VariantSet] = {}
```

### Step 3: Update write sites

Find all three places where variants are computed and written to their respective caches. Replace with a single `_VariantSet` assignment:

```python
# OLD (three separate assignments)
variants_cache[image] = generate_variants(...)
webp_variants_cache[image] = generate_transcoded_variants(..., output_format="WEBP", ...)
avif_variants_cache[image] = generate_transcoded_variants(..., output_format="AVIF", ...)

# NEW (one assignment)
variants_cache[image] = _VariantSet(
    native=generate_variants(...),
    webp=generate_transcoded_variants(..., output_format="WEBP", ...),
    avif=generate_transcoded_variants(..., output_format="AVIF", ...),
)
```

Also update the absolute-path (external URL) case:
```python
# OLD
variants_cache[image] = []
webp_variants_cache[image] = []
avif_variants_cache[image] = []

# NEW
variants_cache[image] = _VariantSet(native=[], webp=[], avif=[])
```

### Step 4: Update read sites

Find the three `.get()` calls and replace with a single lookup:

```python
# OLD
variants = variants_cache.get(image, [])
webp_variants = webp_variants_cache.get(image, [])
avif_variants = avif_variants_cache.get(image, [])

# NEW
vs = variants_cache.get(image, _VariantSet(native=[], webp=[], avif=[]))
variants = vs.native
webp_variants = vs.webp
avif_variants = vs.avif
```

### Step 5: Run tests

```bash
uv run python -m unittest discover -s tests
```

Expected: all tests pass.

---

## Task 3: Unify `generate_variants` and `generate_transcoded_variants`

**Files:**
- Modify: `blog/images.py`

**Key behavioral differences to preserve:**

| Behavior | Native (`generate_variants`) | Transcoded (`generate_transcoded_variants`) |
|---|---|---|
| Full-width entry | Appends original `dist_path` (no resize) | Creates a resized copy at `src_width` in target format |
| `targets` set | `widths < src_width` only | `widths < src_width` **plus** `src_width` |
| Error handling | No try/except (errors propagate) | try/except → logs warning, returns `[]` |
| Save call | `image.save(path, **kwargs)` (Pillow infers format) | `image.save(path, format=output_format, **kwargs)` |
| `save_kwargs` | Computed from source format | Passed in by caller |

### Step 1: Extract `_generate_variants` private function

Add a new private function that handles both cases. Place it above `generate_variants`:

```python
def _generate_variants(
    source_path: Path,
    dist_path: Path,
    *,
    widths: tuple[int, ...],
    original: tuple[int | None, int | None],
    dist_root: Path,
    output_format: str | None = None,
    output_extension: str | None = None,
    save_kwargs: dict[str, int | bool] | None = None,
) -> list[tuple[str, int]]:
    src_width, src_height = original
    if not src_width or not src_height:
        return []

    suffix = source_path.suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        return []

    transcoding = output_format is not None
    effective_ext = output_extension if transcoding else source_path.suffix

    dist_dir = dist_path.parent
    dist_dir.mkdir(parents=True, exist_ok=True)

    # Transcoded variants include src_width itself (full-size in target format).
    # Native variants only include widths smaller than src_width; the original
    # dist_path is appended at the end without re-encoding.
    if transcoding:
        targets = sorted({t for t in widths if t < src_width} | {src_width})
    else:
        targets = [t for t in widths if t < src_width]

    variants: list[tuple[str, int]] = []
    try:
        with Image.open(source_path) as source_image:
            if not transcoding and save_kwargs is None:
                fmt = (source_image.format or "").upper()
                if fmt in {"JPG", "JPEG"}:
                    save_kwargs = {"quality": 85, "optimize": True, "progressive": True}
                elif fmt == "PNG":
                    save_kwargs = {"optimize": True}
                else:
                    save_kwargs = {}

            for target_width in targets:
                target_path = dist_dir / f"{source_path.stem}-{target_width}w{effective_ext}"
                if not target_path.exists():
                    if transcoding and target_width == src_width:
                        output_image = source_image
                    else:
                        target_height = max(1, round(src_height * (target_width / src_width)))
                        output_image = source_image.resize(
                            (target_width, target_height), Image.LANCZOS
                        )
                    if transcoding:
                        output_image.save(
                            target_path, format=output_format, **(save_kwargs or {})
                        )
                    else:
                        output_image.save(target_path, **(save_kwargs or {}))
                variants.append((target_path.relative_to(dist_root).as_posix(), target_width))

    except Exception as exc:
        if transcoding:
            logger.warning(
                "Failed to transcode %s to %s: %s", source_path.name, output_format, exc
            )
            return []
        raise

    if not transcoding:
        variants.append((dist_path.relative_to(dist_root).as_posix(), src_width))

    return variants
```

### Step 2: Replace `generate_variants` body

```python
def generate_variants(
    source_path: Path,
    dist_path: Path,
    *,
    widths: tuple[int, ...],
    original: tuple[int | None, int | None],
    dist_root: Path,
) -> list[tuple[str, int]]:
    return _generate_variants(
        source_path, dist_path, widths=widths, original=original, dist_root=dist_root
    )
```

### Step 3: Replace `generate_transcoded_variants` body

```python
def generate_transcoded_variants(
    source_path: Path,
    dist_path: Path,
    *,
    widths: tuple[int, ...],
    original: tuple[int | None, int | None],
    dist_root: Path,
    output_format: str,
    output_extension: str,
    save_kwargs: dict[str, int | bool],
) -> list[tuple[str, int]]:
    return _generate_variants(
        source_path,
        dist_path,
        widths=widths,
        original=original,
        dist_root=dist_root,
        output_format=output_format,
        output_extension=output_extension,
        save_kwargs=save_kwargs,
    )
```

### Step 4: Run tests

```bash
uv run python -m unittest discover -s tests
```

Expected: all tests pass.

---

## Task 4: Remove duplicate `_is_absolute_url` from `config.py`

**Files:**
- Modify: `blog/config.py`

### Step 1: Add import

In `blog/config.py`, add `is_absolute_url` to the import from `blog.urls`:

```python
from blog.urls import is_absolute_url, UrlContext  # add is_absolute_url
```

Check what is currently imported from `blog.urls` — just add `is_absolute_url` to whatever is already there. If `blog.urls` isn't imported yet, add:

```python
from blog.urls import is_absolute_url
```

### Step 2: Remove `_is_absolute_url`

Delete the private function definition (around line 18–19):

```python
# DELETE THIS:
def _is_absolute_url(value: str) -> bool:
    return value.startswith(("http://", "https://"))
```

### Step 3: Update call sites

Search `config.py` for `_is_absolute_url(` and replace each with `is_absolute_url(`. There should be 1–3 occurrences inside `validate_site_config` and/or `_ensure_absolute_http_url`.

### Step 4: Run tests

```bash
uv run python -m unittest discover -s tests
```

Expected: all tests pass.

---

## Task 5: Extract shared helpers in `feeds.py`

**Files:**
- Modify: `blog/feeds.py`

### Step 1: Add `_trim_posts` near the top of the file (after imports)

```python
def _trim_posts(posts: list[Post], max_posts: int) -> list[Post]:
    return posts[:max_posts] if max_posts else []
```

### Step 2: Add `_write_xml_file` near the top of the file

```python
def _write_xml_file(tree: ET.ElementTree, path: Path) -> None:
    ET.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=True)
    path.write_text(path.read_text(encoding="utf-8").rstrip() + "\n", encoding="utf-8")
```

### Step 3: Update `write_atom_feed`

Replace:
```python
max_posts = site.feed_max_posts
feed_posts = posts[:max_posts] if max_posts else []

def loc(path: str) -> str:
    return url_ctx.page(path)
```
With:
```python
feed_posts = _trim_posts(posts, site.feed_max_posts)
```

Replace all `loc(...)` calls with `url_ctx.page(...)` directly.

At the end, replace the indent+write+newline block with:
```python
_write_xml_file(ET.ElementTree(feed_el), dist_dir / "feed.xml")
```

### Step 4: Update `write_rss_feed`

Same substitutions as Step 3, applied to `write_rss_feed`. Replace the `loc` nested function, the trim logic, and the trailing write block.

Replace the final file-write block with:
```python
_write_xml_file(ET.ElementTree(rss_root), dist_dir / "rss.xml")
```

### Step 5: Run tests

```bash
uv run python -m unittest discover -s tests
```

Expected: all tests pass.

---

## Task 6: Refactor `render.py` — extract helper + split `build_site`

**Files:**
- Modify: `blog/render.py`

### Step 1: Add `_og_image` helper

Add this private function before `build_site`:

```python
def _og_image(post: Post) -> str | None:
    """Return the OG image path for a post, preferring the primary (processed) src."""
    return (
        (post.images_meta[0].primary_src or post.images_meta[0].path)
        if post.images_meta
        else None
    )
```

### Step 2: Add `_build_index_pages`

Extract the index pagination loop from `build_site` into a private function:

```python
def _build_index_pages(
    posts: list[Post],
    *,
    site: SiteConfig,
    env: Environment,
    url_ctx: UrlContext,
    dist_dir: Path,
    now: dt.datetime,
    eager_images_count: int,
    total_pages: int,
) -> None:
    for page_num in range(1, total_pages + 1):
        start = (page_num - 1) * site.posts_per_page
        end = start + site.posts_per_page
        page_posts = posts[start:end]
        output_path = _page_output_path(dist_dir, page_num)

        pagination = Pagination(
            current_page=page_num,
            total_pages=total_pages,
            prev_url=_rel_link(output_path, _page_output_path(dist_dir, page_num - 1))
            if page_num > 1
            else None,
            next_url=_rel_link(output_path, _page_output_path(dist_dir, page_num + 1))
            if page_num < total_pages
            else None,
        )

        feed_images = select_above_fold_metas(
            (meta for post in page_posts for meta in post.images_meta),
            eager_images_count,
        )
        lcp_meta = select_lcp_meta(feed_images)
        preload = (
            PreloadImage(src=image_src(lcp_meta), srcset=lcp_meta.srcset) if lcp_meta else None
        )

        render_page(
            env,
            PageRenderContext(
                template_name="index.html",
                output_path=output_path,
                page_title=site.title if page_num == 1 else f"{site.title} — Page {page_num}",
                page_path="" if page_num == 1 else f"page/{page_num}/",
                page_description=site.description,
                og_type="website",
                og_image_path=_og_image(page_posts[0]) if page_posts else None,
                preload_image=preload,
                payload={
                    "posts": page_posts,
                    "pagination": pagination,
                    "eager_image_ids": [image_src(meta) for meta in feed_images],
                    "lcp_image_id": image_src(lcp_meta) if lcp_meta else None,
                    "image_sizes": site.image_sizes,
                },
            ),
            site=site,
            now=now,
            url_ctx=url_ctx,
            dist_dir=dist_dir,
        )
```

### Step 3: Add `_build_post_pages`

Extract the per-post loop from `build_site`:

```python
def _build_post_pages(
    posts: list[Post],
    *,
    site: SiteConfig,
    env: Environment,
    url_ctx: UrlContext,
    dist_dir: Path,
    now: dt.datetime,
    eager_images_count: int,
) -> None:
    for post in posts:
        out_dir = dist_dir / str(post.date.year) / f"{post.date.month:02d}" / post.slug
        output_file = out_dir / "index.html"
        post_images = select_above_fold_metas(post.images_meta, eager_images_count)
        post_lcp_meta = select_lcp_meta(post_images)
        preload = (
            PreloadImage(src=image_src(post_lcp_meta), srcset=post_lcp_meta.srcset)
            if post_lcp_meta
            else None
        )

        render_page(
            env,
            PageRenderContext(
                template_name="post.html",
                output_path=output_file,
                page_title=_post_page_title(post, site),
                page_path=post.url,
                page_description=_infer_post_description(post, site),
                og_type="article",
                og_image_path=_og_image(post),
                preload_image=preload,
                payload={
                    "post": post,
                    "image_sizes": site.image_sizes,
                    "eager_image_ids": [image_src(meta) for meta in post_images],
                    "lcp_image_id": image_src(post_lcp_meta) if post_lcp_meta else None,
                },
            ),
            site=site,
            now=now,
            url_ctx=url_ctx,
            dist_dir=dist_dir,
        )
```

### Step 4: Simplify `build_site`

Replace the body of `build_site` with:

```python
def build_site(
    posts: list[Post],
    *,
    site: SiteConfig,
    env: Environment,
    url_ctx: UrlContext,
    dist_dir: Path,
) -> None:
    now = dt.datetime.now(dt.timezone.utc)
    eager_images_count = site.eager_images
    total_pages = max(1, math.ceil(len(posts) / site.posts_per_page))
    _build_index_pages(
        posts,
        site=site,
        env=env,
        url_ctx=url_ctx,
        dist_dir=dist_dir,
        now=now,
        eager_images_count=eager_images_count,
        total_pages=total_pages,
    )
    _build_post_pages(
        posts,
        site=site,
        env=env,
        url_ctx=url_ctx,
        dist_dir=dist_dir,
        now=now,
        eager_images_count=eager_images_count,
    )
```

### Step 5: Run tests

```bash
uv run python -m unittest discover -s tests
```

Expected: all tests pass.

---

## Task 7: Lint check + final verification + commit

### Step 1: Format and lint

```bash
uv run ruff format && uv run ruff check
```

Fix any issues reported. Common ones:
- Unused imports (e.g., if `webp_variants_cache` variable name lingers anywhere)
- Line-length violations in new helper functions

### Step 2: Full test run

```bash
uv run python -m unittest discover -s tests
```

Expected: all tests pass.

### Step 3: Build verification

```bash
uv run generate-blog
```

Expected: builds successfully, prints "Built N posts into blog/dist".

### Step 4: Commit

```bash
git add blog/models.py blog/images.py blog/generate.py blog/config.py blog/feeds.py blog/render.py tests/test_images.py
git commit -m "refactor: eliminate duplication, freeze Post, consolidate image caches

- models.py: make Post frozen=True
- images.py: attach_image_meta returns (posts, manifest) instead of mutating;
  consolidate 3 variant caches into _VariantSet NamedTuple;
  extract _generate_variants to unify native and transcoded resize logic
- config.py: remove duplicate _is_absolute_url, import from urls.py
- feeds.py: extract _trim_posts and _write_xml_file helpers, remove duplicate loc functions
- render.py: extract _og_image helper, split build_site into _build_index_pages + _build_post_pages

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Follow-up (separate task, not part of this plan)

Audit all modules for other duplicated utility functions that could warrant a shared `blog/utils.py`. Starting points: date formatting helpers in `feeds.py` (`format_rfc3339`, `format_rfc822`), the `image_src` helper in `images.py` used by both `render.py` and `feeds.py`.
