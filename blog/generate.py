from __future__ import annotations

import argparse
import datetime as dt
import math
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin
from xml.etree import ElementTree as ET

import tomllib

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError as exc:  # pragma: no cover - runtime dependency hint
    raise SystemExit("jinja2 is required. Run `uv sync` before generating.") from exc

try:  # Prefer the markdown package but keep a basic fallback.
    import markdown  # type: ignore
except Exception:  # pragma: no cover - fallback is intentionally simple.
    markdown = None

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover - runtime dependency hint
    raise SystemExit("Pillow is required. Run `uv sync` before generating.") from exc

ROOT = Path(__file__).resolve().parent
POSTS_DIR = ROOT / "posts"
STATIC_DIR = ROOT / "static"
DIST_DIR = ROOT / "dist"
TEMPLATES_DIR = ROOT / "templates"
POSTS_PER_PAGE = 10
RESPONSIVE_WIDTHS = [480, 720, 1080]


@dataclass
class ImageMeta:
    path: str
    width: int | None
    height: int | None
    srcset: list[tuple[str, int]] = field(default_factory=list)
    primary_src: str | None = None
    alt: str | None = None

    @property
    def aspect_ratio(self) -> float | None:
        if self.width and self.height:
            return self.width / self.height
        return None


@dataclass
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
    images_meta: list[ImageMeta] = field(default_factory=list)


def render_markdown(text: str) -> str:
    if markdown is None:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        return "".join(f"<p>{p}</p>" for p in paragraphs)
    return markdown.markdown(text, extensions=["extra"])


def parse_front_matter(raw: str) -> tuple[dict, str]:
    lines = raw.splitlines()
    if not lines:
        raise ValueError("Empty post")

    delimiter = lines[0].strip()
    if delimiter not in ("+++", "++++"):
        raise ValueError("Front matter must start with +++ or ++++")

    try:
        end_idx = next(i for i, line in enumerate(lines[1:], start=1) if line.strip() == delimiter)
    except StopIteration as exc:  # pragma: no cover - guardrail
        raise ValueError(f"Front matter closing {delimiter} not found") from exc

    front = "\n".join(lines[1:end_idx])
    body = "\n".join(lines[end_idx + 1 :]).lstrip()
    data = tomllib.loads(front)
    return data, body


def parse_images(meta: dict, source: Path) -> tuple[list[str], list[str | None]]:
    raw = meta.get("images", [])
    if raw is None:
        return [], []
    if not isinstance(raw, list):
        raise ValueError(f"Invalid images field in {source}: expected a list")

    images: list[str] = []
    image_alts: list[str | None] = []

    for idx, item in enumerate(raw):
        if isinstance(item, str):
            images.append(item)
            image_alts.append(None)
            continue

        if isinstance(item, dict):
            src = item.get("src") or item.get("path")
            if not src:
                raise ValueError(f"Invalid images[{idx}] in {source}: missing src")
            images.append(str(src))

            alt = item.get("alt")
            image_alts.append(None if alt is None else str(alt))
            continue

        raise ValueError(f"Invalid images[{idx}] in {source}: expected string or table")

    return images, image_alts


def parse_post(path: Path) -> Post:
    raw = path.read_text(encoding="utf-8")
    meta, body_md = parse_front_matter(raw)

    try:
        date = dt.date.fromisoformat(str(meta["date"]))
    except Exception as exc:  # pragma: no cover - strict input validation
        raise ValueError(f"Invalid or missing date in {path}") from exc

    title = meta.get("title")
    images, image_alts = parse_images(meta, path)
    excerpt = meta.get("excerpt")
    layout = meta.get("layout", "photo")
    slug = path.stem

    body_html = render_markdown(body_md) if body_md.strip() else ""
    display_date = date.strftime("%d %b %Y")
    url = f"{date.year}/{date.month:02d}/{slug}/"

    return Post(
        source=path,
        title=title,
        date=date,
        images=images,
        image_alts=image_alts,
        excerpt=excerpt,
        layout=layout,
        body_html=body_html,
        display_date=display_date,
        url=url,
        slug=slug,
    )


def collect_posts() -> list[Post]:
    posts: list[Post] = []
    for md in sorted(POSTS_DIR.glob("**/*.md")):
        posts.append(parse_post(md))
    posts.sort(key=lambda p: p.date, reverse=True)
    return posts


def load_config(path: Path) -> dict:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    defaults = {
        "title": "Microblog",
        "tagline": "",
        "description": "",
        "author": "",
        "base_url": "",
        "site_url": "",
    }
    defaults.update(data)
    return defaults


def ensure_empty_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


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
    source_path: Path, dist_path: Path, widths: list[int], original: tuple[int | None, int | None]
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
    for target_width in widths:
        if target_width >= src_width:
            continue

        target_height = max(1, round(src_height * (target_width / src_width)))
        target_path = dist_dir / f"{source_path.stem}-{target_width}w{source_path.suffix}"
        if not target_path.exists():
            with Image.open(source_path) as img:
                resized = img.resize((target_width, target_height), Image.LANCZOS)
                fmt = (img.format or "").upper()
                save_kwargs = {}
                if fmt in {"JPG", "JPEG"}:
                    save_kwargs = {"quality": 85, "optimize": True, "progressive": True}
                elif fmt == "PNG":
                    save_kwargs = {"optimize": True}
                resized.save(target_path, **save_kwargs)

        variants.append((target_path.relative_to(DIST_DIR).as_posix(), target_width))

    variants.append((dist_path.relative_to(DIST_DIR).as_posix(), src_width))
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


