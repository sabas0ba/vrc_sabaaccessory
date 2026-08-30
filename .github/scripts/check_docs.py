#!/usr/bin/env python3
"""生成した GitHub Pages の内部リンクと基本構造を検査する。"""

from __future__ import annotations

import argparse
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class SiteValidationError(ValueError):
    """公開サイトの構造に不整合がある場合のエラー。"""


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.references: list[str] = []
        self.has_japanese_language = False
        self.has_main = False
        self.has_title = False
        self.has_viewport = False
        self._inside_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        identifier = attributes.get("id")
        if identifier:
            self.ids.add(identifier)
        if tag == "html" and attributes.get("lang") == "ja":
            self.has_japanese_language = True
        if tag == "main":
            self.has_main = True
        if tag == "title":
            self._inside_title = True
        if tag == "meta" and attributes.get("name") == "viewport":
            self.has_viewport = True
        for name in ("href", "src"):
            target = attributes.get(name)
            if target:
                self.references.append(target)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._inside_title = False

    def handle_data(self, data: str) -> None:
        if self._inside_title and data.strip():
            self.has_title = True


def parse_page(path: Path) -> PageParser:
    parser = PageParser()
    parser.feed(path.read_text(encoding="utf-8"))
    parser.close()
    return parser


def _within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def check_site(site: Path) -> list[Path]:
    site = site.resolve()
    pages = sorted(site.rglob("*.html"))
    if not pages:
        raise SiteValidationError("site contains no HTML pages")

    parsed = {page: parse_page(page) for page in pages}
    errors: list[str] = []
    for page, document in parsed.items():
        relative_page = page.relative_to(site)
        if not document.has_japanese_language:
            errors.append(f"{relative_page}: html lang must be ja")
        if not document.has_title:
            errors.append(f"{relative_page}: title is missing")
        if not document.has_viewport:
            errors.append(f"{relative_page}: viewport metadata is missing")
        if not document.has_main:
            errors.append(f"{relative_page}: main element is missing")

        for reference in document.references:
            parts = urlsplit(reference)
            if parts.scheme in {"http", "https", "mailto", "vcc", "data"} or parts.netloc:
                continue
            target_path = unquote(parts.path)
            target = page if not target_path else (page.parent / target_path).resolve()
            if not _within(target, site):
                errors.append(f"{relative_page}: reference leaves site: {reference}")
                continue
            if not target.exists():
                errors.append(f"{relative_page}: missing reference: {reference}")
                continue
            if parts.fragment and target.suffix.lower() == ".html":
                target_document = parsed.get(target)
                if target_document is None:
                    target_document = parse_page(target)
                if parts.fragment not in target_document.ids:
                    errors.append(f"{relative_page}: missing anchor: {reference}")

    if errors:
        raise SiteValidationError("\n".join(errors))
    return pages


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", type=Path, default=Path("Website"))
    args = parser.parse_args()
    try:
        pages = check_site(args.site)
    except (OSError, SiteValidationError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"validated {len(pages)} page(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
