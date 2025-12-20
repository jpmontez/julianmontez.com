import datetime as dt
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

import blog.generate as gen


class FeedTests(unittest.TestCase):
    def test_writes_atom_and_rss(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dist_dir = Path(tmp) / "dist"
            dist_dir.mkdir()

            site = {
                "title": "Test Blog",
                "description": "Testing feeds",
                "author": "Test Author",
                "site_url": "http://localhost:8080",
                "base_url": "",
                "feed_max_posts": 25,
            }

            post = gen.Post(
                source=Path("post.md"),
                title="Hello",
                date=dt.date(2024, 1, 2),
                images=["static/photo.jpg"],
                image_alts=[None],
                excerpt="Excerpt",
                layout="photo",
                body_html="<p>Body</p>",
                display_date="02 Jan 2024",
                url="2024/01/hello/",
                slug="hello",
                images_meta=[
                    gen.ImageMeta(
                        path="static/photo.jpg",
                        width=800,
                        height=600,
                        srcset=[("static/photo-480w.jpg", 480), ("static/photo.jpg", 800)],
                        primary_src="static/photo.jpg",
                        alt="Alt text",
                    )
                ],
            )

            with patch.object(gen, "DIST_DIR", dist_dir):
                gen.write_feeds([post], site)

            atom_path = dist_dir / "feed.xml"
            rss_path = dist_dir / "rss.xml"
            self.assertTrue(atom_path.exists())
            self.assertTrue(rss_path.exists())

            atom = ET.parse(atom_path).getroot()
            self.assertEqual(atom.tag, "{http://www.w3.org/2005/Atom}feed")
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            self_link = atom.find("atom:link[@rel='self']", ns)
            self.assertIsNotNone(self_link)
            assert self_link is not None
            self.assertEqual(self_link.attrib["href"], "http://localhost:8080/feed.xml")

            entries = atom.findall("atom:entry", ns)
            self.assertEqual(len(entries), 1)
            entry_link = entries[0].find("atom:link", ns)
            self.assertIsNotNone(entry_link)
            assert entry_link is not None
            self.assertEqual(entry_link.attrib["href"], "http://localhost:8080/2024/01/hello/")

            rss = ET.parse(rss_path).getroot()
            channel = rss.find("channel")
            self.assertIsNotNone(channel)
            assert channel is not None
            rss_ns = {"atom": "http://www.w3.org/2005/Atom"}
            rss_self = channel.find("atom:link", rss_ns)
            self.assertIsNotNone(rss_self)
            assert rss_self is not None
            self.assertEqual(rss_self.attrib["href"], "http://localhost:8080/rss.xml")
            self.assertEqual(rss_self.attrib.get("rel"), "self")
            self.assertEqual(rss_self.attrib.get("type"), "application/rss+xml")
            items = channel.findall("item")
            self.assertEqual(len(items), 1)
            item_link = items[0].findtext("link")
            self.assertEqual(item_link, "http://localhost:8080/2024/01/hello/")


if __name__ == "__main__":
    unittest.main()
