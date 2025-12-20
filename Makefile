SITE_DIST_DIR := blog/dist
LIGHTROOM_EXPORT_DIR ?= ~/Desktop
PREVIEW_URL ?= http://localhost:8080
PREVIEW_PORT ?= 8080

.PHONY: install build preview clean distclean import format lint check test regen

install:
	uv sync

build: install
	uv run generate-blog

preview: install
	uv run generate-blog --site-url $(PREVIEW_URL) --feed-self-url $(PREVIEW_URL)
	python -m http.server $(PREVIEW_PORT) -d $(SITE_DIST_DIR)

clean:
	rm -rf $(SITE_DIST_DIR)

distclean: clean
	rm -rf .uv .venv

import: install
	uv run python scripts/import_lightroom.py --source $(LIGHTROOM_EXPORT_DIR)

format:
	uv run ruff format

lint:
	uv run ruff check

check: format lint

test: install
	uv run python -m unittest discover -s tests

regen: clean build