def attach_image_meta(posts: list[Post]) -> None:
    cache: dict[str, tuple[int | None, int | None]] = {}
    variants_cache: dict[str, list[tuple[str, int]]] = {}

    for post in posts:
        metas: list[ImageMeta] = []
        for idx, image in enumerate(post.images):
            candidate = Path(image)
            image_path = candidate if candidate.is_absolute() else ROOT / candidate
            alt = post.image_alts[idx] if idx < len(post.image_alts) else None

            if image not in cache:
                cache[image] = image_dimensions(image_path)
                if candidate.is_absolute():
                    variants_cache[image] = []
                else:
                    dist_path = DIST_DIR / candidate
                    variants_cache[image] = generate_variants(
                        source_path=image_path,
                        dist_path=dist_path,
                        widths=RESPONSIVE_WIDTHS,
                        original=cache[image],
                    )

            width, height = cache[image]
            variants = variants_cache.get(image, [])
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
                    primary_src=primary_src,
                    alt=alt,
                )
            )

        post.images_meta = metas


def copy_assets() -> None:
    shutil.copy2(ROOT / "theme.css", DIST_DIR / "style.css")
    if STATIC_DIR.exists():
        shutil.copytree(STATIC_DIR, DIST_DIR / "static", dirs_exist_ok=True)
    favicon = ROOT / "favicon.png"
    if favicon.exists():
        shutil.copy2(favicon, DIST_DIR / "favicon.png")
    robots = ROOT / "robots.txt"
    if robots.exists():
        shutil.copy2(robots, DIST_DIR / "robots.txt")


def make_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(enabled_extensions=("html", "xml")),
    )
    env.trim_blocks = True
    env.lstrip_blocks = True
    return env


def compute_assets_prefix(output_file: Path, base_url: str) -> str:
    if base_url:
        return base_url.rstrip("/")
    if output_file.parent == DIST_DIR:
        rel = Path(".")
    else:
        rel = Path(os.path.relpath(DIST_DIR, output_file.parent))
    rel_posix = rel.as_posix()
    return "." if rel_posix == "." else rel_posix


def is_absolute_url(value: str) -> bool:
    value = value.strip()
    return value.startswith(("http://", "https://"))


def public_base_url(site: dict) -> str | None:
    base_url = str(site.get("base_url", "") or "").strip().rstrip("/")
    site_url = str(site.get("site_url", "") or "").strip().rstrip("/")

    if is_absolute_url(base_url):
        return base_url

    if not site_url:
        return None

    if base_url and not base_url.startswith("/"):
        base_url = "/" + base_url
    return f"{site_url}{base_url}"


def public_path_prefix(site: dict) -> str:
    base_url = str(site.get("base_url", "") or "").strip().rstrip("/")
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


def normalize_meta_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def render_page(env: Environment, template_name: str, output_path: Path, context: dict) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    base_url = context["site"].get("base_url", "")
    assets_prefix = compute_assets_prefix(output_path, base_url)
    page_path = str(context.get("page_path", "") or "")
    page_description = normalize_meta_text(
        str(context.get("page_description") or context["site"].get("description") or "")
    )
    og_type = str(context.get("og_type", "website") or "website")
    og_image_path = str(context.get("og_image_path") or "") or None

    absolute_base = public_base_url(context["site"])
    if absolute_base:
        canonical_url = join_absolute_url(absolute_base, page_path)
        page_url = canonical_url
        if og_image_path and is_absolute_url(og_image_path):
            og_image_url = og_image_path
        else:
            og_image_url = (
                join_absolute_url(absolute_base, og_image_path) if og_image_path else None
            )
    else:
        prefix = public_path_prefix(context["site"])
        canonical_url = join_relative_url(prefix, page_path)
        page_url = canonical_url
        if og_image_path and is_absolute_url(og_image_path):
            og_image_url = og_image_path
        else:
            og_image_url = join_relative_url(prefix, og_image_path) if og_image_path else None

    template = env.get_template(template_name)
    render_context = dict(context)
    render_context.update(
        assets_prefix=assets_prefix,
        canonical_url=canonical_url,
        page_url=page_url,
        page_description=page_description,
        og_type=og_type,
        og_image_url=og_image_url,
        twitter_card="summary_large_image" if og_image_url else "summary",
    )
    html = template.render(**render_context)
    output_path.write_text(html, encoding="utf-8")


