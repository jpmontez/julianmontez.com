from __future__ import annotations

import datetime as dt
import math
import os
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from blog.images import image_src, select_above_fold_metas, select_lcp_meta
from blog.models import PageRenderContext, Pagination, Post, PreloadImage, SiteConfig
from blog.urls import UrlContext, is_absolute_url


def make_env(templates_dir: Path) -> Environment:
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(enabled_extensions=("html", "xml")),
    )
    env.trim_blocks = True
    env.lstrip_blocks = True
    return env


def compute_assets_prefix(output_file: Path, base_url: str, dist_dir: Path) -> str:
    if base_url:
        return base_url.rstrip("/")
    if output_file.parent == dist_dir:
        rel = Path(".")
    else:
        rel = Path(os.path.relpath(dist_dir, output_file.parent))
    rel_posix = rel.as_posix()
    return "." if rel_posix == "." else rel_posix


def normalize_meta_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def render_page(
    env: Environment,
    page_ctx: PageRenderContext,
    *,
    site: SiteConfig,
    now: dt.datetime,
    url_ctx: UrlContext,
    dist_dir: Path,
) -> None:
    page_ctx.output_path.parent.mkdir(parents=True, exist_ok=True)
    assets_prefix = compute_assets_prefix(page_ctx.output_path, site.base_url, dist_dir)
    page_description = normalize_meta_text(page_ctx.page_description or site.description)
    canonical_url = url_ctx.page(page_ctx.page_path)
    page_url = canonical_url

    if page_ctx.og_image_path and is_absolute_url(page_ctx.og_image_path):
        og_image_url = page_ctx.og_image_path
    else:
        og_image_url = url_ctx.page(page_ctx.og_image_path) if page_ctx.og_image_path else None

    template = env.get_template(page_ctx.template_name)
    render_context = dict(page_ctx.payload)
    render_context.update(
        page_title=page_ctx.page_title,
        page_path=page_ctx.page_path,
        page_description=page_description,
        og_type=page_ctx.og_type,
        og_image_url=og_image_url,
        site=site,
        now=now,
        inline_style=site.inline_style,
        assets_prefix=assets_prefix,
        canonical_url=canonical_url,
        page_url=page_url,
        twitter_card="summary_large_image" if og_image_url else "summary",
        twitter_title=page_ctx.page_title,
        twitter_description=page_description,
        twitter_image_url=og_image_url,
        preload_image=page_ctx.preload_image,
    )
    html = template.render(**render_context)
    page_ctx.output_path.write_text(html, encoding="utf-8")


def _page_output_path(dist_dir: Path, page_number: int) -> Path:
    if page_number == 1:
        return dist_dir / "index.html"
    return dist_dir / "page" / str(page_number) / "index.html"


def _rel_link(from_output: Path, to_output: Path) -> str:
    target = to_output.parent if to_output.name == "index.html" else to_output
    rel = os.path.relpath(target, from_output.parent)
    rel_posix = Path(rel).as_posix()
    if not rel_posix or rel_posix == ".":
        return "./" if to_output.name == "index.html" else rel_posix
    return f"{rel_posix.rstrip('/')}/" if to_output.name == "index.html" else rel_posix


def _infer_post_description(post: Post, site: SiteConfig) -> str:
    if post.excerpt:
        return post.excerpt
    if post.title:
        return post.title
    if post.body_html:
        text = re.sub(r"<[^>]+>", " ", post.body_html)
        text = normalize_meta_text(text)
        if text:
            return text[:160].rstrip()
    return site.description


def _post_page_title(post: Post, site: SiteConfig) -> str:
    if post.title:
        title = post.title
    elif post.excerpt:
        title = normalize_meta_text(post.excerpt)[:60].rstrip() or post.display_date
    else:
        title = post.display_date
    return f"{title} — {site.title}"


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
                og_image_path=(
                    (page_posts[0].images_meta[0].primary_src or page_posts[0].images_meta[0].path)
                    if page_posts and page_posts[0].images_meta
                    else None
                ),
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
                og_image_path=(
                    (post.images_meta[0].primary_src or post.images_meta[0].path)
                    if post.images_meta
                    else None
                ),
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
