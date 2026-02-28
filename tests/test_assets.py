import tempfile
import unittest
from pathlib import Path

from blog.assets import (
    file_content_hash,
    load_image_manifest,
    prepare_dist,
    save_image_manifest,
)


class PrepareDistTests(unittest.TestCase):
    def test_clean_wipes_everything(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dist = Path(tmp) / "dist"
            dist.mkdir()
            (dist / "index.html").write_text("hi")
            (dist / "static").mkdir()
            (dist / "static" / "photo.jpg").write_text("img")
            (dist / ".image-manifest.json").write_text("{}")

            prepare_dist(dist, clean=True)

            self.assertTrue(dist.exists())
            self.assertEqual(list(dist.iterdir()), [])

    def test_incremental_preserves_static_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dist = Path(tmp) / "dist"
            dist.mkdir()
            (dist / "index.html").write_text("hi")
            (dist / "feed.xml").write_text("<feed/>")
            static = dist / "static"
            static.mkdir()
            (static / "photo.jpg").write_text("img")
            (dist / ".image-manifest.json").write_text("{}")
            subdir = dist / "2024"
            subdir.mkdir()
            (subdir / "page.html").write_text("page")

            prepare_dist(dist, clean=False)

            self.assertTrue(static.exists())
            self.assertTrue((static / "photo.jpg").exists())
            self.assertTrue((dist / ".image-manifest.json").exists())
            self.assertFalse((dist / "index.html").exists())
            self.assertFalse((dist / "feed.xml").exists())
            self.assertFalse(subdir.exists())

    def test_incremental_creates_dist_if_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dist = Path(tmp) / "dist"
            prepare_dist(dist, clean=False)
            self.assertTrue(dist.exists())


class ManifestTests(unittest.TestCase):
    def test_load_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = load_image_manifest(Path(tmp))
            self.assertEqual(result, {})

    def test_load_corrupt_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / ".image-manifest.json"
            manifest.write_text("not valid json!!!", encoding="utf-8")
            result = load_image_manifest(Path(tmp))
            self.assertEqual(result, {})

    def test_load_valid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / ".image-manifest.json"
            manifest.write_text('{"img.jpg": "abc123"}', encoding="utf-8")
            result = load_image_manifest(Path(tmp))
            self.assertEqual(result, {"img.jpg": "abc123"})

    def test_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dist = Path(tmp)
            data = {"static/photo.jpg": "deadbeef", "static/other.png": "cafebabe"}
            save_image_manifest(dist, data)
            loaded = load_image_manifest(dist)
            self.assertEqual(loaded, data)


class FileContentHashTests(unittest.TestCase):
    def test_produces_stable_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.txt"
            path.write_text("hello world", encoding="utf-8")
            h1 = file_content_hash(path)
            h2 = file_content_hash(path)
            self.assertEqual(h1, h2)
            self.assertEqual(len(h1), 8)

    def test_different_content_different_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p1 = Path(tmp) / "a.txt"
            p2 = Path(tmp) / "b.txt"
            p1.write_text("aaa", encoding="utf-8")
            p2.write_text("bbb", encoding="utf-8")
            self.assertNotEqual(file_content_hash(p1), file_content_hash(p2))

    def test_custom_length(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.txt"
            path.write_text("data", encoding="utf-8")
            self.assertEqual(len(file_content_hash(path, length=12)), 12)


if __name__ == "__main__":
    unittest.main()
