#!/usr/bin/env python3
"""Convert blog posts from TOML frontmatter to YAML frontmatter for Astro.

Reads .md files from blog/posts/YYYY/MM/, converts TOML frontmatter (+++/++++)
to YAML frontmatter (---), rewrites image paths, and copies images and favicon.
"""

import re
import shutil
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # Python < 3.11

import yaml


ROOT = Path(__file__).resolve().parent.parent
POSTS_SRC = ROOT / "blog" / "posts"
POSTS_DST = ROOT / "src" / "content" / "posts"
PHOTOS_DST = ROOT / "src" / "assets" / "photos"
PUBLIC_DIR = ROOT / "public"
STATIC_SRC = ROOT / "blog" / "static"
FAVICON_SRC = ROOT / "blog" / "favicon.png"

# Relative path from src/content/posts/ to src/assets/photos/
IMAGE_REL_PREFIX = "../../assets/photos/"


def parse_toml_frontmatter(text: str) -> tuple[dict, str]:
    """Parse TOML frontmatter delimited by +++ or ++++, return (meta, body)."""
    m = re.match(r"^\+{3,4}\n(.*?)\n\+{3,4}\n?(.*)", text, re.DOTALL)
    if not m:
        raise ValueError("No TOML frontmatter found")
    toml_str = m.group(1)
    body = m.group(2)
    meta = tomllib.loads(toml_str)
    return meta, body


def convert_frontmatter(meta: dict) -> str:
    """Convert parsed TOML metadata dict to YAML frontmatter string."""
    out = {}

    # date as ISO string
    if "date" in meta:
        out["date"] = meta["date"].isoformat() if hasattr(meta["date"], "isoformat") else str(meta["date"])

    # layout
    if "layout" in meta:
        out["layout"] = meta["layout"]

    # title
    if "title" in meta:
        out["title"] = meta["title"]

    # excerpt
    if "excerpt" in meta:
        out["excerpt"] = meta["excerpt"]

    # location
    if "location" in meta:
        out["location"] = meta["location"]

    # images: rewrite src paths
    if "images" in meta:
        images = []
        for img in meta["images"]:
            new_img = dict(img)
            src = new_img.get("src", "")
            # Convert static/filename.jpg -> ../../assets/photos/filename.jpg
            if src.startswith("static/"):
                filename = src.removeprefix("static/")
                new_img["src"] = IMAGE_REL_PREFIX + filename
            images.append(new_img)
        out["images"] = images

    return yaml.dump(out, default_flow_style=False, sort_keys=False, allow_unicode=True).rstrip("\n")


def convert_posts():
    """Convert all posts from TOML to YAML frontmatter."""
    POSTS_DST.mkdir(parents=True, exist_ok=True)

    md_files = sorted(POSTS_SRC.glob("**/????-??-??-*.md"))
    print(f"Found {len(md_files)} posts to convert")

    for src_path in md_files:
        text = src_path.read_text(encoding="utf-8")
        meta, body = parse_toml_frontmatter(text)
        yaml_fm = convert_frontmatter(meta)
        output = f"---\n{yaml_fm}\n---\n{body}"

        dst_path = POSTS_DST / src_path.name
        dst_path.write_text(output, encoding="utf-8")
        print(f"  Converted: {src_path.name}")

    print(f"Converted {len(md_files)} posts to {POSTS_DST}")


def copy_images():
    """Copy source images from blog/static/ to src/assets/photos/."""
    PHOTOS_DST.mkdir(parents=True, exist_ok=True)

    count = 0
    for ext in ("*.jpg", "*.png"):
        for src_path in sorted(STATIC_SRC.glob(ext)):
            dst_path = PHOTOS_DST / src_path.name
            shutil.copy2(src_path, dst_path)
            count += 1
            print(f"  Copied: {src_path.name}")

    print(f"Copied {count} images to {PHOTOS_DST}")


def copy_favicon():
    """Copy favicon to public/."""
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    dst = PUBLIC_DIR / "favicon.png"
    shutil.copy2(FAVICON_SRC, dst)
    print(f"Copied favicon to {dst}")


def main():
    print("Converting posts...")
    convert_posts()
    print()
    print("Copying images...")
    copy_images()
    print()
    print("Copying favicon...")
    copy_favicon()
    print()
    print("Done!")


if __name__ == "__main__":
    main()
