#!/usr/bin/env python3
"""リポジトリ内の Markdown を GitHub Pages 用の静的 HTML に変換する。"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable
from urllib.parse import urlsplit


PACKAGE_PREFIX = "io.github.sabas0ba.sabaaccessory."
REPOSITORY_URL = "https://github.com/sabas0ba/vrc_sabaaccessory"

_CODE = re.compile(r"`([^`]+)`")
_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")


class DocumentationError(ValueError):
    """公開用ドキュメントを生成できない場合のエラー。"""


@dataclass(frozen=True)
class Heading:
    level: int
    text: str
    anchor: str


@dataclass(frozen=True)
class Document:
    title: str
    body: str
    headings: list[Heading] = field(default_factory=list)


@dataclass(frozen=True)
class Rewriter:
    link: Callable[[str], str]
    image: Callable[[str], str]


@dataclass(frozen=True)
class PackageDocumentation:
    package_id: str
    display_name: str
    description: str
    guide: Path
    changelog: Path


def slugify(value: str, used: set[str]) -> str:
    slug = re.sub(r"[^\w\- ]+", "", value, flags=re.UNICODE).strip().lower()
    slug = re.sub(r"[\s_]+", "-", slug) or "section"
    candidate = slug
    suffix = 2
    while candidate in used:
        candidate = f"{slug}-{suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


def _safe_target(target: str) -> str:
    scheme = urlsplit(target).scheme.lower()
    if scheme and scheme not in {"http", "https", "mailto"}:
        raise DocumentationError(f"unsupported link scheme: {target}")
    return target


def render_inline(value: str, rewriter: Rewriter) -> str:
    placeholders: list[str] = []

    def stash(markup: str) -> str:
        placeholders.append(markup)
        return f"\x00{len(placeholders) - 1}\x00"

    def code(match: re.Match[str]) -> str:
        return stash(f"<code>{html.escape(match.group(1))}</code>")

    value = _CODE.sub(code, value)

    def image(match: re.Match[str]) -> str:
        alt, target = match.group(1), rewriter.image(match.group(2))
        return stash(
            f'<img src="{html.escape(target, quote=True)}" '
            f'alt="{html.escape(alt, quote=True)}" loading="lazy">'
        )

    value = _IMAGE.sub(image, value)

    def link(match: re.Match[str]) -> str:
        label, target = match.group(1), rewriter.link(match.group(2))
        return stash(
            f'<a href="{html.escape(target, quote=True)}">'
            f"{render_inline(label, rewriter)}</a>"
        )

    value = _LINK.sub(link, value)
    value = html.escape(value)
    value = _BOLD.sub(lambda match: f"<strong>{match.group(1)}</strong>", value)

    for index, markup in enumerate(placeholders):
        value = value.replace(f"\x00{index}\x00", markup)
    return value


def _is_table_rule(value: str) -> bool:
    return bool(re.fullmatch(r"\|(?:\s*:?-{2,}:?\s*\|)+", value.strip()))


def _split_table_row(value: str) -> list[str]:
    return [cell.strip() for cell in value.strip().strip("|").split("|")]


def _render_table(header: list[str], rows: list[list[str]], rewriter: Rewriter) -> str:
    if any(len(row) != len(header) for row in rows):
        raise DocumentationError("table rows must have the same number of cells")
    head = "".join(f"<th>{render_inline(cell, rewriter)}</th>" for cell in header)
    body = "".join(
        "<tr>"
        + "".join(f"<td>{render_inline(cell, rewriter)}</td>" for cell in row)
        + "</tr>"
        for row in rows
    )
    return (
        '<div class="table-scroll"><table><thead><tr>'
        f"{head}</tr></thead><tbody>{body}</tbody></table></div>"
    )


def render_markdown(source: str, rewriter: Rewriter) -> Document:
    lines = source.replace("\r\n", "\n").split("\n")
    output: list[str] = []
    headings: list[Heading] = []
    anchors: set[str] = set()
    paragraph: list[str] = []
    title = ""
    index = 0

    def close_paragraph() -> None:
        if paragraph:
            output.append("<p>" + " ".join(paragraph) + "</p>")
            paragraph.clear()

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if stripped.startswith("```"):
            close_paragraph()
            language = stripped[3:].strip()
            code_lines: list[str] = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            if index == len(lines):
                raise DocumentationError("unclosed fenced code block")
            klass = f' class="language-{html.escape(language, quote=True)}"' if language else ""
            output.append(
                f"<pre><code{klass}>{html.escape(chr(10).join(code_lines))}</code></pre>"
            )
            index += 1
            continue

        if not stripped:
            close_paragraph()
            index += 1
            continue

        heading_match = re.match(r"(#{1,6})\s+(.*)$", stripped)
        if heading_match:
            close_paragraph()
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()
            anchor = slugify(re.sub(r"`", "", heading_text), anchors)
            if level == 1 and not title:
                title = re.sub(r"`", "", heading_text)
            headings.append(Heading(level, heading_text, anchor))
            output.append(
                f'<h{level} id="{html.escape(anchor, quote=True)}">'
                f"{render_inline(heading_text, rewriter)}</h{level}>"
            )
            index += 1
            continue

        if stripped.startswith("|") and index + 1 < len(lines) and _is_table_rule(lines[index + 1]):
            close_paragraph()
            header = _split_table_row(stripped)
            rows: list[list[str]] = []
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                rows.append(_split_table_row(lines[index]))
                index += 1
            output.append(_render_table(header, rows, rewriter))
            continue

        list_match = re.match(r"(?:[-*+]\s+|\d+\.\s+)(.*)$", stripped)
        if list_match:
            close_paragraph()
            ordered = bool(re.match(r"\d+\.\s+", stripped))
            items: list[str] = []
            while index < len(lines):
                candidate = lines[index].strip()
                pattern = r"\d+\.\s+(.*)$" if ordered else r"[-*+]\s+(.*)$"
                item_match = re.match(pattern, candidate)
                if not item_match:
                    break
                items.append(render_inline(item_match.group(1), rewriter))
                index += 1
            tag = "ol" if ordered else "ul"
            output.append(f"<{tag}>" + "".join(f"<li>{item}</li>" for item in items) + f"</{tag}>")
            continue

        if stripped.startswith(">"):
            close_paragraph()
            quote_lines: list[str] = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                quote_lines.append(lines[index].strip()[1:].strip())
                index += 1
            output.append(
                "<blockquote><p>"
                + " ".join(render_inline(value, rewriter) for value in quote_lines)
                + "</p></blockquote>"
            )
            continue

        if _IMAGE.fullmatch(stripped):
            close_paragraph()
            output.append(f"<figure>{render_inline(stripped, rewriter)}</figure>")
            index += 1
            continue

        paragraph.append(render_inline(stripped, rewriter))
        index += 1

    close_paragraph()
    if not title:
        raise DocumentationError("document must have a level-one heading")
    return Document(title=title, body="\n".join(output), headings=headings)


def discover_packages(repository: Path) -> list[PackageDocumentation]:
    source_path = repository / "source.json"
    source = json.loads(source_path.read_text(encoding="utf-8"))
    package_ids = source.get("packages")
    if not isinstance(package_ids, list) or not all(isinstance(item, str) for item in package_ids):
        raise DocumentationError("source packages must be an array of strings")

    packages: list[PackageDocumentation] = []
    for package_id in package_ids:
        if not package_id.startswith(PACKAGE_PREFIX):
            raise DocumentationError(f"unsupported package id: {package_id}")
        package_dir = repository / "Packages" / package_id
        manifest_path = package_dir / "package.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        guide_name = package_id.removeprefix(PACKAGE_PREFIX) + ".md"
        guide = repository / "docs" / guide_name
        changelog = package_dir / "CHANGELOG.md"
        for required in (guide, changelog):
            if not required.is_file():
                raise DocumentationError(f"missing documentation source: {required}")
        packages.append(
            PackageDocumentation(
                package_id=package_id,
                display_name=str(manifest.get("displayName", package_id)),
                description=str(manifest.get("description", "")),
                guide=guide,
                changelog=changelog,
            )
        )
    return packages


def _within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def make_rewriter(source: Path, repository: Path, page_output: Path) -> Rewriter:
    docs_root = (repository / "docs").resolve()

    def rewrite_link(target: str) -> str:
        target = _safe_target(target)
        if target.startswith(("http://", "https://", "mailto:", "#")):
            return target
        resolved = (source.parent / target.split("#", 1)[0]).resolve()
        if not _within(resolved, repository.resolve()):
            raise DocumentationError(f"link leaves repository: {target}")
        return f"{REPOSITORY_URL}/blob/main/{resolved.relative_to(repository.resolve()).as_posix()}"

    def rewrite_image(target: str) -> str:
        target = _safe_target(target)
        if target.startswith(("http://", "https://")):
            raise DocumentationError(f"external images are not published: {target}")
        source_image = (source.parent / target).resolve()
        if not _within(source_image, docs_root):
            raise DocumentationError(f"image leaves docs directory: {target}")
        if not source_image.is_file():
            raise DocumentationError(f"missing image: {target}")
        relative = source_image.relative_to(source.parent.resolve())
        destination = page_output.parent / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_image, destination)
        return relative.as_posix()

    return Rewriter(link=rewrite_link, image=rewrite_image)


def _theme_bootstrap() -> str:
    return """<script>
