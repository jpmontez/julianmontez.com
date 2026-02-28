from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Iterable

from PIL import Image

from blog.models import ImageMeta, Post

logger = logging.getLogger(__name__)


def image_dimensions(image_path: Path) -> tuple[int | None, int | None]:
    if not image_path.exists():
        return None, None

    try:
        with Image.open(image_path) as img:
            width, height = img.size
            return int(width), int(height)
    except Exception:
        return None, None


def generate_variants(
    source_path: Path,
    dist_path: Path,
    *,
    widths: tuple[int, ...],
    original: tuple[int | None, int | None],
    dist_root: Path,
) -> list[tuple[str, int]]:
    src_width, src_height = original
    if not src_width or not src_height:
        return []

    suffix = source_path.suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        return []

    dist_dir = dist_path.parent
    dist_dir.mkdir(parents=True, exist_ok=True)

    variants: list[tuple[str, int]] = []
    with Image.open(source_path) as source_image:
        fmt = (source_image.format or "").upper()
        save_kwargs = {}
        if fmt in {"JPG", "JPEG"}:
            save_kwargs = {"quality": 85, "optimize": True, "progressive": True}
        elif fmt == "PNG":
            save_kwargs = {"optimize": True}

        for target_width in widths:
            if target_width >= src_width:
                continue

            target_height = max(1, round(src_height * (target_width / src_width)))
            target_path = dist_dir / f"{source_path.stem}-{target_width}w{source_path.suffix}"
            if not target_path.exists():
                resized = source_image.resize((target_width, target_height), Image.LANCZOS)
                resized.save(target_path, **save_kwargs)

            variants.append((target_path.relative_to(dist_root).as_posix(), target_width))

    variants.append((dist_path.relative_to(dist_root).as_posix(), src_width))
    return variants


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
    src_width, src_height = original
    if not src_width or not src_height:
        return []

    suffix = source_path.suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        return []

    targets = sorted({target for target in widths if target < src_width} | {src_width})
    if not targets:
        return []

    dist_dir = dist_path.parent
    dist_dir.mkdir(parents=True, exist_ok=True)

    variants: list[tuple[str, int]] = []
    try:
        with Image.open(source_path) as source_image:
            for target_width in targets:
                target_path = dist_dir / f"{source_path.stem}-{target_width}w{output_extension}"
                if not target_path.exists():
                    if target_width == src_width:
                        output_image = source_image
                    else:
                        target_height = max(1, round(src_height * (target_width / src_width)))
                        output_image = source_image.resize((target_width, target_height), Image.LANCZOS)
                    output_image.save(target_path, format=output_format, **save_kwargs)
                variants.append((target_path.relative_to(dist_root).as_posix(), target_width))
    except Exception as exc:
        logger.warning(
            "Failed to transcode %s to %s: %s", source_path.name, output_format, exc
        )
        return []

    return variants


def choose_primary_src(
    srcset: list[tuple[str, int]],
    fallback: str,
    target_width: int = 1040,
) -> str:
    if not srcset:
        return fallback
    sorted_srcset = sorted(srcset, key=lambda item: item[1])
    for candidate_path, candidate_width in sorted_srcset:
        if candidate_width >= target_width:
            return candidate_path
    return sorted_srcset[-1][0]


def attach_image_meta(
    posts: list[Post],
    *,
    root: Path,
    dist_dir: Path,
    responsive_widths: tuple[int, ...],
    image_manifest: dict[str, str] | None = None,
) -> dict[str, str]:
    cache: dict[str, tuple[int | None, int | None]] = {}
    variants_cache: dict[str, list[tuple[str, int]]] = {}
    webp_variants_cache: dict[str, list[tuple[str, int]]] = {}
    avif_variants_cache: dict[str, list[tuple[str, int]]] = {}
    manifest = dict(image_manifest or {})
    updated_manifest: dict[str, str] = {}

    for post in posts:
        metas: list[ImageMeta] = []
        for idx, image in enumerate(post.images):
            candidate = Path(image)
            image_path = candidate if candidate.is_absolute() else root / candidate
            alt = post.image_alts[idx] if idx < len(post.image_alts) else None

            if image not in cache:
                cache[image] = image_dimensions(image_path)
                current_hash = ""
                if image_path.exists() and not candidate.is_absolute():
                    current_hash = hashlib.md5(image_path.read_bytes()).hexdigest()  # noqa: S324
                    if current_hash != manifest.get(image, ""):
                        # Source changed — remove old variants so they get regenerated.
                        dist_path_dir = (dist_dir / candidate).parent
                        if dist_path_dir.exists():
                            stem = image_path.stem
                            for old in dist_path_dir.glob(f"{stem}-*"):
                                old.unlink(missing_ok=True)
                updated_manifest[image] = current_hash
                if candidate.is_absolute():
                    variants_cache[image] = []
                    webp_variants_cache[image] = []
                    avif_variants_cache[image] = []
                else:
                    dist_path = dist_dir / candidate
                    variants_cache[image] = generate_variants(
                        source_path=image_path,
                        dist_path=dist_path,
                        widths=responsive_widths,
                        original=cache[image],
                        dist_root=dist_dir,
                    )
                    webp_variants_cache[image] = generate_transcoded_variants(
                        source_path=image_path,
                        dist_path=dist_path,
                        widths=responsive_widths,
                        original=cache[image],
                        dist_root=dist_dir,
                        output_format="WEBP",
                        output_extension=".webp",
                        save_kwargs={"quality": 80, "method": 6},
                    )
                    avif_variants_cache[image] = generate_transcoded_variants(
                        source_path=image_path,
                        dist_path=dist_path,
                        widths=responsive_widths,
                        original=cache[image],
                        dist_root=dist_dir,
                        output_format="AVIF",
                        output_extension=".avif",
                        save_kwargs={"quality": 55},
                    )

            width, height = cache[image]
            variants = variants_cache.get(image, [])
            webp_variants = webp_variants_cache.get(image, [])
            avif_variants = avif_variants_cache.get(image, [])
            primary_src = choose_primary_src(
                srcset=variants,
                fallback=image if candidate.is_absolute() else candidate.as_posix(),
            )
            metas.append(
                ImageMeta(
                    path=image,
                    width=width,
                    height=height,
                    srcset=variants,
                    webp_srcset=webp_variants,
                    avif_srcset=avif_variants,
                    primary_src=primary_src,
                    alt=alt,
                )
            )

        post.images_meta = metas

    return updated_manifest


def image_src(meta: ImageMeta) -> str:
    return meta.primary_src or meta.path


def image_lcp_score(meta: ImageMeta) -> float:
    if meta.width and meta.height and meta.width > 0:
        return meta.height / meta.width
    return 0.0


def select_lcp_meta(candidates: list[ImageMeta]) -> ImageMeta | None:
    if not candidates:
        return None
    # If candidates are equally sized in the viewport, the later element can
    # become the LCP candidate, so break ties by picking the last one.
    return max(enumerate(candidates), key=lambda item: (image_lcp_score(item[1]), item[0]))[1]


def select_above_fold_metas(metas: Iterable[ImageMeta], count: int) -> list[ImageMeta]:
    selected: list[ImageMeta] = []
    if count <= 0:
        return selected
    for meta in metas:
        selected.append(meta)
        if len(selected) >= count:
            break
    return selected
