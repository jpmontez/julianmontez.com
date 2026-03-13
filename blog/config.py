from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from urllib.parse import urlparse

import tomllib

from blog.models import (
    DEFAULT_FEED_MAX_POSTS,
    DEFAULT_IMAGE_SIZES,
    DEFAULT_POSTS_PER_PAGE,
    DEFAULT_RESPONSIVE_WIDTHS,
    SiteConfig,
)
from blog.urls import is_absolute_url


def _ensure_absolute_http_url(field_name: str, value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{field_name} must be an absolute http(s) URL: {value!r}")
    return value.rstrip("/")


def _coerce_non_negative_int(field_name: str, value: object, *, allow_zero: bool = True) -> int:
    try:
        numeric = int(value)  # type: ignore[arg-type]
    except Exception as exc:  # pragma: no cover - guardrail
        raise ValueError(f"{field_name} must be an integer") from exc

    minimum = 0 if allow_zero else 1
    if numeric < minimum:
        comparator = ">= 0" if allow_zero else ">= 1"
        raise ValueError(f"{field_name} must be {comparator}")
    return numeric


def _coerce_responsive_widths(raw: object) -> tuple[int, ...]:
    if raw is None:
        return DEFAULT_RESPONSIVE_WIDTHS
    if not isinstance(raw, list):
        raise ValueError("responsive_widths must be a list of positive integers")

    seen: set[int] = set()
    normalized: list[int] = []
    for item in raw:
        width = _coerce_non_negative_int("responsive_widths item", item, allow_zero=False)
        if width not in seen:
            seen.add(width)
            normalized.append(width)
    if not normalized:
        raise ValueError("responsive_widths must include at least one width")
    return tuple(sorted(normalized))


def validate_site_config(site: SiteConfig) -> SiteConfig:
    site_url = site.site_url.strip()
    base_url = site.base_url.strip()
    feed_self_url = site.feed_self_url.strip()

    if site_url:
        site_url = _ensure_absolute_http_url("site_url", site_url)

    if base_url:
        if is_absolute_url(base_url):
            base_url = _ensure_absolute_http_url("base_url", base_url)
        else:
            if " " in base_url:
                raise ValueError("base_url cannot contain spaces")
            if not base_url.startswith("/"):
                base_url = f"/{base_url}"
            base_url = base_url.rstrip("/")
            if base_url == "/":
                base_url = ""

    if feed_self_url:
        if is_absolute_url(feed_self_url):
            feed_self_url = _ensure_absolute_http_url("feed_self_url", feed_self_url)
        else:
            if " " in feed_self_url:
                raise ValueError("feed_self_url cannot contain spaces")
            if not feed_self_url.startswith("/"):
                feed_self_url = f"/{feed_self_url}"
            feed_self_url = feed_self_url.rstrip("/") or "/"

    eager_images = _coerce_non_negative_int("eager_images", site.eager_images)
    feed_max_posts = _coerce_non_negative_int("feed_max_posts", site.feed_max_posts)
    posts_per_page = _coerce_non_negative_int(
        "posts_per_page", site.posts_per_page, allow_zero=False
    )

    responsive_widths = tuple(sorted(dict.fromkeys(site.responsive_widths)))
    if not responsive_widths or any(width <= 0 for width in responsive_widths):
        raise ValueError("responsive_widths must contain positive integers")

    image_sizes = site.image_sizes.strip() or DEFAULT_IMAGE_SIZES

    return replace(
        site,
        site_url=site_url,
        base_url=base_url,
        feed_self_url=feed_self_url,
        eager_images=eager_images,
        feed_max_posts=feed_max_posts,
        posts_per_page=posts_per_page,
        responsive_widths=responsive_widths,
        image_sizes=image_sizes,
    )


def load_site_config(path: Path) -> SiteConfig:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    config = SiteConfig(
        title=str(raw.get("title", "Microblog") or "Microblog"),
        tagline=str(raw.get("tagline", "") or ""),
        description=str(raw.get("description", "") or ""),
        author=str(raw.get("author", "") or ""),
        base_url=str(raw.get("base_url", "") or ""),
        site_url=str(raw.get("site_url", "") or ""),
        eager_images=int(raw.get("eager_images", 2) or 0),
        feed_max_posts=int(raw.get("feed_max_posts", DEFAULT_FEED_MAX_POSTS) or 0),
        feed_self_url=str(raw.get("feed_self_url", "") or ""),
        posts_per_page=int(
            raw.get("posts_per_page", DEFAULT_POSTS_PER_PAGE) or DEFAULT_POSTS_PER_PAGE
        ),
        responsive_widths=_coerce_responsive_widths(raw.get("responsive_widths")),
        image_sizes=str(raw.get("image_sizes", DEFAULT_IMAGE_SIZES) or DEFAULT_IMAGE_SIZES),
        emit_style_file=bool(raw.get("emit_style_file", False)),
    )
    return validate_site_config(config)


def apply_cli_overrides(
    site: SiteConfig,
    *,
    site_url: str | None = None,
    base_url: str | None = None,
    feed_self_url: str | None = None,
) -> SiteConfig:
    updated = replace(
        site,
        site_url=site.site_url if site_url is None else str(site_url),
        base_url=site.base_url if base_url is None else str(base_url),
        feed_self_url=site.feed_self_url if feed_self_url is None else str(feed_self_url),
    )
    return validate_site_config(updated)
