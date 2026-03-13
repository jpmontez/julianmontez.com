from __future__ import annotations

import argparse
import sys
from pathlib import Path

from blog.assets import (
    copy_assets,
    file_content_hash,
    load_image_manifest,
    prepare_dist,
    save_image_manifest,
)
from blog.config import apply_cli_overrides, load_site_config
from blog.content import collect_posts
from blog.feeds import write_feeds
from blog.images import attach_image_meta
from blog.models import BuildPaths
from blog.render import build_site, make_env
from blog.seo import rewrite_dist_robots, write_sitemap
from blog.urls import UrlContext

ROOT = Path(__file__).resolve().parent
PATHS = BuildPaths.from_root(ROOT)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the static microblog")
    parser.add_argument(
        "--config",
        type=Path,
        default=PATHS.config_path,
        help="Path to site config (TOML)",
    )
    parser.add_argument(
        "--site-url",
        default=None,
        help=(
            "Override site_url for absolute canonical/sitemap/feed URLs "
            "(e.g. http://localhost:8080)."
        ),
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Override base_url (path prefix or absolute URL) for published links.",
    )
    parser.add_argument(
        "--feed-self-url",
        default=None,
        help="Override base URL used for feed self links (e.g. http://localhost:8080).",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        default=False,
        help="Wipe dist/ completely before building (disables incremental image caching).",
    )
    args = parser.parse_args(argv)

    if not args.config.exists():
        raise SystemExit(f"Config not found: {args.config}")

    try:
        site = load_site_config(args.config)
        site = apply_cli_overrides(
            site,
            site_url=args.site_url,
            base_url=args.base_url,
            feed_self_url=args.feed_self_url,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    fav_hash = file_content_hash(PATHS.favicon_path) if PATHS.favicon_path.exists() else ""
    site = site.with_runtime(
        inline_style=PATHS.theme_path.read_text(encoding="utf-8"),
        favicon_hash=fav_hash,
    )
    url_ctx = UrlContext.from_site(site)

    prev_manifest = load_image_manifest(PATHS.dist_dir) if not args.clean else {}
    prepare_dist(PATHS.dist_dir, clean=args.clean)
    copy_assets(PATHS, site)

    posts = collect_posts(PATHS.posts_dir)
    posts, new_manifest = attach_image_meta(
        posts,
        root=PATHS.root,
        dist_dir=PATHS.dist_dir,
        responsive_widths=site.responsive_widths,
        image_manifest=prev_manifest,
    )
    save_image_manifest(PATHS.dist_dir, new_manifest)

    env = make_env(PATHS.templates_dir)
    build_site(posts, site=site, env=env, url_ctx=url_ctx, dist_dir=PATHS.dist_dir)
    write_sitemap(posts, site=site, url_ctx=url_ctx, dist_dir=PATHS.dist_dir)
    rewrite_dist_robots(site=site, url_ctx=url_ctx, dist_dir=PATHS.dist_dir)
    write_feeds(posts, site=site, url_ctx=url_ctx, dist_dir=PATHS.dist_dir)

    try:
        rel = PATHS.dist_dir.relative_to(Path.cwd())
    except ValueError:
        rel = PATHS.dist_dir
    print(f"Built {len(posts)} posts into {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
