#!/usr/bin/env python3
"""人物i2v用の入力画像を非破壊で準備する。"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

from kamui_i2v import require_commands, sanitize_task


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--task", required=True)
    parser.add_argument("--quality", type=int, default=3, help="ffmpeg q:v。小さいほど高品質")
    parser.add_argument("--max-width", type=int, help="必要な場合だけ横幅を縮小する")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    require_commands("ffmpeg", "ffprobe")
    task = sanitize_task(args.task)
    source = args.source.resolve()
    if not source.is_file():
        raise SystemExit(f"入力画像がありません: {source}")

    task_dir = args.project.resolve() / "output" / task
    assets_dir = task_dir / "_assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    original = assets_dir / f"source-image-original{source.suffix.lower()}"
    prepared = assets_dir / "source-image-prepared.jpg"

    if prepared.exists() and not args.overwrite:
        print(prepared)
        return 0

    shutil.copy2(source, original)
    vf = []
    if args.max_width:
        vf.append(f"scale='min({args.max_width},iw)':-2")

    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
        "-map_metadata",
        "-1",
    ]
    if vf:
        command += ["-vf", ",".join(vf)]
    command += ["-q:v", str(args.quality), str(prepared)]
    subprocess.run(command, check=True)

    print(prepared)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
