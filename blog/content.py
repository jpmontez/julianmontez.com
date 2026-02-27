from __future__ import annotations

import datetime as dt
from pathlib import Path

import tomllib

from blog.models import Post

try:  # Prefer the markdown package but keep a basic fallback.
    import markdown  # type: ignore
except Exception:  # pragma: no cover - fallback is intentionally simple.
    markdown = None


def render_markdown(text: str) -> str:
    if markdown is None:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        return "".join(f"<p>{p}</p>" for p in paragraphs)
    return markdown.markdown(text, extensions=["extra"])


def parse_front_matter(raw: str) -> tuple[dict, str]:
    lines = raw.splitlines()
    if not lines:
        raise ValueError("Empty post")

    delimiter = lines[0].strip()
    if delimiter not in ("+++", "++++"):
        raise ValueError("Front matter must start with +++ or ++++")

    try:
        end_idx = next(i for i, line in enumerate(lines[1:], start=1) if line.strip() == delimiter)
    except StopIteration as exc:  # pragma: no cover - guardrail
        raise ValueError(f"Front matter closing {delimiter} not found") from exc

    front = "\n".join(lines[1:end_idx])
    body = "\n".join(lines[end_idx + 1 :]).lstrip()
    data = tomllib.loads(front)
    return data, body


def parse_images(meta: dict, source: Path) -> tuple[list[str], list[str | None]]:
    raw = meta.get("images", [])
    if raw is None:
        return [], []
    if not isinstance(raw, list):
        raise ValueError(f"Invalid images field in {source}: expected a list")

    images: list[str] = []
    image_alts: list[str | None] = []

    for idx, item in enumerate(raw):
        if isinstance(item, str):
            images.append(item)
            image_alts.append(None)
            continue

        if isinstance(item, dict):
            src = item.get("src") or item.get("path")
            if not src:
                raise ValueError(f"Invalid images[{idx}] in {source}: missing src")
            images.append(str(src))

            alt = item.get("alt")
            image_alts.append(None if alt is None else str(alt))
            continue

        raise ValueError(f"Invalid images[{idx}] in {source}: expected string or table")

    return images, image_alts


def _parse_coordinate(
    value: object,
    *,
    source: Path,
    field_name: str,
    min_value: float,
    max_value: float,
) -> float:
    try:
        coordinate = float(value)  # type: ignore[arg-type]
    except Exception as exc:
        raise ValueError(f"Invalid {field_name} in {source}: expected a number") from exc

    if coordinate < min_value or coordinate > max_value:
        raise ValueError(
            f"Invalid {field_name} in {source}: expected {min_value} <= value <= {max_value}"
        )
    return coordinate


def parse_location(meta: dict, source: Path) -> tuple[str | None, float | None, float | None]:
    raw = meta.get("location")
    if raw is None:
        return None, None, None

    if isinstance(raw, str):
        name = raw.strip()
        return (name if name else None), None, None

    if not isinstance(raw, dict):
        raise ValueError(f"Invalid location field in {source}: expected a string or table")

    raw_name = raw.get("name")
    name = None if raw_name is None else str(raw_name).strip()
    latitude_raw = raw.get("lat", raw.get("latitude"))
    longitude_raw = raw.get("lon", raw.get("lng", raw.get("longitude")))

    if (latitude_raw is None) != (longitude_raw is None):
        raise ValueError(f"Invalid location in {source}: latitude/longitude must be provided together")

    latitude = (
        _parse_coordinate(
            latitude_raw,
            source=source,
            field_name="location latitude",
            min_value=-90.0,
            max_value=90.0,
        )
        if latitude_raw is not None
        else None
    )
    longitude = (
        _parse_coordinate(
            longitude_raw,
            source=source,
            field_name="location longitude",
            min_value=-180.0,
            max_value=180.0,
        )
        if longitude_raw is not None
        else None
    )

    return (name if name else None), latitude, longitude


def parse_post(path: Path) -> Post:
    raw = path.read_text(encoding="utf-8")
    meta, body_md = parse_front_matter(raw)

    try:
        date = dt.date.fromisoformat(str(meta["date"]))
    except Exception as exc:  # pragma: no cover - strict input validation
        raise ValueError(f"Invalid or missing date in {path}") from exc

    title = meta.get("title")
    images, image_alts = parse_images(meta, path)
    location_name, location_latitude, location_longitude = parse_location(meta, path)
    excerpt = meta.get("excerpt")
    layout = meta.get("layout", "photo")
    slug = path.stem

    body_html = render_markdown(body_md) if body_md.strip() else ""
    display_date = date.strftime("%d %b %Y")
    url = f"{date.year}/{date.month:02d}/{slug}/"

    return Post(
        source=path,
        title=None if title is None else str(title),
        date=date,
        images=images,
        image_alts=image_alts,
        excerpt=None if excerpt is None else str(excerpt),
        layout=str(layout),
        body_html=body_html,
        display_date=display_date,
        url=url,
        slug=slug,
        location_name=location_name,
        location_latitude=location_latitude,
        location_longitude=location_longitude,
    )


def collect_posts(posts_dir: Path) -> list[Post]:
    posts: list[Post] = []
    for md in sorted(posts_dir.glob("**/*.md")):
        posts.append(parse_post(md))
    posts.sort(key=lambda p: p.date, reverse=True)
    return posts
