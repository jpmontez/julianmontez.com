"""Snapshot tests for generated HTML output.

These tests render pages with known inputs and compare the output against
stored snapshots.  When templates or rendering logic change intentionally,
update snapshots by running::

    UPDATE_SNAPSHOTS=1 make test
"""

from __future__ import annotations

import datetime as dt
import os
import re
import tempfile
import unittest
from pathlib import Path

from blog.models import ImageMeta, Post, SiteConfig
from blog.render import build_site, make_env
from blog.urls import UrlContext

SNAPSHOTS_DIR = Path(__file__).resolve().parent / "snapshots"

# Strip dynamic content that changes between runs (e.g., copyright year).
_YEAR_RE = re.compile(r"&copy; \d{4}")


def _normalize(html: str) -> str:
    html = _YEAR_RE.sub("&copy; YYYY", html)
    return html.strip() + "\n"


def _make_post(
    *,
    slug: str = "test-post",
    date: dt.date = dt.date(2024, 6, 15),
    title: str | None = None,
    excerpt: str | None = "A test excerpt.",
    body_html: str = "<p>Body content here.</p>",
    location_name: str | None = "Brooklyn, NY",
    location_latitude: float | None = 40.6602,
    location_longitude: float | None = -73.969,
    num_images: int = 1,
) -> Post:
    images_meta = []
    images = []
    image_alts: list[str | None] = []
    for i in range(num_images):
        img_name = f"static/photo-{i}.jpg"
        images.append(img_name)
        image_alts.append(f"Alt text {i}")
        images_meta.append(
            ImageMeta(
                path=img_name,
                width=1200,
                height=800,
                srcset=[(f"static/photo-{i}-480w.jpg", 480), (f"static/photo-{i}.jpg", 1200)],
                webp_srcset=[
                    (f"static/photo-{i}-480w.webp", 480),
                    (f"static/photo-{i}-1200w.webp", 1200),
                ],
                avif_srcset=[
                    (f"static/photo-{i}-480w.avif", 480),
                    (f"static/photo-{i}-1200w.avif", 1200),
                ],
                primary_src=f"static/photo-{i}.jpg",
                alt=f"Alt text {i}",
            )
        )

    return Post(
        source=Path(f"{slug}.md"),
        title=title,
        date=date,
        images=images,
        image_alts=image_alts,
        excerpt=excerpt,
        layout="photo",
        body_html=body_html,
        display_date=date.strftime("%d %b %Y"),
        url=f"{date.year}/{date.month:02d}/{slug}/",
        slug=slug,
        location_name=location_name,
        location_latitude=location_latitude,
        location_longitude=location_longitude,
        images_meta=images_meta,
    )


def _build_and_collect(posts: list[Post], site: SiteConfig) -> dict[str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        dist_dir = Path(tmp) / "dist"
        dist_dir.mkdir()
        templates_dir = Path(__file__).resolve().parents[1] / "blog" / "templates"
        env = make_env(templates_dir)
        url_ctx = UrlContext.from_site(site)
        build_site(posts, site=site, env=env, url_ctx=url_ctx, dist_dir=dist_dir)

        result: dict[str, str] = {}
        for html_file in sorted(dist_dir.rglob("*.html")):
            key = html_file.relative_to(dist_dir).as_posix()
            result[key] = _normalize(html_file.read_text(encoding="utf-8"))
        return result


class SnapshotTests(unittest.TestCase):
    def _check_snapshot(self, name: str, actual: str) -> None:
        snapshot_path = SNAPSHOTS_DIR / name
        if os.environ.get("UPDATE_SNAPSHOTS"):
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            snapshot_path.write_text(actual, encoding="utf-8")
            return

        if not snapshot_path.exists():
            self.fail(
                f"Snapshot {name} does not exist. Run with UPDATE_SNAPSHOTS=1 to create it."
            )

        expected = snapshot_path.read_text(encoding="utf-8")
        if actual != expected:
            # Show first divergent line for easier debugging.
            actual_lines = actual.splitlines()
            expected_lines = expected.splitlines()
            for i, (a, e) in enumerate(zip(actual_lines, expected_lines), 1):
                if a != e:
                    self.fail(
                        f"Snapshot {name} differs at line {i}:\n"
                        f"  expected: {e!r}\n"
                        f"  actual:   {a!r}\n"
                        f"Run with UPDATE_SNAPSHOTS=1 to update."
                    )
            if len(actual_lines) != len(expected_lines):
                self.fail(
                    f"Snapshot {name} has {len(actual_lines)} lines, expected {len(expected_lines)}.\n"
                    f"Run with UPDATE_SNAPSHOTS=1 to update."
                )

    def test_single_image_post_page(self) -> None:
        post = _make_post(num_images=1)
        site = SiteConfig(
            title="Test Blog",
            description="A test blog",
            author="Test Author",
            site_url="https://example.com",
            inline_style="body{}",
        )
        pages = _build_and_collect([post], site)
        post_key = "2024/06/test-post/index.html"
        self.assertIn(post_key, pages)
        self._check_snapshot("post_single_image.html", pages[post_key])

    def test_multi_image_post_page(self) -> None:
        post = _make_post(num_images=3)
        site = SiteConfig(
            title="Test Blog",
            description="A test blog",
            author="Test Author",
            site_url="https://example.com",
            inline_style="body{}",
        )
        pages = _build_and_collect([post], site)
        post_key = "2024/06/test-post/index.html"
        self.assertIn(post_key, pages)
        self._check_snapshot("post_multi_image.html", pages[post_key])

    def test_index_page(self) -> None:
        post = _make_post(num_images=1)
        site = SiteConfig(
            title="Test Blog",
            description="A test blog",
            author="Test Author",
            site_url="https://example.com",
            inline_style="body{}",
        )
        pages = _build_and_collect([post], site)
        self.assertIn("index.html", pages)
        self._check_snapshot("index.html", pages["index.html"])


if __name__ == "__main__":
    unittest.main()
