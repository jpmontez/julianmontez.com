import unittest

from blog.models import SiteConfig
from blog.urls import UrlContext


class UrlContextTests(unittest.TestCase):
    def test_absolute_site_url_builds_absolute_paths(self) -> None:
        site = SiteConfig(site_url="https://example.com", base_url="/blog")
        url_ctx = UrlContext.from_site(site)
        self.assertEqual(url_ctx.page(""), "https://example.com/blog/")
        self.assertEqual(url_ctx.page("2024/01/post/"), "https://example.com/blog/2024/01/post/")
        self.assertEqual(
            url_ctx.asset("static/photo.jpg"), "https://example.com/blog/static/photo.jpg"
        )

    def test_relative_base_url_uses_prefix(self) -> None:
        site = SiteConfig(base_url="/blog")
        url_ctx = UrlContext.from_site(site)
        self.assertEqual(url_ctx.page(""), "/blog/")
        self.assertEqual(url_ctx.page("feed.xml"), "/blog/feed.xml")
        self.assertEqual(url_ctx.feed_self("rss.xml"), "/blog/rss.xml")

    def test_feed_self_override_can_be_relative(self) -> None:
        site = SiteConfig(site_url="https://example.com", feed_self_url="/preview")
        url_ctx = UrlContext.from_site(site)
        self.assertEqual(url_ctx.feed_self("feed.xml"), "/preview/feed.xml")


if __name__ == "__main__":
    unittest.main()
