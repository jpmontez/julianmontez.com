import tempfile
import unittest
from pathlib import Path

from blog.content import parse_front_matter, parse_images, parse_location, parse_post


class ContentTests(unittest.TestCase):
    def test_parse_front_matter_accepts_plus_delimiters(self) -> None:
        raw = """++++
title = "A"
date = 2024-10-12
++++

Body
"""
        meta, body = parse_front_matter(raw)
        self.assertEqual(meta["title"], "A")
        self.assertEqual(str(meta["date"]), "2024-10-12")
        self.assertEqual(body, "Body")

    def test_parse_images_supports_strings_and_tables(self) -> None:
        images, alts = parse_images(
            {
                "images": [
                    "static/one.jpg",
                    {"src": "static/two.jpg", "alt": "Alt"},
                ]
            },
            Path("post.md"),
        )
        self.assertEqual(images, ["static/one.jpg", "static/two.jpg"])
        self.assertEqual(alts, [None, "Alt"])

    def test_parse_post_requires_valid_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.md"
            path.write_text(
                """+++
title = "Bad"
date = "not-a-date"
+++
Body
""",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                parse_post(path)

    def test_parse_location_supports_named_coordinates(self) -> None:
        name, lat, lon = parse_location(
            {"location": {"name": "Brooklyn Bridge Park", "lat": 40.7003, "lon": -73.9967}},
            Path("post.md"),
        )
        self.assertEqual(name, "Brooklyn Bridge Park")
        self.assertEqual(lat, 40.7003)
        self.assertEqual(lon, -73.9967)

    def test_parse_location_rejects_partial_coordinates(self) -> None:
        with self.assertRaises(ValueError):
            parse_location({"location": {"name": "Incomplete", "lat": 40.7}}, Path("post.md"))

    def test_parse_images_empty_list(self) -> None:
        images, alts = parse_images({"images": []}, Path("post.md"))
        self.assertEqual(images, [])
        self.assertEqual(alts, [])

    def test_parse_images_dict_missing_src(self) -> None:
        with self.assertRaises(ValueError):
            parse_images({"images": [{"alt": "no source"}]}, Path("post.md"))

    def test_parse_images_none_field(self) -> None:
        images, alts = parse_images({"images": None}, Path("post.md"))
        self.assertEqual(images, [])
        self.assertEqual(alts, [])

    def test_parse_images_missing_field(self) -> None:
        images, alts = parse_images({}, Path("post.md"))
        self.assertEqual(images, [])
        self.assertEqual(alts, [])

    def test_parse_location_empty_string(self) -> None:
        name, lat, lon = parse_location({"location": ""}, Path("post.md"))
        self.assertIsNone(name)
        self.assertIsNone(lat)
        self.assertIsNone(lon)

    def test_parse_location_boundary_coordinates(self) -> None:
        name, lat, lon = parse_location(
            {"location": {"lat": 90.0, "lon": -180.0}}, Path("post.md")
        )
        self.assertIsNone(name)
        self.assertEqual(lat, 90.0)
        self.assertEqual(lon, -180.0)

    def test_parse_location_zero_coordinates(self) -> None:
        name, lat, lon = parse_location(
            {"location": {"lat": 0, "lon": 0}}, Path("post.md")
        )
        self.assertEqual(lat, 0.0)
        self.assertEqual(lon, 0.0)

    def test_parse_front_matter_no_body(self) -> None:
        raw = "+++\ntitle = \"No body\"\ndate = 2024-01-01\n+++\n"
        meta, body = parse_front_matter(raw)
        self.assertEqual(meta["title"], "No body")
        self.assertEqual(body, "")

    def test_parse_front_matter_empty_post(self) -> None:
        with self.assertRaises(ValueError) as cm:
            parse_front_matter("", source=Path("empty.md"))
        self.assertIn("empty.md", str(cm.exception))

    def test_parse_post_no_images_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "no-images.md"
            path.write_text(
                "+++\ndate = 2024-06-15\ntitle = \"No images\"\n+++\n\nSome text.\n",
                encoding="utf-8",
            )
            post = parse_post(path)
            self.assertEqual(post.images, [])
            self.assertEqual(post.image_alts, [])


if __name__ == "__main__":
    unittest.main()
