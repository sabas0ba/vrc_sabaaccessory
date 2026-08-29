#!/usr/bin/env python3
"""Release workflow で使用する package、version、tag を解決する。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from check_package import PACKAGE_PREFIX, ValidationError, validate_manifest


def resolve(
    packages_dir: Path,
    ref_type: str,
    ref_name: str,
    requested_package: str,
) -> dict[str, str]:
    package_name = requested_package
    tag_version = ""

    if ref_type == "tag":
        if "/" not in ref_name:
            raise ValidationError("release tag must be '<package-id>/v<version>'")
        tag_package, tag_version = ref_name.rsplit("/", 1)
        if package_name and package_name != tag_package:
            raise ValidationError("workflow package input does not match the tag")
        package_name = tag_package

    if not package_name:
        candidates = sorted(
            path.name
            for path in packages_dir.iterdir()
            if path.is_dir() and path.name.startswith(PACKAGE_PREFIX)
        )
        if len(candidates) != 1:
            raise ValidationError(
                "package cannot be inferred; specify it explicitly when multiple packages exist"
            )
        package_name = candidates[0]

    package_dir = packages_dir / package_name
    manifest = validate_manifest(package_dir)
    version = str(manifest["version"])
    if tag_version:
        if not tag_version.startswith("v") or tag_version[1:] != version:
            raise ValidationError(
                f"tag version {tag_version!r} does not match package version {version!r}"
            )

    tag = ref_name if ref_type == "tag" else f"{package_name}/v{version}"
    return {
        "PACKAGE": package_name,
        "VERSION": version,
        "TAG": tag,
        "MANIFEST": f"Packages/{package_name}/package.json",
        "ZIP_NAME": f"{package_name}-{version}.zip",
        "JSON_NAME": f"{package_name}-{version}.json",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packages", type=Path, default=Path("Packages"))
    parser.add_argument("--ref-type", default="")
    parser.add_argument("--ref-name", default="")
    parser.add_argument("--package", default="")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        values = resolve(args.packages, args.ref_type, args.ref_name, args.package)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            "".join(f"{key}={value}\n" for key, value in values.items()),
            encoding="utf-8",
        )
    except (OSError, ValidationError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

