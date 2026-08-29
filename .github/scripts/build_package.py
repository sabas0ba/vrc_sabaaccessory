#!/usr/bin/env python3
"""再現可能な VPM package ZIP を生成する。"""

from __future__ import annotations

import argparse
import hashlib
import stat
import sys
import zipfile
from pathlib import Path

from check_package import ValidationError, validate_manifest

FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
EXCLUDED_NAMES = {".DS_Store", "Thumbs.db"}


def build_package(package_dir: Path, output_path: Path) -> str:
    validate_manifest(package_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    files = sorted(
        path
        for path in package_dir.rglob("*")
        if path.is_file()
        and path.name not in EXCLUDED_NAMES
        and ".git" not in path.relative_to(package_dir).parts
    )
    if not files:
        raise ValidationError(f"{package_dir}: package contains no files")

    with zipfile.ZipFile(
        output_path,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path in files:
            if path.is_symlink():
                raise ValidationError(f"{path}: symbolic links are not allowed")
            relative = path.relative_to(package_dir).as_posix()
            info = zipfile.ZipInfo(relative, FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            mode = stat.S_IMODE(path.stat().st_mode)
            info.external_attr = (mode or 0o644) << 16
            archive.writestr(info, path.read_bytes(), compresslevel=9)

    digest = hashlib.sha256(output_path.read_bytes()).hexdigest()
    return digest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    try:
        digest = build_package(args.package, args.output)
    except ValidationError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(f"created {args.output}")
    print(f"sha256 {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

