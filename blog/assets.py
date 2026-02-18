from __future__ import annotations

import shutil
from pathlib import Path

from blog.models import BuildPaths, SiteConfig


def ensure_empty_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def copy_assets(paths: BuildPaths, site: SiteConfig) -> None:
    if site.emit_style_file:
        shutil.copy2(paths.theme_path, paths.dist_dir / "style.css")
    if paths.static_dir.exists():
        shutil.copytree(paths.static_dir, paths.dist_dir / "static", dirs_exist_ok=True)
    if paths.favicon_path.exists():
        shutil.copy2(paths.favicon_path, paths.dist_dir / "favicon.png")
    if paths.robots_path.exists():
        shutil.copy2(paths.robots_path, paths.dist_dir / "robots.txt")
