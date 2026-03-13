# Python Refactoring Design

**Date:** 2026-03-13
**Scope:** All 7 refactoring improvements identified in code quality review
**Commit strategy:** Single commit, all changes together
**Execution order:** Bottom-up (dependencies first — models → images → config → feeds → render)

---

## 1. `models.py` — Make `Post` frozen

**Problem:** `Post` is mutable solely because `attach_image_meta` does `post.images_meta = metas` after construction.

**Change:**
- Add `frozen=True` to `@dataclass(frozen=True)` on `Post`
- `attach_image_meta` uses `dataclasses.replace(post, images_meta=metas)` instead of direct mutation
- `attach_image_meta` return type changes from `dict[str, str]` to `tuple[list[Post], dict[str, str]]`
- `generate.py` caller updates to: `posts, new_manifest = attach_image_meta(posts, ...)`

---

## 2. `images.py` — Consolidate variant caches + unify variant generation

### Cache consolidation

**Problem:** Three parallel dicts (`variants_cache`, `webp_variants_cache`, `avif_variants_cache`) always written and read together.

**Change:** Replace with one dict keyed to a `_VariantSet` NamedTuple:

```python
class _VariantSet(NamedTuple):
    """Holds the three responsive variant lists for a single source image."""
    native: list[tuple[str, int]]  # resized in source format (JPEG/PNG)
    webp: list[tuple[str, int]]    # transcoded to WebP
    avif: list[tuple[str, int]]    # transcoded to AVIF

variants_cache: dict[str, _VariantSet] = {}
```

Access via `vs = variants_cache[image]` then `vs.native`, `vs.webp`, `vs.avif`.

### Unify variant generation

**Problem:** `generate_variants` and `generate_transcoded_variants` share ~70% of their resize loop logic.

**Change:** Extract a private `_generate_variants` that accepts optional `output_format`, `output_extension`, and `save_kwargs`. Omitting them preserves source format (native behavior); providing them transcodes. The two public functions become thin wrappers, or are inlined in `attach_image_meta` (their only caller).

---

## 3. `config.py` — Remove duplicate `_is_absolute_url`

**Problem:** `config.py:18` defines `_is_absolute_url` identically to `urls.is_absolute_url`.

**Change:** Remove `_is_absolute_url` from `config.py`. Import `is_absolute_url` from `blog.urls` and update all internal call sites.

**Follow-up (separate task):** Audit all modules for other duplicated utility functions that could justify a shared `blog/utils.py`.

---

## 4. `feeds.py` — Extract shared helpers

**Problem:** Three duplications between `write_atom_feed` and `write_rss_feed`.

**Changes:**

- **`_trim_posts(posts, max_posts)`** — extracts the feed-trimming logic:
  ```python
  def _trim_posts(posts: list[Post], max_posts: int) -> list[Post]:
      return posts[:max_posts] if max_posts else []
  ```

- **`_write_xml_file(tree, path)`** — extracts the write + trailing-newline pattern:
  ```python
  def _write_xml_file(tree: ET.ElementTree, path: Path) -> None:
      ET.indent(tree, space="  ")
      tree.write(path, encoding="utf-8", xml_declaration=True)
      path.write_text(path.read_text(encoding="utf-8").rstrip() + "\n", encoding="utf-8")
  ```

- **`loc` nested function** — removed from both feed functions; call sites use `url_ctx.page(...)` directly.

---

## 5. `render.py` — Extract `_og_image` helper + split `build_site`

### `_og_image` helper

**Problem:** `(post.images_meta[0].primary_src or post.images_meta[0].path) if post.images_meta else None` appears twice in `build_site`.

**Change:**
```python
def _og_image(post: Post) -> str | None:
    return (post.images_meta[0].primary_src or post.images_meta[0].path) if post.images_meta else None
```

### Split `build_site`

**Problem:** `build_site` is 105 lines with two independent loops (index pagination + per-post rendering).

**Change:** `build_site` becomes an orchestrator:
```python
def build_site(posts, *, site, env, url_ctx, dist_dir) -> None:
    now = dt.datetime.now(dt.timezone.utc)
    eager_images_count = site.eager_images
    total_pages = max(1, math.ceil(len(posts) / site.posts_per_page))
    _build_index_pages(posts, *, site, env, url_ctx, dist_dir, now, eager_images_count, total_pages)
    _build_post_pages(posts, *, site, env, url_ctx, dist_dir, now, eager_images_count)
```

`_build_index_pages` contains the pagination loop; `_build_post_pages` contains the per-post loop.

---

## Success Criteria

- All existing tests pass (`uv run python -m unittest discover -s tests`)
- No behavior changes — output HTML, feeds, sitemap, and robots.txt are identical before and after
- `uv run ruff format && uv run ruff check` passes clean
