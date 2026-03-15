import datetime as dt
import hashlib
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from blog.images import attach_image_meta, select_lcp_meta
from blog.models import ImageMeta, Post


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
            posts, _ = attach_image_meta(
                [post], root=root, dist_dir=dist_dir, responsive_widths=(50, 100, 200)
            )

            self.assertEqual(len(posts[0].images_meta), 1)
            meta = posts[0].images_meta[0]
            self.assertEqual(meta.width, 120)
            self.assertEqual(meta.height, 80)
            widths = [width for _, width in meta.srcset]
            self.assertEqual(widths, [50, 100, 120])
            self.assertTrue((dist_dir / "static" / "photo-50w.jpg").exists())
            self.assertTrue((dist_dir / "static" / "photo-100w.jpg").exists())

            if meta.webp_srcset:
                webp_widths = [width for _, width in meta.webp_srcset]
                self.assertEqual(webp_widths, [50, 100, 120])
                self.assertTrue((dist_dir / "static" / "photo-120w.webp").exists())

            if meta.avif_srcset:
                avif_widths = [width for _, width in meta.avif_srcset]
                self.assertEqual(avif_widths, [50, 100, 120])
                self.assertTrue((dist_dir / "static" / "photo-120w.avif").exists())

    def test_attach_image_meta_no_images(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dist_dir = root / "dist"
            dist_dir.mkdir()

            post = Post(
                source=Path("post.md"),
                title="No Images",
                date=dt.date(2024, 1, 1),
                images=[],
                image_alts=[],
                excerpt=None,
                layout="photo",
                body_html="",
                display_date="01 Jan 2024",
                url="2024/01/no-images/",
                slug="no-images",
            )
            posts, _ = attach_image_meta(
                [post], root=root, dist_dir=dist_dir, responsive_widths=(480,)
            )
            self.assertEqual(posts[0].images_meta, [])

    def test_all_widths_larger_than_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            static_dir = root / "static"
            static_dir.mkdir()
            dist_dir = root / "dist"
            dist_dir.mkdir()

            source = static_dir / "tiny.jpg"
            Image.new("RGB", (50, 50), color=(128, 128, 128)).save(source)

            post = Post(
                source=Path("post.md"),
                title="Tiny",
                date=dt.date(2024, 1, 1),
                images=["static/tiny.jpg"],
                image_alts=[None],
                excerpt=None,
                layout="photo",
                body_html="",
                display_date="01 Jan 2024",
                url="2024/01/tiny/",
                slug="tiny",
            )
            posts, _ = attach_image_meta(
                [post], root=root, dist_dir=dist_dir, responsive_widths=(200, 400, 800)
            )
            meta = posts[0].images_meta[0]
            # Only the original width should be in the srcset (no upscaling)
            widths = [w for _, w in meta.srcset]
            self.assertEqual(widths, [50])

    def test_missing_image_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dist_dir = root / "dist"
            dist_dir.mkdir()

            post = Post(
                source=Path("post.md"),
                title="Missing",
                date=dt.date(2024, 1, 1),
                images=["static/nonexistent.jpg"],
                image_alts=[None],
                excerpt=None,
                layout="photo",
                body_html="",
                display_date="01 Jan 2024",
                url="2024/01/missing/",
                slug="missing",
            )
            posts, _ = attach_image_meta(
                [post], root=root, dist_dir=dist_dir, responsive_widths=(480,)
            )
            meta = posts[0].images_meta[0]
            self.assertIsNone(meta.width)
            self.assertIsNone(meta.height)

    def test_manifest_cache_hit_skips_regeneration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            static_dir = root / "static"
            static_dir.mkdir()
            dist_dir = root / "dist"
            dist_dir.mkdir()

            source = static_dir / "cached.jpg"
            Image.new("RGB", (200, 100), color=(0, 0, 0)).save(source)

            source_hash = hashlib.md5(source.read_bytes()).hexdigest()  # noqa: S324
            manifest = {"static/cached.jpg": source_hash}

            post = Post(
                source=Path("post.md"),
                title="Cached",
                date=dt.date(2024, 1, 1),
                images=["static/cached.jpg"],
                image_alts=[None],
                excerpt=None,
                layout="photo",
                body_html="",
                display_date="01 Jan 2024",
                url="2024/01/cached/",
                slug="cached",
            )
            posts, new_manifest = attach_image_meta(
                [post],
                root=root,
                dist_dir=dist_dir,
                responsive_widths=(100,),
                image_manifest=manifest,
            )
            # Manifest entry should be unchanged (same hash)
            self.assertEqual(new_manifest["static/cached.jpg"], source_hash)

    def test_manifest_cache_miss_regenerates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            static_dir = root / "static"
            static_dir.mkdir()
            dist_dir = root / "dist"
            dist_dir.mkdir()

            source = static_dir / "changed.jpg"
            Image.new("RGB", (200, 100), color=(0, 0, 0)).save(source)

            # Stale hash that doesn't match current content
            manifest = {"static/changed.jpg": "stale_hash_value"}

            post = Post(
                source=Path("post.md"),
                title="Changed",
                date=dt.date(2024, 1, 1),
                images=["static/changed.jpg"],
                image_alts=[None],
                excerpt=None,
                layout="photo",
                body_html="",
                display_date="01 Jan 2024",
                url="2024/01/changed/",
                slug="changed",
            )
            posts, new_manifest = attach_image_meta(
                [post],
                root=root,
                dist_dir=dist_dir,
                responsive_widths=(100,),
                image_manifest=manifest,
            )
            # Hash should be updated (not the stale value)
            self.assertNotEqual(new_manifest["static/changed.jpg"], "stale_hash_value")

    def test_transcoded_variants_returns_empty_on_error(self) -> None:
        from unittest.mock import patch
        from blog.images import generate_transcoded_variants

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "photo.jpg"
            # Create a real file so path checks pass, but mock Image.open to fail
            source.write_bytes(b"not a real image")
            dist = root / "dist" / "static" / "photo.jpg"

            with patch("blog.images.Image.open", side_effect=OSError("boom")):
                result = generate_transcoded_variants(
                    source_path=source,
                    dist_path=dist,
                    widths=(100,),
                    original=(200, 100),
                    dist_root=root / "dist",
                    output_format="WEBP",
                    output_extension=".webp",
                    save_kwargs={"quality": 80, "method": 6},
                )

            self.assertEqual(result, [])


class SelectLcpMetaTests(unittest.TestCase):
    def test_returns_first_candidate_not_most_portrait(self) -> None:
        """select_lcp_meta returns the first image in DOM order, not the most portrait."""
        first = ImageMeta(path="first.jpg", width=1600, height=400)  # wide → low portrait ratio
        second = ImageMeta(path="second.jpg", width=400, height=1600)  # tall → high portrait ratio
        result = select_lcp_meta([first, second])
        self.assertEqual(result.path, "first.jpg")

    def test_returns_only_candidate(self) -> None:
        meta = ImageMeta(path="only.jpg", width=800, height=600)
        self.assertEqual(select_lcp_meta([meta]), meta)

    def test_returns_none_for_empty(self) -> None:
        self.assertIsNone(select_lcp_meta([]))


if __name__ == "__main__":
    unittest.main()
