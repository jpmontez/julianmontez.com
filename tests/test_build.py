import datetime as dt
import tempfile
import unittest
from pathlib import Path

from blog.models import ImageMeta, Post, SiteConfig
from blog.render import build_site, make_env
from blog.urls import UrlContext


def _post(
    *,
    slug: str,
    date: dt.date,
    title: str | None,
    location_name: str | None = None,
    location_latitude: float | None = None,
    location_longitude: float | None = None,
) -> Post:
    return Post(
        source=Path(f"{slug}.md"),
        title=title,
        date=date,
        images=["static/photo.jpg"],
        image_alts=[None],
        excerpt=None,
        layout="photo",
        body_html="<p>Body</p>",
        display_date=date.strftime("%d %b %Y"),
        url=f"{date.year}/{date.month:02d}/{slug}/",
        slug=slug,
        location_name=location_name,
        location_latitude=location_latitude,
        location_longitude=location_longitude,
        images_meta=[
            ImageMeta(
                path="static/photo.jpg",
                width=800,
                height=600,
                srcset=[("static/photo-480w.jpg", 480), ("static/photo.jpg", 800)],
                webp_srcset=[("static/photo-480w.webp", 480), ("static/photo-800w.webp", 800)],
                avif_srcset=[("static/photo-480w.avif", 480), ("static/photo-800w.avif", 800)],
            )
        ],
    )


class BuildTests(unittest.TestCase):
    def test_build_site_renders_expected_structure_without_post_titles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dist_dir = Path(tmp) / "dist"
            dist_dir.mkdir()
            templates_dir = Path(__file__).resolve().parents[1] / "blog" / "templates"
            env = make_env(templates_dir)

            posts = [
                _post(
                    slug="titled",
                    date=dt.date(2024, 1, 3),
                    title="Titled",
                    location_name="Prospect Park, Brooklyn, NY",
                    location_latitude=40.6602,
                    location_longitude=-73.9690,
                ),
                _post(slug="untitled", date=dt.date(2024, 1, 2), title=None),
            ]
            site = SiteConfig(
                title="Test Blog",
                description="Test description",
                inline_style="body{}",
                posts_per_page=1,
            )
            url_ctx = UrlContext.from_site(site)

            build_site(posts, site=site, env=env, url_ctx=url_ctx, dist_dir=dist_dir)

            index = (dist_dir / "index.html").read_text(encoding="utf-8")
            self.assertIn('class="post-image-link" href="./2024/01/titled/"', index)
            self.assertIn("<picture>", index)
            self.assertIn('type="image/avif"', index)
            self.assertIn("Prospect Park, Brooklyn, NY", index)
            self.assertIn("maps.google.com/?q=40.6602,-73.969", index)
            self.assertNotIn('<h2 class="title">', index)
            self.assertIn('<nav class="feed-nav" aria-label="Feed pagination">', index)
            self.assertIn('href="page/2/"', index)

            untitled = (dist_dir / "2024" / "01" / "untitled" / "index.html").read_text(
                encoding="utf-8"
            )
            self.assertIn("<title>02 Jan 2024 — Test Blog</title>", untitled)
            self.assertNotIn('<h1 class="title">', untitled)
            self.assertIn('<nav class="feed-nav" aria-label="Post navigation">', untitled)

    def test_preload_uses_avif_srcset_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dist_dir = Path(tmp) / "dist"
            dist_dir.mkdir()
            templates_dir = Path(__file__).resolve().parents[1] / "blog" / "templates"
            env = make_env(templates_dir)

            post = _post(slug="avif-post", date=dt.date(2024, 3, 1), title="AVIF Post")
            site = SiteConfig(
                title="Test Blog",
                description="Test description",
                inline_style="body{}",
                eager_images=2,
            )
            url_ctx = UrlContext.from_site(site)
            build_site([post], site=site, env=env, url_ctx=url_ctx, dist_dir=dist_dir)

            index = (dist_dir / "index.html").read_text(encoding="utf-8")
            head = index[: index.find("</head>")]

            # The preload link in <head> must target the AVIF srcset
            self.assertIn('type="image/avif"', head)
            self.assertIn("photo-480w.avif", head)
            self.assertIn("photo-800w.avif", head)


if __name__ == "__main__":
    unittest.main()
