import datetime as dt
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from blog.images import attach_image_meta
from blog.models import Post


class ImageTests(unittest.TestCase):
    def test_attach_image_meta_generates_responsive_variants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            static_dir = root / "static"
            static_dir.mkdir()
            dist_dir = root / "dist"
            dist_dir.mkdir()

            source = static_dir / "photo.jpg"
            Image.new("RGB", (120, 80), color=(255, 255, 255)).save(source)

            post = Post(
                source=Path("post.md"),
                title="Image Test",
                date=dt.date(2024, 1, 1),
                images=["static/photo.jpg"],
                image_alts=[None],
                excerpt=None,
                layout="photo",
                body_html="",
                display_date="01 Jan 2024",
                url="2024/01/image-test/",
                slug="image-test",
            )
            attach_image_meta(
                [post], root=root, dist_dir=dist_dir, responsive_widths=(50, 100, 200)
            )

            self.assertEqual(len(post.images_meta), 1)
            meta = post.images_meta[0]
            self.assertEqual(meta.width, 120)
            self.assertEqual(meta.height, 80)
            widths = [width for _, width in meta.srcset]
            self.assertEqual(widths, [50, 100, 120])
            self.assertTrue((dist_dir / "static" / "photo-50w.jpg").exists())
            self.assertTrue((dist_dir / "static" / "photo-100w.jpg").exists())


if __name__ == "__main__":
    unittest.main()
