from __future__ import annotations

import datetime as dt
import email.utils
import html
from pathlib import Path
from xml.etree import ElementTree as ET

from blog.images import image_src
from blog.models import Post, SiteConfig
from blog.render import normalize_meta_text
from blog.urls import UrlContext


def _trim_posts(posts: list[Post], max_posts: int) -> list[Post]:
    return posts[:max_posts] if max_posts else []


def _write_xml_file(tree: ET.ElementTree, path: Path) -> None:
    ET.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=True)
    path.write_text(path.read_text(encoding="utf-8").rstrip() + "\n", encoding="utf-8")


def format_rfc3339(value: dt.date | dt.datetime) -> str:
    if isinstance(value, dt.date) and not isinstance(value, dt.datetime):
        value = dt.datetime(value.year, value.month, value.day, tzinfo=dt.timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=dt.timezone.utc)
    return value.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def format_rfc822(value: dt.date | dt.datetime) -> str:
    if isinstance(value, dt.date) and not isinstance(value, dt.datetime):
        value = dt.datetime(value.year, value.month, value.day, tzinfo=dt.timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=dt.timezone.utc)
    return email.utils.format_datetime(value.astimezone(dt.timezone.utc), usegmt=True)


def feed_post_title(post: Post) -> str:
    return str(post.title or post.display_date or post.slug or "Post")


def render_feed_post_html(post: Post, url_ctx: UrlContext) -> str:
    parts: list[str] = []
    for meta in post.images_meta:
        src = url_ctx.asset(image_src(meta))
        if not src:
            continue
        alt = meta.alt if meta.alt is not None else (post.title or "Photo")
        alt = html.escape(str(alt), quote=True)
        src = html.escape(str(src), quote=True)
        width_attr = f' width="{meta.width}"' if meta.width else ""
        height_attr = f' height="{meta.height}"' if meta.height else ""
        parts.append(f'<p><img src="{src}" alt="{alt}"{width_attr}{height_attr} /></p>')

    if post.excerpt:
        parts.append(f"<p>{html.escape(str(post.excerpt))}</p>")
    if post.body_html:
        parts.append(post.body_html)
    return "\n".join(parts).strip()


def write_atom_feed(
    posts: list[Post], *, site: SiteConfig, url_ctx: UrlContext, dist_dir: Path
) -> None:
    feed_posts = _trim_posts(posts, site.feed_max_posts)

    atom_ns = "http://www.w3.org/2005/Atom"
    ET.register_namespace("", atom_ns)
    feed_el = ET.Element(f"{{{atom_ns}}}feed")

    ET.SubElement(feed_el, f"{{{atom_ns}}}title").text = site.title
    ET.SubElement(feed_el, f"{{{atom_ns}}}id").text = url_ctx.page("")
    ET.SubElement(feed_el, f"{{{atom_ns}}}link", {"href": url_ctx.page("")})
    ET.SubElement(
        feed_el,
        f"{{{atom_ns}}}link",
        {"href": url_ctx.feed_self("feed.xml"), "rel": "self", "type": "application/atom+xml"},
    )

    newest = feed_posts[0].date if feed_posts else dt.datetime.now(dt.timezone.utc)
    ET.SubElement(feed_el, f"{{{atom_ns}}}updated").text = format_rfc3339(newest)

    author = site.author.strip()
    if author:
        author_el = ET.SubElement(feed_el, f"{{{atom_ns}}}author")
        ET.SubElement(author_el, f"{{{atom_ns}}}name").text = author

    for post in feed_posts:
        entry_el = ET.SubElement(feed_el, f"{{{atom_ns}}}entry")
        post_url = url_ctx.page(post.url)

        ET.SubElement(entry_el, f"{{{atom_ns}}}title").text = feed_post_title(post)
        ET.SubElement(entry_el, f"{{{atom_ns}}}id").text = post_url
        ET.SubElement(entry_el, f"{{{atom_ns}}}link", {"href": post_url})
        ET.SubElement(entry_el, f"{{{atom_ns}}}updated").text = format_rfc3339(post.date)
        ET.SubElement(entry_el, f"{{{atom_ns}}}published").text = format_rfc3339(post.date)

        summary = normalize_meta_text(str(post.excerpt or post.title or ""))
        if summary:
            summary_el = ET.SubElement(entry_el, f"{{{atom_ns}}}summary", {"type": "html"})
            summary_el.text = summary

        content_html = render_feed_post_html(post, url_ctx)
        if content_html:
            content_el = ET.SubElement(entry_el, f"{{{atom_ns}}}content", {"type": "html"})
            content_el.text = content_html

    _write_xml_file(ET.ElementTree(feed_el), dist_dir / "feed.xml")


def write_rss_feed(
    posts: list[Post], *, site: SiteConfig, url_ctx: UrlContext, dist_dir: Path
) -> None:
    feed_posts = _trim_posts(posts, site.feed_max_posts)

    atom_ns = "http://www.w3.org/2005/Atom"
    ET.register_namespace("atom", atom_ns)

    rss_root = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(rss_root, "channel")

    ET.SubElement(channel, "title").text = site.title
    ET.SubElement(channel, "link").text = url_ctx.page("")
    ET.SubElement(
        channel,
        f"{{{atom_ns}}}link",
        {"href": url_ctx.feed_self("rss.xml"), "rel": "self", "type": "application/rss+xml"},
    )
    ET.SubElement(channel, "description").text = site.description
    ET.SubElement(channel, "lastBuildDate").text = format_rfc822(
        feed_posts[0].date if feed_posts else dt.datetime.now(dt.timezone.utc)
    )

    for post in feed_posts:
        item = ET.SubElement(channel, "item")
        post_url = url_ctx.page(post.url)
        ET.SubElement(item, "title").text = feed_post_title(post)
        ET.SubElement(item, "link").text = post_url
        guid = ET.SubElement(item, "guid", {"isPermaLink": "true"})
        guid.text = post_url
        ET.SubElement(item, "pubDate").text = format_rfc822(post.date)

        description = render_feed_post_html(post, url_ctx)
        if not description:
            description = normalize_meta_text(str(post.excerpt or post.title or "")) or post_url
        ET.SubElement(item, "description").text = description

    _write_xml_file(ET.ElementTree(rss_root), dist_dir / "rss.xml")


def write_feeds(
    posts: list[Post], *, site: SiteConfig, url_ctx: UrlContext, dist_dir: Path
) -> None:
    write_atom_feed(posts, site=site, url_ctx=url_ctx, dist_dir=dist_dir)
    write_rss_feed(posts, site=site, url_ctx=url_ctx, dist_dir=dist_dir)
