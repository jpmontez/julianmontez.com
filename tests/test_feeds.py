import datetime as dt
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from blog.feeds import write_feeds
from blog.models import ImageMeta, Post, SiteConfig
from blog.urls import UrlContext


class FeedTests(unittest.TestCase):
    def test_writes_atom_and_rss(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dist_dir = Path(tmp) / "dist"
            dist_dir.mkdir()

            site = SiteConfig(
                title="Test Blog",
                description="Testing feeds",
                author="Test Author",
                site_url="http://localhost:8080",
                feed_max_posts=25,
            )
            post = Post(
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
                    ImageMeta(
                        path="static/photo.jpg",
                        width=800,
                        height=600,
                        srcset=[("static/photo-480w.jpg", 480), ("static/photo.jpg", 800)],
                        primary_src="static/photo.jpg",
                        alt="Alt text",
                    )
                ],
            )

            write_feeds([post], site=site, url_ctx=UrlContext.from_site(site), dist_dir=dist_dir)

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


    def test_atom_feed_has_required_elements(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dist_dir = Path(tmp) / "dist"
            dist_dir.mkdir()

            site = SiteConfig(
                title="Test Blog",
                description="Testing feeds",
                author="Test Author",
                site_url="http://localhost:8080",
                feed_max_posts=25,
            )
            post = Post(
                source=Path("post.md"),
                title="Hello",
                date=dt.date(2024, 1, 2),
                images=["static/photo.jpg"],
                image_alts=["Alt text"],
                excerpt="Excerpt",
                layout="photo",
                body_html="<p>Body</p>",
                display_date="02 Jan 2024",
                url="2024/01/hello/",
                slug="hello",
                images_meta=[
                    ImageMeta(
                        path="static/photo.jpg",
                        width=800,
                        height=600,
                        srcset=[("static/photo-480w.jpg", 480), ("static/photo.jpg", 800)],
                        primary_src="static/photo.jpg",
                        alt="Alt text",
                    )
                ],
            )

            write_feeds([post], site=site, url_ctx=UrlContext.from_site(site), dist_dir=dist_dir)

            atom_path = dist_dir / "feed.xml"
            atom = ET.parse(atom_path).getroot()
            ns = {"atom": "http://www.w3.org/2005/Atom"}

            # Required top-level Atom elements
            self.assertIsNotNone(atom.find("atom:title", ns))
            self.assertIsNotNone(atom.find("atom:id", ns))
            self.assertIsNotNone(atom.find("atom:updated", ns))
            self.assertIsNotNone(atom.find("atom:link", ns))
            self.assertIsNotNone(atom.find("atom:author/atom:name", ns))

            # Entry required elements
            entry = atom.find("atom:entry", ns)
            self.assertIsNotNone(entry)
            assert entry is not None
            self.assertIsNotNone(entry.find("atom:title", ns))
            self.assertIsNotNone(entry.find("atom:id", ns))
            self.assertIsNotNone(entry.find("atom:updated", ns))
            self.assertIsNotNone(entry.find("atom:link", ns))

            # Content should be present and non-empty
            content = entry.find("atom:content", ns)
            self.assertIsNotNone(content)
            assert content is not None
            self.assertTrue(content.text and len(content.text.strip()) > 0)

    def test_rss_feed_has_required_elements(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dist_dir = Path(tmp) / "dist"
            dist_dir.mkdir()

            site = SiteConfig(
                title="Test Blog",
                description="Testing feeds",
                author="Test Author",
                site_url="http://localhost:8080",
                feed_max_posts=25,
            )
            post = Post(
                source=Path("post.md"),
                title="Hello",
                date=dt.date(2024, 1, 2),
                images=["static/photo.jpg"],
                image_alts=["Alt text"],
                excerpt="Excerpt",
                layout="photo",
                body_html="<p>Body</p>",
                display_date="02 Jan 2024",
                url="2024/01/hello/",
                slug="hello",
                images_meta=[
                    ImageMeta(
                        path="static/photo.jpg",
                        width=800,
                        height=600,
                        srcset=[("static/photo-480w.jpg", 480), ("static/photo.jpg", 800)],
                        primary_src="static/photo.jpg",
                        alt="Alt text",
                    )
                ],
            )

            write_feeds([post], site=site, url_ctx=UrlContext.from_site(site), dist_dir=dist_dir)

            rss_path = dist_dir / "rss.xml"
            rss = ET.parse(rss_path).getroot()

            # RSS 2.0 structure
            self.assertEqual(rss.tag, "rss")
            self.assertEqual(rss.attrib.get("version"), "2.0")

            channel = rss.find("channel")
            self.assertIsNotNone(channel)
            assert channel is not None

            # Required channel elements
            self.assertIsNotNone(channel.find("title"))
            self.assertIsNotNone(channel.find("link"))
            self.assertIsNotNone(channel.find("description"))
            self.assertIsNotNone(channel.find("lastBuildDate"))

            # Item required elements
            item = channel.find("item")
            self.assertIsNotNone(item)
            assert item is not None
            self.assertIsNotNone(item.find("title"))
            self.assertIsNotNone(item.find("link"))
            self.assertIsNotNone(item.find("guid"))
            self.assertIsNotNone(item.find("pubDate"))
            self.assertIsNotNone(item.find("description"))

    def test_feeds_with_no_posts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dist_dir = Path(tmp) / "dist"
            dist_dir.mkdir()

            site = SiteConfig(
                title="Empty Blog",
                description="No posts",
                site_url="http://localhost:8080",
            )

            write_feeds([], site=site, url_ctx=UrlContext.from_site(site), dist_dir=dist_dir)

            # Both feeds should be valid XML even with no posts
            atom = ET.parse(dist_dir / "feed.xml").getroot()
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            self.assertEqual(atom.tag, "{http://www.w3.org/2005/Atom}feed")
            self.assertEqual(len(atom.findall("atom:entry", ns)), 0)

            rss = ET.parse(dist_dir / "rss.xml").getroot()
            channel = rss.find("channel")
            assert channel is not None
            self.assertEqual(len(channel.findall("item")), 0)


if __name__ == "__main__":
    unittest.main()
