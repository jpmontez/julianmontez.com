import datetime as dt
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from blog.models import ImageMeta, Post, SiteConfig
from blog.seo import rewrite_dist_robots, write_sitemap
from blog.urls import UrlContext


def _post(slug: str, date: dt.date) -> Post:
    return Post(
        source=Path(f"{slug}.md"),
        title=slug,
        date=date,
        images=["static/photo.jpg"],
        image_alts=[None],
        excerpt=None,
        layout="photo",
        body_html="",
        display_date=date.strftime("%d %b %Y"),
        url=f"{date.year}/{date.month:02d}/{slug}/",
        slug=slug,
        images_meta=[ImageMeta(path="static/photo.jpg", width=100, height=80)],
    )


class SeoTests(unittest.TestCase):
    def test_write_sitemap_includes_pages_posts_and_images(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dist_dir = Path(tmp)
            site = SiteConfig(site_url="https://example.com", posts_per_page=1)
            posts = [
                _post("second", dt.date(2024, 1, 3)),
                _post("first", dt.date(2024, 1, 2)),
            ]

            write_sitemap(posts, site=site, url_ctx=UrlContext.from_site(site), dist_dir=dist_dir)
            sitemap = dist_dir / "sitemap.xml"
            self.assertTrue(sitemap.exists())

            root = ET.parse(sitemap).getroot()
            ns = {
                "sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
                "img": "http://www.google.com/schemas/sitemap-image/1.1",
            }
            locs = [el.text for el in root.findall("sm:url/sm:loc", ns)]
            self.assertIn("https://example.com/", locs)
            self.assertIn("https://example.com/page/2/", locs)
            self.assertIn("https://example.com/2024/01/second/", locs)
            self.assertIn("https://example.com/2024/01/first/", locs)

            image_locs = [el.text for el in root.findall("sm:url/img:image/img:loc", ns)]
            self.assertIn("https://example.com/static/photo.jpg", image_locs)

    def test_rewrite_dist_robots_prefers_absolute_generated_sitemap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dist_dir = Path(tmp)
            robots = dist_dir / "robots.txt"
            robots.write_text("User-agent: *\nDisallow:\n", encoding="utf-8")

            site = SiteConfig(site_url="https://example.com")
            rewrite_dist_robots(site=site, url_ctx=UrlContext.from_site(site), dist_dir=dist_dir)

            content = robots.read_text(encoding="utf-8")
            self.assertIn("Sitemap: https://example.com/sitemap.xml", content)

    def test_rewrite_dist_robots_keeps_existing_absolute_when_site_url_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dist_dir = Path(tmp)
            robots = dist_dir / "robots.txt"
            robots.write_text(
                "User-agent: *\nDisallow:\nSitemap: https://fallback.example/sitemap.xml\n",
                encoding="utf-8",
            )

            site = SiteConfig()
            rewrite_dist_robots(site=site, url_ctx=UrlContext.from_site(site), dist_dir=dist_dir)

            content = robots.read_text(encoding="utf-8")
            self.assertIn("Sitemap: https://fallback.example/sitemap.xml", content)


if __name__ == "__main__":
    unittest.main()