(function () {
  try {
    var saved = localStorage.getItem('sabaaccessory-theme');
    if (saved === 'light' || saved === 'dark') document.documentElement.setAttribute('data-theme', saved);
  } catch (error) {}
})();
</script>"""


def render_page(title: str, body: str, root: str, current: str) -> str:
    items = [
        (f"{root}index.html", "トップ", "home"),
        (f"{root}docs/index.html", "ドキュメント", "docs"),
        (REPOSITORY_URL, "GitHub", "github"),
    ]
    nav = "".join(
        f'<strong aria-current="page">{label}</strong>'
        if key == current
        else f'<a href="{html.escape(href, quote=True)}">{label}</a>'
        for href, label, key in items
    )
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#f3f5f9" media="(prefers-color-scheme: light)" data-color="#f3f5f9">
<meta name="theme-color" content="#0d1118" media="(prefers-color-scheme: dark)" data-color="#0d1118">
<title>{html.escape(title)}</title>
{_theme_bootstrap()}
<link rel="stylesheet" href="{root}assets/site.css">
<script src="{root}assets/site.js" defer></script>
</head>
<body>
<a class="skip-link" href="#content">本文へ移動</a>
<div class="site-shell">
<header class="site-header docs-header">
  <a class="brand" href="{root}index.html"><span class="brand-mark" aria-hidden="true"></span><span>SabaAccessory</span></a>
  <nav class="site-nav" aria-label="サイト内ナビゲーション">{nav}</nav>
  <button class="theme-toggle" id="theme-toggle" type="button" hidden aria-pressed="false">
    <span class="theme-icon theme-icon-light" aria-hidden="true"></span>
    <span class="theme-icon theme-icon-dark" aria-hidden="true"></span>
    <span>テーマ</span>
  </button>
</header>
{body}
<footer class="site-footer">
  <p>SabaAccessory</p>
  <nav aria-label="フッターナビゲーション"><a href="{root}index.json">index.json</a><a href="{REPOSITORY_URL}">GitHub</a></nav>
</footer>
</div>
</body>
</html>
"""