def build(posts: Iterable[Post], site: dict, env: Environment) -> None:
    now = dt.datetime.now(dt.timezone.utc)
    posts_list = list(posts)

    def page_output_path(page_number: int) -> Path:
        if page_number == 1:
            return DIST_DIR / "index.html"
        return DIST_DIR / "page" / str(page_number) / "index.html"

    def rel_link(from_output: Path, to_output: Path) -> str:
        target = to_output.parent if to_output.name == "index.html" else to_output
        rel = os.path.relpath(target, from_output.parent)
        rel_posix = Path(rel).as_posix()
        if not rel_posix or rel_posix == ".":
            return "./" if to_output.name == "index.html" else rel_posix
        return f"{rel_posix.rstrip('/')}/" if to_output.name == "index.html" else rel_posix

    total_pages = max(1, math.ceil(len(posts_list) / POSTS_PER_PAGE))
    for page_num in range(1, total_pages + 1):
        start = (page_num - 1) * POSTS_PER_PAGE
        end = start + POSTS_PER_PAGE
        page_posts = posts_list[start:end]

        pagination = {
            "current_page": page_num,
            "total_pages": total_pages,
            "prev_url": rel_link(page_output_path(page_num), page_output_path(page_num - 1))
            if page_num > 1
            else None,
            "next_url": rel_link(page_output_path(page_num), page_output_path(page_num + 1))
            if page_num < total_pages
            else None,
        }

        index_context = {
            "page_title": site["title"] if page_num == 1 else f"{site['title']} — Page {page_num}",
            "page_path": "" if page_num == 1 else f"page/{page_num}/",
            "page_description": site.get("description", ""),
            "og_type": "website",
            "og_image_path": (
                (page_posts[0].images_meta[0].primary_src or page_posts[0].images_meta[0].path)
                if page_posts and page_posts[0].images_meta
                else None
            ),
            "posts": page_posts,
            "site": site,
            "now": now,
            "pagination": pagination,
            "inline_style": site["inline_style"],
        }
        render_page(env, "index.html", page_output_path(page_num), index_context)

    def infer_post_description(post: Post) -> str:
        if post.excerpt:
            return post.excerpt
        if post.title:
            return post.title
        if post.body_html:
            text = re.sub(r"<[^>]+>", " ", post.body_html)
            text = normalize_meta_text(text)
            if text:
                return text[:160].rstrip()
        return str(site.get("description", "") or "")

    for post in posts_list:
        out_dir = DIST_DIR / str(post.date.year) / f"{post.date.month:02d}" / post.slug
        output_file = out_dir / "index.html"
        context = {
            "page_title": f"{post.title or 'Post'} — {site['title']}",
            "page_path": post.url,
            "page_description": infer_post_description(post),
            "og_type": "article",
            "og_image_path": (
                (post.images_meta[0].primary_src or post.images_meta[0].path)
                if post.images_meta
                else None
            ),
            "post": post,
            "site": site,
            "now": now,
            "inline_style": site["inline_style"],
        }
        render_page(env, "post.html", output_file, context)


def write_sitemap(posts: list[Post], site: dict) -> None:
    absolute_base = public_base_url(site)
    prefix = public_path_prefix(site)

    def loc(path: str) -> str:
        if absolute_base:
            return join_absolute_url(absolute_base, path)
        return join_relative_url(prefix, path)

    def asset_url(path: str) -> str | None:
        if not path:
            return None
        if is_absolute_url(path):
            return path
        candidate = Path(path)
        if candidate.is_absolute():
            return None
        return loc(candidate.as_posix())

    total_pages = max(1, math.ceil(len(posts) / POSTS_PER_PAGE))
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

    sitemap_path = DIST_DIR / "sitemap.xml"
    tree = ET.ElementTree(urlset)
    ET.indent(tree, space="  ")
    tree.write(sitemap_path, encoding="utf-8", xml_declaration=True)
    sitemap_path.write_text(
        sitemap_path.read_text(encoding="utf-8").rstrip() + "\n", encoding="utf-8"
    )


def rewrite_dist_robots(site: dict) -> None:
    robots_path = DIST_DIR / "robots.txt"
    if not robots_path.exists():
        return

    lines = robots_path.read_text(encoding="utf-8").splitlines()
    lines = [line for line in lines if not line.strip().lower().startswith("sitemap:")]

    absolute_base = public_base_url(site)
    if absolute_base:
        sitemap_url = join_absolute_url(absolute_base, "sitemap.xml")
    else:
        sitemap_url = join_relative_url(public_path_prefix(site), "sitemap.xml")

    lines.append("")
    lines.append(f"Sitemap: {sitemap_url}")
    robots_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the static microblog")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config.toml",
        help="Path to site config (TOML)",
    )
    args = parser.parse_args(argv)

    if not args.config.exists():
        raise SystemExit(f"Config not found: {args.config}")

    site = load_config(args.config)
    site["inline_style"] = (ROOT / "theme.css").read_text(encoding="utf-8")
    ensure_empty_dir(DIST_DIR)
    copy_assets()

    posts = collect_posts()
    attach_image_meta(posts)
    env = make_env()
    build(posts, site, env)
    write_sitemap(posts, site)
    rewrite_dist_robots(site)

    try:
        rel = DIST_DIR.relative_to(Path.cwd())
    except ValueError:
        rel = DIST_DIR
    print(f"Built {len(posts)} posts into {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
