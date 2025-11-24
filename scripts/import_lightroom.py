#!/usr/bin/env python3
"""Import Lightroom JPG exports from the Desktop into the blog assets and scaffold posts."""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DESKTOP = Path.home() / "Desktop"
STATIC_DIR = ROOT / "blog" / "static"
POSTS_DIR = ROOT / "blog" / "posts"
LOGGER = logging.getLogger("import_lightroom")

# Lightroom export format: YYYMMDD-DSC_NNNN.jpg (per the request; assume 8-digit date)
SOURCE_PATTERN = re.compile(r"^(?P<date>\d{8})-DSC_(?P<num>\d{4,})\.jpg$", re.IGNORECASE)


@dataclass
class Photo:
    source: Path
    date: dt.date
    number: str
    destination: Path


def parse_candidates(source_dir: Path) -> list[Photo]:
    photos: list[Photo] = []
    for path in sorted(source_dir.iterdir()):
        if not path.is_file():
            continue
        match = SOURCE_PATTERN.match(path.name)
        if not match:
            continue

        raw_date = match.group("date")
        number = match.group("num")
        try:
            date = dt.datetime.strptime(raw_date, "%Y%m%d").date()
        except ValueError:
            LOGGER.warning("Skipping %s: invalid date %s", path.name, raw_date)
            continue

        dest_name = f"{date:%Y-%m-%d}-DSC_{number}{path.suffix.lower()}"
        photos.append(Photo(path, date, number, STATIC_DIR / dest_name))
    return photos


def prompt_overwrite(photo: Photo) -> bool:
    prompt = f"{photo.destination.name} already exists. Overwrite with {photo.source.name}? [y/N]: "
    reply = input(prompt).strip().lower()
    return reply in {"y", "yes"}


def copy_photos(photos: Iterable[Photo], overwrite: bool) -> list[Photo]:
    imported: list[Photo] = []
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

    for photo in photos:
        if photo.destination.exists():
            if overwrite or prompt_overwrite(photo):
                LOGGER.info("Overwriting %s with %s", photo.destination.name, photo.source.name)
            else:
                LOGGER.info("Skipping %s (exists)", photo.destination.name)
                continue
        shutil.copy2(photo.source, photo.destination)
        imported.append(photo)
        LOGGER.info("Copied %s -> %s", photo.source, photo.destination)
    return imported


def sanitize_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-").lower()
    return slug


def prompt_slug(date: dt.date, default_slug: str) -> str:
    prompt = f"Multiple images on {date:%Y-%m-%d}. Enter a custom name (default: {default_slug}): "
    while True:
        user_input = input(prompt).strip()
        slug = sanitize_slug(user_input) if user_input else default_slug
        if not slug:
            print("Slug cannot be empty.")
            continue
        if not slug.startswith(f"{date:%Y-%m-%d}"):
            slug = f"{date:%Y-%m-%d}-{slug}"
        return slug


def ensure_post_path(date: dt.date, slug: str) -> Path:
    year_dir = POSTS_DIR / f"{date.year:04d}"
    month_dir = year_dir / f"{date.month:02d}"
    month_dir.mkdir(parents=True, exist_ok=True)
    return month_dir / f"{slug}.md"


def choose_slug(date: dt.date, photos: list[Photo]) -> tuple[str, Path]:
    if len(photos) == 1:
        base_slug = photos[0].destination.stem
    else:
        default = f"{date:%Y-%m-%d}-photos"
        base_slug = prompt_slug(date, default)

    while True:
        post_path = ensure_post_path(date, base_slug)
        if not post_path.exists():
            return base_slug, post_path
        print(f"{post_path} already exists. Enter another name.")
        base_slug = prompt_slug(date, base_slug)


def write_post(post_path: Path, date: dt.date, photos: list[Photo]) -> None:
    images_lines = [f'  "static/{p.destination.name}",' for p in photos]
    content_lines = [
        "++++",
        f"date = {date:%Y-%m-%d}",
        "images = [",
        *images_lines,
        "]",
        'layout = "photo"',
        "++++",
        "",
    ]
    post_path.write_text("\n".join(content_lines), encoding="utf-8")
    LOGGER.info("Wrote post: %s", post_path)


def create_posts(imported: list[Photo]) -> None:
    if not imported:
        LOGGER.info("No new photos imported; skipping post creation.")
        return

    grouped: dict[dt.date, list[Photo]] = {}
    for photo in imported:
        grouped.setdefault(photo.date, []).append(photo)

    for photos in grouped.values():
        photos.sort(key=lambda p: p.number)

    for date, photos in grouped.items():
        slug, post_path = choose_slug(date, photos)
        write_post(post_path, date, photos)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import Lightroom JPG exports from ~/Desktop into the blog assets/posts."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_DESKTOP,
        help="Directory to scan for JPG exports (default: ~/Desktop)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files in blog/static without prompting.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR). Default: INFO",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(levelname)s %(message)s",
    )

    source_dir = args.source.expanduser()
    if not source_dir.exists():
        print(f"Source directory {source_dir} does not exist.", file=sys.stderr)
        return 1

    candidates = parse_candidates(source_dir)
    if not candidates:
        LOGGER.info("No Lightroom-style JPG exports found in %s", source_dir)
        return 0

    imported = copy_photos(candidates, overwrite=args.overwrite)
    create_posts(imported)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
