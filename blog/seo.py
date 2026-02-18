from __future__ import annotations

import math
from pathlib import Path
from xml.etree import ElementTree as ET

from blog.models import Post, SiteConfig
from blog.urls import UrlContext, is_absolute_url


def write_sitemap(
    posts: list[Post],
    *,
    site: SiteConfig,
    url_ctx: UrlContext,
    dist_dir: Path,
) -> None:
    def loc(path: str) -> str:
        return url_ctx.page(path)

    def asset_url(path: str) -> str | None:
        return url_ctx.asset(path)

    total_pages = max(1, math.ceil(len(posts) / site.posts_per_page))
    newest_post = posts[0] if posts else None
    lastmod_feed = newest_post.date.isoformat() if newest_post else None

    sitemap_ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
    image_ns = "http://www.google.com/schemas/sitemap-image/1.1"
    ET.register_namespace("", sitemap_ns)
    ET.register_namespace("image", image_ns)
    urlset = ET.Element(f"{{{sitemap_ns}}}urlset")

    def add_url(path: str, lastmod: str | None = None, images: list[str] | None = None) -> None:
        url_el = ET.SubElement(urlset, f"{{{sitemap_ns}}}url")
        loc_el = ET.SubElement(url_el, f"{{{sitemap_ns}}}loc")
        loc_el.text = loc(path)
        if lastmod:
            lastmod_el = ET.SubElement(url_el, f"{{{sitemap_ns}}}lastmod")
            lastmod_el.text = lastmod
        for image_loc in images or []:
            image_el = ET.SubElement(url_el, f"{{{image_ns}}}image")
            image_loc_el = ET.SubElement(image_el, f"{{{image_ns}}}loc")
            image_loc_el.text = image_loc

    add_url("", lastmod=lastmod_feed)
    for page_num in range(2, total_pages + 1):
        add_url(f"page/{page_num}/", lastmod=lastmod_feed)

    for post in posts:
        images: list[str] = []
        for meta in post.images_meta:
            image_loc = asset_url(meta.path)
            if image_loc:
                images.append(image_loc)
        add_url(post.url, lastmod=post.date.isoformat(), images=images or None)

    sitemap_path = dist_dir / "sitemap.xml"
    tree = ET.ElementTree(urlset)
    ET.indent(tree, space="  ")
    tree.write(sitemap_path, encoding="utf-8", xml_declaration=True)
    sitemap_path.write_text(
        sitemap_path.read_text(encoding="utf-8").rstrip() + "\n", encoding="utf-8"
    )


def rewrite_dist_robots(*, site: SiteConfig, url_ctx: UrlContext, dist_dir: Path) -> None:
    robots_path = dist_dir / "robots.txt"
    if not robots_path.exists():
        return

    raw_lines = robots_path.read_text(encoding="utf-8").splitlines()
    existing_sitemaps: list[str] = []
    lines: list[str] = []
    for line in raw_lines:
        stripped = line.strip()
        if stripped.lower().startswith("sitemap:"):
            existing_sitemaps.append(stripped.split(":", 1)[1].strip())
        else:
            lines.append(line)

    if url_ctx.absolute_base:
        sitemap_url = url_ctx.page("sitemap.xml")
    else:
        sitemap_url = next((url for url in existing_sitemaps if is_absolute_url(url)), "")

    if sitemap_url:
        lines.append("")
        lines.append(f"Sitemap: {sitemap_url}")
    robots_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
