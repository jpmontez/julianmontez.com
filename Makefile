SITE_DIST_DIR := blog/dist
LIGHTROOM_EXPORT_DIR ?= ~/Desktop

.PHONY: install build preview clean distclean import format lint check regen

install:
	uv sync

build: install
	uv run generate-blog

preview: build
	python -m http.server 8080 -d $(SITE_DIST_DIR)

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

regen: clean build
