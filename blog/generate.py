from __future__ import annotations

import argparse
import datetime as dt
import math
import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import tomllib

try:
    from jinja2 import Environment, FileSystemLoader
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


@dataclass
class ImageMeta:
    path: str
    width: int | None
    height: int | None

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


def parse_post(path: Path) -> Post:
    raw = path.read_text(encoding="utf-8")
    meta, body_md = parse_front_matter(raw)

    try:
        date = dt.date.fromisoformat(str(meta["date"]))
    except Exception as exc:  # pragma: no cover - strict input validation
        raise ValueError(f"Invalid or missing date in {path}") from exc

    title = meta.get("title")
    images = list(meta.get("images", []))
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


def attach_image_meta(posts: list[Post]) -> None:
    cache: dict[str, tuple[int | None, int | None]] = {}

    for post in posts:
        metas: list[ImageMeta] = []
        for image in post.images:
            if image not in cache:
                candidate = Path(image)
                image_path = candidate if candidate.is_absolute() else ROOT / candidate
                cache[image] = image_dimensions(image_path)

            width, height = cache[image]
            metas.append(ImageMeta(path=image, width=width, height=height))

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
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
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


def render_page(env: Environment, template_name: str, output_path: Path, context: dict) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    base_url = context["site"].get("base_url", "")
    assets_prefix = compute_assets_prefix(output_path, base_url)
    template = env.get_template(template_name)
    html = template.render(**context, assets_prefix=assets_prefix)
    output_path.write_text(html, encoding="utf-8")


def build(posts: Iterable[Post], site: dict, env: Environment) -> None:
    now = dt.datetime.now(dt.timezone.utc)
    posts_list = list(posts)

    def page_output_path(page_number: int) -> Path:
        if page_number == 1:
            return DIST_DIR / "index.html"
        return DIST_DIR / "page" / str(page_number) / "index.html"

    def rel_link(from_output: Path, to_output: Path) -> str:
        rel = os.path.relpath(to_output, from_output.parent)
        rel_posix = Path(rel).as_posix()
        return rel_posix if rel_posix else "./"

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
            "posts": page_posts,
            "site": site,
            "now": now,
            "pagination": pagination,
            "inline_style": site["inline_style"],
        }
        render_page(env, "index.html", page_output_path(page_num), index_context)

    for post in posts_list:
        out_dir = DIST_DIR / str(post.date.year) / f"{post.date.month:02d}" / post.slug
        output_file = out_dir / "index.html"
        context = {
            "page_title": f"{post.title or 'Post'} — {site['title']}",
            "post": post,
            "site": site,
            "now": now,
            "inline_style": site["inline_style"],
        }
        render_page(env, "post.html", output_file, context)


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

    try:
        rel = DIST_DIR.relative_to(Path.cwd())
    except ValueError:
        rel = DIST_DIR
    print(f"Built {len(posts)} posts into {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
