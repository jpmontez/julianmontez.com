from __future__ import annotations

import argparse
import sys
from pathlib import Path

from blog.assets import copy_assets, ensure_empty_dir
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

    site = site.with_runtime(inline_style=PATHS.theme_path.read_text(encoding="utf-8"))
    url_ctx = UrlContext.from_site(site)

    ensure_empty_dir(PATHS.dist_dir)
    copy_assets(PATHS, site)

    posts = collect_posts(PATHS.posts_dir)
    attach_image_meta(
        posts,
        root=PATHS.root,
        dist_dir=PATHS.dist_dir,
        responsive_widths=site.responsive_widths,
    )

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
