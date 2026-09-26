#!/usr/bin/env python3
"""Build a reviewed, manifest-bearing ZIP from an explicit file list."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


SECRET_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "credentials.json",
    "service-account.json",
    "id_rsa",
    "id_ed25519",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--files", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def relative_file(root: Path, raw: str) -> tuple[Path, str]:
    name = raw.strip()
    if not name:
        raise ValueError("empty path in file list")
    relative = PurePosixPath(name)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"path escapes root: {name}")
    if any(part in {"", "."} for part in relative.parts):
        raise ValueError(f"non-canonical path: {name}")
    if relative.name in SECRET_NAMES or relative.name.startswith(".env."):
        raise ValueError(f"secret-like file is not allowed: {name}")
    path = (root / Path(*relative.parts)).resolve()
    if root not in path.parents:
        raise ValueError(f"path escapes root: {name}")
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"not a regular file: {name}")
    return path, relative.as_posix()


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    output = args.output.resolve()
    if not root.is_dir():
        raise SystemExit(f"root is not a directory: {root}")
    if output == root or root in output.parents:
        raise SystemExit("output must be outside root")

    entries: list[tuple[Path, str, bytes]] = []
    seen: set[str] = set()
    for line in args.files.read_text(encoding="utf-8").splitlines():
        path, archive_name = relative_file(root, line)
        if archive_name in seen:
            raise SystemExit(f"duplicate path: {archive_name}")
        seen.add(archive_name)
        data = path.read_bytes()
        entries.append((path, archive_name, data))

    entries.sort(key=lambda item: item[1])
    manifest = {
        "format": 1,
        "root": "reviewed file list; local root intentionally omitted",
        "files": [
            {
                "path": archive_name,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
            for _, archive_name, data in entries
        ],
    }
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for _, archive_name, data in entries:
            info = ZipInfo(archive_name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, data)
        info = ZipInfo("BUNDLE-MANIFEST.json", date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = ZIP_DEFLATED
        archive.writestr(info, manifest_bytes)
    print(json.dumps({"output": str(output), "files": len(entries), "manifest": "BUNDLE-MANIFEST.json"}))


if __name__ == "__main__":
    main()
