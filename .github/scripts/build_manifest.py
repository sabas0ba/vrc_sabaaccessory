#!/usr/bin/env python3
"""package.json から listing 収録用 manifest を生成する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

from check_package import ValidationError, validate_manifest


def build_manifest(package_dir: Path, archive: Path, url: str, output: Path) -> None:
    parsed_url = urlparse(url)
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise ValidationError("release URL must be an absolute HTTPS URL")

    manifest = validate_manifest(package_dir).copy()
    manifest["url"] = url
    manifest["zipSHA256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        build_manifest(args.package, args.archive, args.url, args.output)
    except (OSError, ValidationError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

