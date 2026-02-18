import tempfile
import unittest
from pathlib import Path

from blog.config import apply_cli_overrides, load_site_config
from blog.models import SiteConfig


class ConfigTests(unittest.TestCase):
    def test_load_site_config_supports_responsive_settings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "config.toml"
            cfg.write_text(
                """title = "Test"
responsive_widths = [1080, 480, 720, 480]
posts_per_page = 12
image_sizes = "(max-width: 600px) 100vw, 700px"
""",
                encoding="utf-8",
            )
            site = load_site_config(cfg)
            self.assertEqual(site.title, "Test")
            self.assertEqual(site.responsive_widths, (480, 720, 1080))
            self.assertEqual(site.posts_per_page, 12)
            self.assertEqual(site.image_sizes, "(max-width: 600px) 100vw, 700px")

    def test_apply_cli_overrides_normalizes_relative_urls(self) -> None:
        site = SiteConfig()
        updated = apply_cli_overrides(
            site,
            base_url="blog",
            feed_self_url="preview",
        )
        self.assertEqual(updated.base_url, "/blog")
        self.assertEqual(updated.feed_self_url, "/preview")

    def test_apply_cli_overrides_rejects_invalid_site_url(self) -> None:
        with self.assertRaises(ValueError):
            apply_cli_overrides(SiteConfig(), site_url="localhost:8080")


if __name__ == "__main__":
    unittest.main()
