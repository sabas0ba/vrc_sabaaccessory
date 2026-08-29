#!/usr/bin/env python3
"""GitHub Releases から VPM repository listing を生成する。"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from check_package import ValidationError, load_json


def request_json(url: str, token: str) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "sabaaccessory-listing-builder",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def fetch_releases(repository: str, token: str) -> list[dict[str, Any]]:
    releases: list[dict[str, Any]] = []
    for page in range(1, 101):
        value = request_json(
            f"https://api.github.com/repos/{repository}/releases?per_page=100&page={page}",
            token,
        )
        if not isinstance(value, list):
            raise ValidationError("GitHub Releases API returned a non-array response")
        releases.extend(item for item in value if isinstance(item, dict))
        if len(value) < 100:
            return releases
    raise ValidationError("GitHub Releases pagination exceeded 100 pages")


def build_listing(source: dict[str, Any], releases: list[dict[str, Any]], token: str) -> dict[str, Any]:
    configured = source.get("packages")
    if not isinstance(configured, list) or not all(isinstance(item, str) for item in configured):
        raise ValidationError("source packages must be an array of strings")
    configured_set = set(configured)
    versions: dict[str, dict[str, dict[str, Any]]] = {
        package_name: {} for package_name in configured
    }

    for release in releases:
        if release.get("draft"):
            continue
        assets = release.get("assets", [])
        if not isinstance(assets, list):
            continue
        for asset in assets:
            if not isinstance(asset, dict) or not str(asset.get("name", "")).endswith(".json"):
                continue
            url = asset.get("browser_download_url")
            if not isinstance(url, str):
                continue
            manifest = request_json(url, token)
            if not isinstance(manifest, dict):
                raise ValidationError(f"release manifest is not an object: {url}")
            package_name = manifest.get("name")
            version = manifest.get("version")
            if package_name not in configured_set:
                continue
            if not isinstance(version, str) or not version:
                raise ValidationError(f"release manifest has no version: {url}")
            if not isinstance(manifest.get("url"), str) or not isinstance(
                manifest.get("zipSHA256"), str
            ):
                raise ValidationError(f"release manifest lacks url or zipSHA256: {url}")
            if version in versions[package_name]:
                raise ValidationError(f"duplicate release: {package_name} {version}")
            versions[package_name][version] = manifest

    packages: dict[str, Any] = {}
    for package_name in configured:
        package_versions = versions[package_name]
        if not package_versions:
            print(f"warning: no release found for {package_name}", file=sys.stderr)
            continue
        packages[package_name] = {
            "versions": {
                version: package_versions[version]
                for version in sorted(package_versions, reverse=True)
            }
        }

    listing = {
        key: value
        for key, value in source.items()
        if key not in {"githubRepo", "packages"}
    }
    listing["packages"] = packages
    return listing


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        source = load_json(args.source)
        repository = source.get("githubRepo")
        if not isinstance(repository, str) or not repository:
            raise ValidationError("source githubRepo must be a non-empty string")
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN", "")
        configured = source.get("packages", [])
        releases = fetch_releases(repository, token) if configured else []
        listing = build_listing(source, releases, token)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(listing, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except (HTTPError, OSError, URLError, ValidationError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

