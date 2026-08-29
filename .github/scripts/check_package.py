#!/usr/bin/env python3
"""VPM listing source と repository 内 package を検査する。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PACKAGE_PREFIX = "io.github.sabas0ba.sabaaccessory."
PACKAGE_NAME_RE = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)+$")
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


class ValidationError(ValueError):
    """Repository の検査エラー。"""


def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicates)
    except (OSError, json.JSONDecodeError) as error:
        raise ValidationError(f"{path}: invalid JSON: {error}") from error
    if not isinstance(value, dict):
        raise ValidationError(f"{path}: root must be an object")
    return value


def _require_string(value: dict[str, Any], key: str, context: Path) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item.strip():
        raise ValidationError(f"{context}: {key} must be a non-empty string")
    return item


def validate_manifest(package_dir: Path) -> dict[str, Any]:
    manifest_path = package_dir / "package.json"
    manifest = load_json(manifest_path)

    name = _require_string(manifest, "name", manifest_path)
    if name != package_dir.name:
        raise ValidationError(f"{manifest_path}: name must match its directory")
    if not name.startswith(PACKAGE_PREFIX) or not PACKAGE_NAME_RE.fullmatch(name):
        raise ValidationError(f"{manifest_path}: invalid SabaAccessory package id: {name}")

    _require_string(manifest, "displayName", manifest_path)
    version = _require_string(manifest, "version", manifest_path)
    if not SEMVER_RE.fullmatch(version):
        raise ValidationError(f"{manifest_path}: version is not SemVer 2.0.0: {version}")
    if manifest.get("unity") != "2022.3":
        raise ValidationError(f"{manifest_path}: unity must be 2022.3")
    _require_string(manifest, "description", manifest_path)

    author = manifest.get("author")
    if not isinstance(author, dict):
        raise ValidationError(f"{manifest_path}: author must be an object")
    _require_string(author, "name", manifest_path)
    email = _require_string(author, "email", manifest_path)
    if "@" not in email:
        raise ValidationError(f"{manifest_path}: author.email is invalid")

    if manifest.get("license") != "MIT":
        raise ValidationError(f"{manifest_path}: license must be MIT")
    dependencies = manifest.get("vpmDependencies")
    if not isinstance(dependencies, dict):
        raise ValidationError(f"{manifest_path}: vpmDependencies must be an object")
    if dependencies.get("com.vrchat.avatars") != "3.10.x":
        raise ValidationError(
            f"{manifest_path}: com.vrchat.avatars dependency must be 3.10.x"
        )

    for generated_key in ("url", "zipSHA256"):
        if generated_key in manifest:
            raise ValidationError(
                f"{manifest_path}: {generated_key} belongs in the release manifest"
            )

    required_files = ("README.md", "CHANGELOG.md", "LICENSE.md")
    for filename in required_files:
        if not (package_dir / filename).is_file():
            raise ValidationError(f"{package_dir}: missing {filename}")

    samples = manifest.get("samples", [])
    if not isinstance(samples, list):
        raise ValidationError(f"{manifest_path}: samples must be an array")
    for sample in samples:
        if not isinstance(sample, dict) or not isinstance(sample.get("path"), str):
            raise ValidationError(f"{manifest_path}: invalid sample entry")
        if not (package_dir / sample["path"]).is_dir():
            raise ValidationError(
                f"{manifest_path}: sample path does not exist: {sample['path']}"
            )

    for source_file in package_dir.rglob("*.cs"):
        relative = source_file.relative_to(package_dir)
        if "Editor" in relative.parts:
            continue
        text = source_file.read_text(encoding="utf-8")
        if re.search(r"\b(?:using\s+UnityEditor|UnityEditor\.)", text):
            raise ValidationError(
                f"{source_file}: UnityEditor API must be placed below Editor/"
            )

    return manifest


def validate_repository(source_path: Path, packages_dir: Path) -> list[dict[str, Any]]:
    source = load_json(source_path)
    for key in ("name", "id", "url", "author", "description", "githubRepo"):
        _require_string(source, key, source_path)

    configured = source.get("packages")
    if not isinstance(configured, list) or not all(isinstance(item, str) for item in configured):
        raise ValidationError(f"{source_path}: packages must be an array of strings")
    if configured != sorted(set(configured)):
        raise ValidationError(f"{source_path}: packages must be unique and sorted")

    discovered = sorted(
        path.name
        for path in packages_dir.iterdir()
        if path.is_dir() and path.name.startswith(PACKAGE_PREFIX)
    )
    if configured != discovered:
        raise ValidationError(
            f"{source_path}: packages mismatch; configured={configured}, discovered={discovered}"
        )

    return [validate_manifest(packages_dir / package_name) for package_name in discovered]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--packages", type=Path, required=True)
    args = parser.parse_args()

    try:
        manifests = validate_repository(args.source, args.packages)
    except ValidationError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(f"validated {len(manifests)} package(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

