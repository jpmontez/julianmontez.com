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


if __name__ == "__main__":
    unittest.main()
