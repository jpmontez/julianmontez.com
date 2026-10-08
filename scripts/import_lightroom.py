#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# ///
"""Import Lightroom JPG exports into the blog assets and scaffold one post per photo with alt text from Claude Code."""

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHOTOS_DIR = ROOT / "src" / "assets" / "photos"
POSTS_DIR = ROOT / "src" / "content" / "posts"

# Lightroom export format: YYYYMMDD-DSC_NNNN.jpg (Nikon) or YYYYMMDD-DSCFNNNN.jpg (Fujifilm), optionally
# with the -Edit suffix Lightroom adds after an external edit (dropped from the imported name)
SOURCE_PATTERN = re.compile(r"^(?P<date>\d{8})-(?P<frame>DSC_\d{4,}|DSCF\d{4,})(?:-Edit)?\.jpg$", re.IGNORECASE)

ALT_PROMPT = (
    "Read the image file below, then write alt text for it as a photograph on a photoblog. "
    "One plain sentence, under 125 characters, describing the subject and setting as a sighted viewer "
    'would see them. Don\'t begin with "Image of" or "Photo of", and don\'t guess at specific place names. '
    "Reply with only the alt text, no quotes or commentary."
)


@dataclass
class Photo:
    source: Path
    date: dt.date
    destination: Path


def parse_candidates(source_dir):
    photos = []
    for path in sorted(source_dir.iterdir()):
        match = SOURCE_PATTERN.match(path.name)
        if not (path.is_file() and match):
            continue
        try:
            date = dt.datetime.strptime(match["date"], "%Y%m%d").date()
        except ValueError:
            print(f"Skipping {path.name}: invalid date {match['date']}", file=sys.stderr)
            continue
        photos.append(Photo(path, date, PHOTOS_DIR / f"{date}-{match['frame'].upper()}.jpg"))
    return photos


def copy_photos(photos, overwrite):
    """Copy every photo; return those no post references yet, so an interrupted run's photos still get posts."""
    posts = "".join(path.read_text(encoding="utf-8") for path in POSTS_DIR.glob("*.md"))
    new = []
    for photo in photos:
        if photo.destination.exists() and not overwrite:
            reply = input(f"{photo.destination.name} already exists. Overwrite with {photo.source.name}? [y/N]: ")
            if reply.strip().lower() not in {"y", "yes"}:
                print(f"Skipping {photo.destination.name} (exists)")
                continue
        shutil.copy2(photo.source, photo.destination)
        print(f"Copied {photo.source} -> {photo.destination}")
        if photo.destination.name not in posts:
            new.append(photo)
    return new


def alt_text(photo):
    # Headless Claude Code reads the image with its Read tool. ANTHROPIC_API_KEY is dropped so usage
    # bills to the Claude Code login instead of a pay-per-use API account.
    env = {key: value for key, value in os.environ.items() if key != "ANTHROPIC_API_KEY"}
    result = subprocess.run(
        ["claude", "-p", f"{ALT_PROMPT}\n\n{photo.destination}", "--allowedTools", "Read"],
        capture_output=True,
        text=True,
        check=True,
        cwd=ROOT,
        env=env,
    )
    text = result.stdout.strip().strip('"')
    if not text:
        raise RuntimeError("Claude Code returned no text")
    return text


def write_post(path, photo):
    lines = ["---", f"date: {photo.date}", "images:", f'  - src: "../../assets/photos/{photo.destination.name}"']
    print(f"Generating alt text for {photo.destination.name}...")
    try:
        # JSON strings are valid YAML double-quoted scalars, so quotes and colons are escaped safely.
        lines.append(f"    alt: {json.dumps(alt_text(photo), ensure_ascii=False)}")
    except (OSError, subprocess.CalledProcessError, RuntimeError) as error:
        print(f"WARNING: no alt text for {photo.destination.name} ({error}); add it by hand.", file=sys.stderr)
    lines += ["---", ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote post: {path}")


def main():
    parser = argparse.ArgumentParser(description="Import Lightroom JPG exports into the blog assets and posts.")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path.home() / "Desktop",
        help="Directory to scan for JPG exports (default: ~/Desktop)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files in src/assets/photos without prompting.",
    )
    args = parser.parse_args()

    candidates = parse_candidates(args.source)
    if not candidates:
        print(f"No Lightroom-style JPG exports found in {args.source}")
        return 0

    new = copy_photos(candidates, args.overwrite)
    for photo in new:
        path = POSTS_DIR / f"{photo.destination.stem}.md"
        if path.exists():
            print(f"Skipping {path.name}: post already exists", file=sys.stderr)
            continue
        write_post(path, photo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
