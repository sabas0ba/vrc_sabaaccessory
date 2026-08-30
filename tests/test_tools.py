from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".github" / "scripts"
WORK = ROOT / ".work"
WORK.mkdir(exist_ok=True)
sys.path.insert(0, str(SCRIPTS))

from build_docs import (  # noqa: E402
    DocumentationError,
    Rewriter,
    build as build_docs,
    render_markdown,
)
from build_manifest import build_manifest  # noqa: E402
from build_listing import build_listing, semver_key  # noqa: E402
from build_package import build_package  # noqa: E402
from check_docs import check_site  # noqa: E402
from check_package import validate_repository  # noqa: E402


class ToolTests(unittest.TestCase):
    def make_repository(self, root: Path) -> Path:
        package_name = "io.github.sabas0ba.sabaaccessory.example"
        package_dir = root / "Packages" / package_name
        package_dir.mkdir(parents=True)
        manifest = {
            "name": package_name,
            "displayName": "SabaAccessory Example",
            "version": "0.1.0",
            "unity": "2022.3",
            "description": "Test package",
            "author": {
                "name": "sabas0ba",
                "email": "sabas0ba@outlook.com",
            },
            "license": "Apache-2.0",
            "vpmDependencies": {"com.vrchat.avatars": "3.10.x"},
        }
        (package_dir / "package.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        for filename in ("README.md", "CHANGELOG.md", "LICENSE.md"):
            (package_dir / filename).write_text(filename + "\n", encoding="utf-8")
        source = {
            "name": "SabaAccessory",
            "id": "io.github.sabas0ba.sabaaccessory",
            "url": "https://example.invalid/index.json",
            "author": "sabas0ba",
            "description": "test",
            "githubRepo": "sabas0ba/vrc_sabaaccessory",
            "packages": [package_name],
        }
        (root / "source.json").write_text(json.dumps(source), encoding="utf-8")
        return package_dir

    def test_repository_validation(self) -> None:
        with tempfile.TemporaryDirectory(dir=WORK) as temporary:
            root = Path(temporary)
            self.make_repository(root)
            manifests = validate_repository(root / "source.json", root / "Packages")
            self.assertEqual(len(manifests), 1)

    def test_empty_listing_requires_no_releases(self) -> None:
        source = {
            "name": "SabaAccessory",
            "id": "io.github.sabas0ba.sabaaccessory",
            "url": "https://example.invalid/index.json",
            "author": "sabas0ba",
            "description": "test",
            "githubRepo": "sabas0ba/vrc_sabaaccessory",
            "packages": [],
        }
        listing = build_listing(source, [], "")
        self.assertEqual(listing["packages"], {})
        self.assertNotIn("githubRepo", listing)

    def test_semver_order_uses_precedence(self) -> None:
        versions = [
            "0.9.0",
            "0.10.0",
            "1.0.0-alpha",
            "1.0.0-alpha.2",
            "1.0.0-alpha.10",
            "1.0.0",
            "1.0.0+build.2",
        ]
        ordered = sorted(versions, key=semver_key, reverse=True)
        self.assertIn(ordered[0], {"1.0.0", "1.0.0+build.2"})
        self.assertLess(ordered.index("0.10.0"), ordered.index("0.9.0"))
        self.assertLess(ordered.index("1.0.0-alpha.10"), ordered.index("1.0.0-alpha.2"))
        self.assertLess(ordered.index("1.0.0-alpha.2"), ordered.index("1.0.0-alpha"))

    def test_package_archive_is_reproducible(self) -> None:
        with tempfile.TemporaryDirectory(dir=WORK) as temporary:
            root = Path(temporary)
            package_dir = self.make_repository(root)
            first = root / "first.zip"
            second = root / "second.zip"
            first_hash = build_package(package_dir, first)
            second_hash = build_package(package_dir, second)
            self.assertEqual(first_hash, second_hash)
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_release_manifest_contains_archive_hash(self) -> None:
        with tempfile.TemporaryDirectory(dir=WORK) as temporary:
            root = Path(temporary)
            package_dir = self.make_repository(root)
            archive = root / "package.zip"
            output = root / "manifest.json"
            build_package(package_dir, archive)
            build_manifest(
                package_dir,
                archive,
                "https://example.invalid/package.zip",
                output,
            )
            manifest = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(
                manifest["zipSHA256"], hashlib.sha256(archive.read_bytes()).hexdigest()
            )

    def test_markdown_renderer_escapes_html(self) -> None:
        identity = Rewriter(link=lambda target: target, image=lambda target: target)
        document = render_markdown(
            "# Guide\n\n<script>alert(1)</script> and **bold** and `code`\n",
            identity,
        )
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", document.body)
        self.assertIn("<strong>bold</strong>", document.body)
        self.assertIn("<code>code</code>", document.body)
        self.assertNotIn("<script>alert(1)</script>", document.body)

    def test_markdown_renderer_rejects_unclosed_code_block(self) -> None:
        identity = Rewriter(link=lambda target: target, image=lambda target: target)
        with self.assertRaises(DocumentationError):
            render_markdown("# Guide\n\n```text\nunclosed\n", identity)

    def test_repository_documentation_site(self) -> None:
        with tempfile.TemporaryDirectory(dir=WORK) as temporary:
            site = Path(temporary) / "site"
            shutil.copytree(ROOT / "Website", site)
            (site / "index.json").write_text("{}\n", encoding="utf-8")
            written = build_docs(ROOT, site / "docs")
            pages = check_site(site)
            self.assertEqual(len(written), 3)
            self.assertEqual(len(pages), 4)
            guide = site / "docs" / "io.github.sabas0ba.sabaaccessory.digital-halo" / "index.html"
            guide_html = guide.read_text(encoding="utf-8")
            self.assertIn("Digital Halo / Geometry Block Effect 使用ガイド", guide_html)
            self.assertIn("digital-halo-shapes-oblique.png", guide_html)
            self.assertTrue((guide.parent / "images" / "digital-halo-shapes-oblique.png").is_file())


if __name__ == "__main__":
    unittest.main()