def render_toc(document: Document) -> str:
    items = "".join(
        f'<li class="level-{heading.level}"><a href="#{html.escape(heading.anchor, quote=True)}">'
        f"{render_inline(heading.text, Rewriter(link=_safe_target, image=_safe_target))}</a></li>"
        for heading in document.headings
        if heading.level in {2, 3}
    )
    return f'<aside class="doc-toc" aria-label="目次"><p>目次</p><ol>{items}</ol></aside>'


def _write_document(
    package: PackageDocumentation,
    source: Path,
    output: Path,
    repository: Path,
    label: str,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    rewriter = make_rewriter(source, repository, output)
    document = render_markdown(source.read_text(encoding="utf-8"), rewriter)
    source_url = f"{REPOSITORY_URL}/blob/main/{source.relative_to(repository).as_posix()}"
    actions = (
        '<div class="doc-actions">'
        f'<a href="{html.escape(source_url, quote=True)}">Markdown を GitHub で表示</a>'
        '<a href="changelog.html">変更履歴</a>'
        '<a href="../index.html">ドキュメント一覧</a>'
        "</div>"
    )
    if output.name == "changelog.html":
        actions = (
            '<div class="doc-actions">'
            f'<a href="{html.escape(source_url, quote=True)}">Markdown を GitHub で表示</a>'
            '<a href="index.html">使用ガイド</a>'
            '<a href="../index.html">ドキュメント一覧</a>'
            "</div>"
        )
    body = (
        '<main class="docs-main" id="content">'
        '<div class="doc-layout">'
        f'<article class="doc-article" aria-label="{html.escape(label, quote=True)}">'
        f"{document.body}{actions}</article>{render_toc(document)}"
        "</div></main>"
    )
    output.write_text(
        render_page(f"{document.title} | SabaAccessory", body, "../../", "docs"),
        encoding="utf-8",
        newline="\n",
    )


def _write_index(packages: list[PackageDocumentation], output: Path) -> None:
    cards = "".join(
        '<a class="doc-card" href="'
        + html.escape(f"{package.package_id}/index.html", quote=True)
        + '">'
        + f"<h2>{html.escape(package.display_name)}</h2>"
        + f'<span class="doc-card-id">{html.escape(package.package_id)}</span>'
        + f"<p>{html.escape(package.description)}</p>"
        + '<span class="doc-card-action">使用ガイドを開く</span></a>'
        for package in packages
    )
    body = f"""<main class="docs-main" id="content">
<section class="docs-intro">
  <p class="section-label">Documentation</p>
  <h1>ツールと package の使用ガイド</h1>
  <p>導入手順、設定項目、Demo Scene、対応環境と制約を package ごとに掲載しています。</p>
</section>
<section class="docs-grid" aria-label="パッケージ別ドキュメント">{cards}</section>
</main>"""
    output.mkdir(parents=True, exist_ok=True)
    (output / "index.html").write_text(
        render_page("ドキュメント | SabaAccessory", body, "../", "docs"),
        encoding="utf-8",
        newline="\n",
    )


def build(repository: Path, output: Path) -> list[Path]:
    repository = repository.resolve()
    output = output.resolve()
    generated_roots = ((repository / "Website").resolve(), (repository / ".work").resolve())
    if not any(_within(output, root) for root in generated_roots) or output in generated_roots:
        raise DocumentationError("output must be below Website or .work")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    packages = discover_packages(repository)
    _write_index(packages, output)
    written = [output / "index.html"]
    for package in packages:
        package_output = output / package.package_id
        guide_output = package_output / "index.html"
        changelog_output = package_output / "changelog.html"
        _write_document(package, package.guide, guide_output, repository, "使用ガイド")
        _write_document(package, package.changelog, changelog_output, repository, "変更履歴")
        written.extend((guide_output, changelog_output))
    return written


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=Path("Website/docs"))
    args = parser.parse_args()
    repository = args.repository.resolve()
    output = args.output if args.output.is_absolute() else repository / args.output
    try:
        written = build(repository, output)
    except (DocumentationError, json.JSONDecodeError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    for path in written:
        print(f"wrote {path.relative_to(repository)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
