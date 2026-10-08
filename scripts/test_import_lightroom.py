#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# ///
"""Assert-based self-check for import_lightroom.py. Runs in a temp dir; never touches the repo or calls claude."""

import datetime as dt
import json
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True  # keep scripts/ free of __pycache__
sys.path.insert(0, str(Path(__file__).resolve().parent))
import import_lightroom as il

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    source, il.PHOTOS_DIR, il.POSTS_DIR = tmp / "source", tmp / "photos", tmp / "posts"
    for directory in (source, il.PHOTOS_DIR, il.POSTS_DIR):
        directory.mkdir()
    for name in ("20260516-DSC_0411.JPG", "20261340-DSC_0001.jpg", "notes.txt", "IMG_1.jpg"):
        (source / name).write_bytes(b"jpg")

    # parse_candidates: uppercase extension matches, bad date and non-Lightroom names are skipped.
    [photo] = il.parse_candidates(source)
    assert photo.date == dt.date(2026, 5, 16)
    assert photo.destination == il.PHOTOS_DIR / "2026-05-16-DSC_0411.jpg"

    # copy_photos: a copied photo with no post (interrupted run) is still new on the next run.
    assert il.copy_photos([photo], overwrite=True) == [photo]
    assert il.copy_photos([photo], overwrite=True) == [photo]
    (il.POSTS_DIR / "2026-05-16-DSC_0411.md").write_text(
        'images:\n  - src: "../../assets/photos/2026-05-16-DSC_0411.jpg"\n', encoding="utf-8"
    )
    assert il.copy_photos([photo], overwrite=True) == []

    # write_post: tricky alt text round-trips as a JSON/YAML double-quoted scalar.
    alt = 'He said "hi": café at 5:30'
    il.alt_text = lambda photo: alt
    post = tmp / "post.md"
    il.write_post(post, photo.date, [photo])
    lines = post.read_text(encoding="utf-8").splitlines()
    assert lines[:4] == ["---", "date: 2026-05-16", "images:", '  - src: "../../assets/photos/2026-05-16-DSC_0411.jpg"']
    assert lines[4].startswith("    alt: ") and json.loads(lines[4].removeprefix("    alt: ")) == alt
    assert "café" in lines[4] and lines[5:] == ["---"]

    # write_post: a failing alt_text still writes the post, just without an alt line.
    def fail(photo):
        raise RuntimeError("no claude")

    il.alt_text = fail
    il.write_post(post, photo.date, [photo])
    text = post.read_text(encoding="utf-8")
    assert "alt:" not in text and text.endswith("2026-05-16-DSC_0411.jpg\"\n---\n")

print("OK")
