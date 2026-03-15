from __future__ import annotations

import dataclasses
import hashlib
import logging
from pathlib import Path
from typing import Iterable, NamedTuple

from PIL import Image

from blog.models import ImageMeta, Post

logger = logging.getLogger(__name__)


class _VariantSet(NamedTuple):
    """Holds the three responsive variant lists for a single source image.
    Each list contains (relative_path, width) tuples for use in srcset attributes."""

    native: list[tuple[str, int]]  # resized in source format (JPEG/PNG/WebP)
    webp: list[tuple[str, int]]  # transcoded to WebP
    avif: list[tuple[str, int]]  # transcoded to AVIF


def image_dimensions(image_path: Path) -> tuple[int | None, int | None]:
    if not image_path.exists():
        return None, None

    try:
        with Image.open(image_path) as img:
            width, height = img.size
            return int(width), int(height)
    except Exception:
        return None, None


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
                        output_image = source_image.copy()
                    else:
                        target_height = max(1, round(src_height * (target_width / src_width)))
                        output_image = source_image.resize(
                            (target_width, target_height), Image.LANCZOS
                        )
                    if transcoding:
                        output_image.save(target_path, format=output_format, **(save_kwargs or {}))
                    else:
                        output_image.save(target_path, **(save_kwargs or {}))
                variants.append((target_path.relative_to(dist_root).as_posix(), target_width))

    except Exception as exc:
        if transcoding:
            logger.warning("Failed to transcode %s to %s: %s", source_path.name, output_format, exc)
            return []
        raise

    if not transcoding:
        variants.append((dist_path.relative_to(dist_root).as_posix(), src_width))

    return variants


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
) -> tuple[list[Post], dict[str, str]]:
    cache: dict[str, tuple[int | None, int | None]] = {}
    variants_cache: dict[str, _VariantSet] = {}
    manifest = dict(image_manifest or {})
    updated_manifest: dict[str, str] = {}
    updated_posts: list[Post] = []

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
                    variants_cache[image] = _VariantSet(native=[], webp=[], avif=[])
                else:
                    dist_path = dist_dir / candidate
                    variants_cache[image] = _VariantSet(
                        native=generate_variants(
                            source_path=image_path,
                            dist_path=dist_path,
                            widths=responsive_widths,
                            original=cache[image],
                            dist_root=dist_dir,
                        ),
                        webp=generate_transcoded_variants(
                            source_path=image_path,
                            dist_path=dist_path,
                            widths=responsive_widths,
                            original=cache[image],
                            dist_root=dist_dir,
                            output_format="WEBP",
                            output_extension=".webp",
                            save_kwargs={"quality": 80, "method": 6},
                        ),
                        avif=generate_transcoded_variants(
                            source_path=image_path,
                            dist_path=dist_path,
                            widths=responsive_widths,
                            original=cache[image],
                            dist_root=dist_dir,
                            output_format="AVIF",
                            output_extension=".avif",
                            save_kwargs={"quality": 40},
                        ),
                    )

            width, height = cache[image]
            vs = variants_cache.get(
                image, _VariantSet(native=[], webp=[], avif=[])
            )  # absolute URL images skip variant generation
            variants = vs.native
            webp_variants = vs.webp
            avif_variants = vs.avif
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

        updated_posts.append(dataclasses.replace(post, images_meta=metas))

    return updated_posts, updated_manifest


def image_src(meta: ImageMeta) -> str:
    return meta.primary_src or meta.path


def select_lcp_meta(candidates: list[ImageMeta]) -> ImageMeta | None:
    if not candidates:
        return None
    # The first image in DOM order is the actual LCP element — it's the first
    # visible content the browser paints. Portrait-ratio ranking was a bad
    # heuristic that mis-predicted the LCP for multi-image slideshows.
    return candidates[0]


def select_above_fold_metas(metas: Iterable[ImageMeta], count: int) -> list[ImageMeta]:
    selected: list[ImageMeta] = []
    if count <= 0:
        return selected
    for meta in metas:
        selected.append(meta)
        if len(selected) >= count:
            break
    return selected
