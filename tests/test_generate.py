import shutil
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

from blog.generate import main

REAL_TEMPLATES = Path(__file__).resolve().parent.parent / "blog" / "templates"


class GenerateMainTests(unittest.TestCase):
    def _create_minimal_site(self, tmp: str) -> Path:
        root = Path(tmp)
        config = root / "config.toml"
        config.write_text(
            textwrap.dedent("""\
                title = "Test"
                site_url = "http://localhost:8080"
            """),
            encoding="utf-8",
        )
        posts_dir = root / "posts"
        posts_dir.mkdir()
        (posts_dir / "hello.md").write_text(
            textwrap.dedent("""\
                +++
                date = 2024-01-01
                title = "Hello"
                +++

                Body text.
            """),
            encoding="utf-8",
        )
        templates_dir = root / "templates"
        shutil.copytree(REAL_TEMPLATES, templates_dir)
        theme = root / "theme.css"
        theme.write_text("body { margin: 0; }", encoding="utf-8")
        return root

    def _apply_paths(self, mock_paths: object, root: Path) -> None:
        from blog.models import BuildPaths

        paths = BuildPaths.from_root(root)
        for field in (
            "root", "posts_dir", "static_dir", "dist_dir", "templates_dir",
            "config_path", "theme_path", "robots_path", "favicon_path",
        ):
            setattr(mock_paths, field, getattr(paths, field))

    @patch("blog.generate.PATHS")
    @patch("blog.generate.ROOT")
    def test_main_with_missing_config(self, mock_root: object, mock_paths: object) -> None:
        with self.assertRaises(SystemExit) as cm:
            main(["--config", "/nonexistent/config.toml"])
        self.assertIn("Config not found", str(cm.exception))

    @patch("blog.generate.PATHS")
    @patch("blog.generate.ROOT")
    def test_main_with_minimal_site(self, mock_root: object, mock_paths: object) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._create_minimal_site(tmp)
            self._apply_paths(mock_paths, root)

            result = main(["--config", str(root / "config.toml")])
            self.assertEqual(result, 0)
            self.assertTrue((root / "dist" / "index.html").exists())

    @patch("blog.generate.PATHS")
    @patch("blog.generate.ROOT")
    def test_main_clean_flag(self, mock_root: object, mock_paths: object) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._create_minimal_site(tmp)
            self._apply_paths(mock_paths, root)

            result = main(["--config", str(root / "config.toml"), "--clean"])
            self.assertEqual(result, 0)

    @patch("blog.generate.PATHS")
    @patch("blog.generate.ROOT")
    def test_main_site_url_override(self, mock_root: object, mock_paths: object) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._create_minimal_site(tmp)
            self._apply_paths(mock_paths, root)

            result = main([
                "--config", str(root / "config.toml"),
                "--site-url", "http://example.com",
            ])
            self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
