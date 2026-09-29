#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# ///
"""Import Lightroom JPG exports into the blog assets and scaffold posts with alt text from Claude Code."""

import argparse
import datetime as dt
import itertools
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

# Lightroom export format: YYYYMMDD-DSC_NNNN.jpg
SOURCE_PATTERN = re.compile(r"^(?P<date>\d{8})-DSC_(?P<num>\d{4,})\.jpg$", re.IGNORECASE)

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
        photos.append(Photo(path, date, PHOTOS_DIR / f"{date}-DSC_{match['num']}.jpg"))
    return photos


def copy_photos(photos, overwrite):
    """Copy every photo; return only the new ones. An overwritten photo keeps its existing post."""
    new = []
    for photo in photos:
        exists = photo.destination.exists()
        if exists and not overwrite:
            reply = input(f"{photo.destination.name} already exists. Overwrite with {photo.source.name}? [y/N]: ")
            if reply.strip().lower() not in {"y", "yes"}:
                print(f"Skipping {photo.destination.name} (exists)")
                continue
        shutil.copy2(photo.source, photo.destination)
        print(f"Copied {photo.source} -> {photo.destination}")
        if not exists:
            new.append(photo)
    return new


def prompt_slug(date, default):
    while True:
        name = input(f"Multiple images on {date}. Enter a custom name (default: {default}): ").strip()
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", name).strip("-").lower() if name else default
        if slug:
            return slug if slug.startswith(str(date)) else f"{date}-{slug}"
        print("Slug cannot be empty.")


def choose_post_path(date, photos):
    slug = photos[0].destination.stem if len(photos) == 1 else prompt_slug(date, f"{date}-photos")
    while (path := POSTS_DIR / f"{slug}.md").exists():
        print(f"{path} already exists. Enter another name.")
        slug = prompt_slug(date, slug)
    return path


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


def write_post(path, date, photos):
    lines = ["---", f"date: {date}", "images:"]
    for photo in photos:
        lines.append(f'  - src: "../../assets/photos/{photo.destination.name}"')
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
    # Candidates are sorted by filename (YYYYMMDD-DSC_NNNN), so same-day photos are adjacent and in order.
    for date, group in itertools.groupby(new, key=lambda photo: photo.date):
        photos = list(group)
        write_post(choose_post_path(date, photos), date, photos)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
