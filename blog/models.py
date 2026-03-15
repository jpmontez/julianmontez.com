from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_POSTS_PER_PAGE = 10
DEFAULT_RESPONSIVE_WIDTHS = (480, 720, 1080)
DEFAULT_IMAGE_SIZES = "(max-width: 720px) 100vw, 520px"
DEFAULT_FEED_MAX_POSTS = 25


@dataclass
class ImageMeta:
    path: str
    width: int | None
    height: int | None
    srcset: list[tuple[str, int]] = field(default_factory=list)
    webp_srcset: list[tuple[str, int]] = field(default_factory=list)
    avif_srcset: list[tuple[str, int]] = field(default_factory=list)
    primary_src: str | None = None
    alt: str | None = None

    @property
    def aspect_ratio(self) -> float | None:
        if self.width and self.height:
            return self.width / self.height
        return None


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


@dataclass(frozen=True)
class BuildPaths:
    root: Path
    posts_dir: Path
    static_dir: Path
    dist_dir: Path
    templates_dir: Path
    config_path: Path
    theme_path: Path
    robots_path: Path
    favicon_path: Path

    @classmethod
    def from_root(cls, root: Path) -> "BuildPaths":
        return cls(
            root=root,
            posts_dir=root / "posts",
            static_dir=root / "static",
            dist_dir=root / "dist",
            templates_dir=root / "templates",
            config_path=root / "config.toml",
            theme_path=root / "theme.css",
            robots_path=root / "robots.txt",
            favicon_path=root / "favicon.png",
        )


@dataclass(frozen=True)
class SiteConfig:
    title: str = "Microblog"
    tagline: str = ""
    description: str = ""
    author: str = ""
    base_url: str = ""
    site_url: str = ""
    eager_images: int = 2
    feed_max_posts: int = DEFAULT_FEED_MAX_POSTS
    feed_self_url: str = ""
    posts_per_page: int = DEFAULT_POSTS_PER_PAGE
    responsive_widths: tuple[int, ...] = DEFAULT_RESPONSIVE_WIDTHS
    image_sizes: str = DEFAULT_IMAGE_SIZES
    inline_style: str = ""
    emit_style_file: bool = False
    favicon_hash: str = ""

    def with_runtime(self, *, inline_style: str, favicon_hash: str = "") -> "SiteConfig":
        return SiteConfig(
            title=self.title,
            tagline=self.tagline,
            description=self.description,
            author=self.author,
            base_url=self.base_url,
            site_url=self.site_url,
            eager_images=self.eager_images,
            feed_max_posts=self.feed_max_posts,
            feed_self_url=self.feed_self_url,
            posts_per_page=self.posts_per_page,
            responsive_widths=self.responsive_widths,
            image_sizes=self.image_sizes,
            inline_style=inline_style,
            emit_style_file=self.emit_style_file,
            favicon_hash=favicon_hash,
        )


@dataclass(frozen=True)
class Pagination:
    current_page: int
    total_pages: int
    prev_url: str | None
    next_url: str | None


@dataclass(frozen=True)
class PreloadImage:
    src: str
    srcset: list[tuple[str, int]]
    avif_srcset: list[tuple[str, int]] = field(default_factory=list)


@dataclass(frozen=True)
class PageRenderContext:
    template_name: str
    output_path: Path
    page_title: str
    page_path: str
    page_description: str
    og_type: str
    og_image_path: str | None
    preload_image: PreloadImage | None = None
    payload: dict[str, Any] = field(default_factory=dict)
