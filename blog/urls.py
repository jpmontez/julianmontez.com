from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

from blog.models import SiteConfig


def is_absolute_url(value: str) -> bool:
    value = value.strip()
    return value.startswith(("http://", "https://"))


def public_base_url(site: SiteConfig) -> str | None:
    base_url = site.base_url.strip().rstrip("/")
    site_url = site.site_url.strip().rstrip("/")

    if is_absolute_url(base_url):
        return base_url

    if not site_url:
        return None

    if base_url and not base_url.startswith("/"):
        base_url = "/" + base_url
    return f"{site_url}{base_url}"


def public_path_prefix(site: SiteConfig) -> str:
    base_url = site.base_url.strip().rstrip("/")
    if not base_url:
        return ""
    if is_absolute_url(base_url):
        return ""
    return base_url if base_url.startswith("/") else f"/{base_url}"


def join_relative_url(prefix: str, path: str) -> str:
    prefix = prefix.rstrip("/")
    path = path.lstrip("/")
    if not path:
        return f"{prefix}/" if prefix else "/"
    if not prefix or prefix == ".":
        return f"{prefix}/{path}" if prefix else f"/{path}"
    return f"{prefix}/{path}"


def join_absolute_url(base: str, path: str) -> str:
    return urljoin(base.rstrip("/") + "/", path.lstrip("/"))


@dataclass(frozen=True)
class UrlContext:
    absolute_base: str | None
    prefix: str
    feed_self_override: str | None

    @classmethod
    def from_site(cls, site: SiteConfig) -> "UrlContext":
        return cls(
            absolute_base=public_base_url(site),
            prefix=public_path_prefix(site),
            feed_self_override=site.feed_self_url.strip() or None,
        )

    def page(self, path: str) -> str:
        if self.absolute_base:
            return join_absolute_url(self.absolute_base, path)
        return join_relative_url(self.prefix, path)

    def asset(self, path: str) -> str | None:
        if not path:
            return None
        if is_absolute_url(path):
            return path
        candidate = Path(path)
        if candidate.is_absolute():
            return None
        return self.page(candidate.as_posix())

    def feed_self(self, path: str) -> str:
        if self.feed_self_override:
            if is_absolute_url(self.feed_self_override):
                return join_absolute_url(self.feed_self_override, path)
            return join_relative_url(self.feed_self_override, path)
        return self.page(path)
