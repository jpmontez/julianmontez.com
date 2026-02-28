from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from blog.models import BuildPaths, SiteConfig

MANIFEST_NAME = ".image-manifest.json"


def ensure_empty_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def prepare_dist(dist_dir: Path, *, clean: bool) -> None:
    if clean:
        ensure_empty_dir(dist_dir)
        return

    dist_dir.mkdir(parents=True, exist_ok=True)
    for child in dist_dir.iterdir():
        if child.name == "static":
            continue
        if child.name == MANIFEST_NAME:
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def file_content_hash(path: Path, length: int = 8) -> str:
    digest = hashlib.md5(path.read_bytes()).hexdigest()  # noqa: S324
    return digest[:length]


def load_image_manifest(dist_dir: Path) -> dict[str, str]:
    manifest_path = dist_dir / MANIFEST_NAME
    if not manifest_path.exists():
        return {}
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_image_manifest(dist_dir: Path, manifest: dict[str, str]) -> None:
    manifest_path = dist_dir / MANIFEST_NAME
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def copy_assets(paths: BuildPaths, site: SiteConfig) -> None:
    if site.emit_style_file:
        shutil.copy2(paths.theme_path, paths.dist_dir / "style.css")
    if paths.static_dir.exists():
        shutil.copytree(paths.static_dir, paths.dist_dir / "static", dirs_exist_ok=True)
    if paths.favicon_path.exists():
        shutil.copy2(paths.favicon_path, paths.dist_dir / "favicon.png")
    if paths.robots_path.exists():
        shutil.copy2(paths.robots_path, paths.dist_dir / "robots.txt")
