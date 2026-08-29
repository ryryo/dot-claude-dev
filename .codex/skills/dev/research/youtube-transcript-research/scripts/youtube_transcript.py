#!/usr/bin/env python3
"""Search YouTube and save complete caption tracks as research data."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def require_yt_dlp() -> str:
    executable = shutil.which("yt-dlp")
    if not executable:
        raise SystemExit("yt-dlp was not found in PATH")
    return executable


def run(command: list[str], *, capture: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=True,
        text=True,
        capture_output=capture,
    )


def safe_write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def command_search(args: argparse.Namespace) -> int:
    yt_dlp = require_yt_dlp()
    result = run(
        [
            yt_dlp,
            f"ytsearch{args.limit}:{args.query}",
            "--flat-playlist",
            "--no-warnings",
            "--dump-json",
        ]
    )

    rows: list[dict[str, Any]] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        row = {
            "id": item.get("id"),
            "title": item.get("title"),
            "channel": item.get("channel") or item.get("uploader"),
            "duration": item.get("duration"),
            "url": item.get("webpage_url") or item.get("url"),
            "query": args.query,
        }
        rows.append(row)

    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )

    for row in rows:
        duration = row.get("duration") or ""
        print(
            "\t".join(
                str(row.get(key) or "")
                for key in ("id", "title", "channel")
            )
            + f"\t{duration}\t{row.get('url') or ''}"
        )
    return 0


def format_timestamp(milliseconds: int) -> str:
    seconds = max(0, milliseconds // 1000)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def clean_json3(source: Path, destination_prefix: Path) -> int:
    data = json.loads(source.read_text(encoding="utf-8"))
    rows: list[tuple[str, str]] = []
    for event in data.get("events", []):
        segments = event.get("segs")
        if not segments:
            continue
        text = "".join(str(segment.get("utf8", "")) for segment in segments)
        text = " ".join(text.replace("\u200b", "").split())
        if not text:
            continue
        timestamp = format_timestamp(int(event.get("tStartMs", 0)))
        rows.append((timestamp, text))

    tsv_path = Path(str(destination_prefix) + ".transcript.tsv")
    txt_path = Path(str(destination_prefix) + ".transcript.txt")
    tsv_path.write_text(
        "".join(f"{timestamp}\t{text}\n" for timestamp, text in rows),
        encoding="utf-8",
    )
    txt_path.write_text(
        "".join(f"[{timestamp}] {text}\n" for timestamp, text in rows),
        encoding="utf-8",
    )
    return len(rows)


def fetch_one(yt_dlp: str, url: str, output_root: Path, languages: str) -> dict[str, Any]:
    metadata_result = run(
        [yt_dlp, url, "--skip-download", "--no-warnings", "--dump-single-json"]
    )
    metadata = json.loads(metadata_result.stdout)
    video_id = str(metadata.get("id") or "unknown-video")
    video_dir = output_root / video_id
    video_dir.mkdir(parents=True, exist_ok=True)
    safe_write_json(video_dir / "metadata.json", metadata)

    caption_command = [
        yt_dlp,
        url,
        "--skip-download",
        "--write-subs",
        "--write-auto-subs",
        "--sub-langs",
        languages,
        "--sub-format",
        "json3",
        "--no-warnings",
        "-o",
        str(video_dir / "%(id)s.%(ext)s"),
    ]
    caption_error: str | None = None
    try:
        run(caption_command)
    except subprocess.CalledProcessError as error:
        caption_error = (error.stderr or error.stdout or str(error)).strip()

    transcript_files: list[dict[str, Any]] = []
    for subtitle in sorted(video_dir.glob("*.json3")):
        prefix = subtitle.with_suffix("")
        segment_count = clean_json3(subtitle, prefix)
        transcript_files.append(
            {
                "subtitle": subtitle.name,
                "transcript_tsv": Path(str(prefix) + ".transcript.tsv").name,
                "transcript_text": Path(str(prefix) + ".transcript.txt").name,
                "segments": segment_count,
            }
        )

    manifest = {
        "id": video_id,
        "title": metadata.get("title"),
        "channel": metadata.get("channel") or metadata.get("uploader"),
        "upload_date": metadata.get("upload_date"),
        "duration": metadata.get("duration"),
        "webpage_url": metadata.get("webpage_url") or url,
        "requested_languages": languages,
        "transcripts": transcript_files,
        "caption_error": caption_error,
    }
    safe_write_json(video_dir / "manifest.json", manifest)
    return manifest


def command_fetch(args: argparse.Namespace) -> int:
    yt_dlp = require_yt_dlp()
    output_root = Path(args.output_dir).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    fetched = [
        fetch_one(yt_dlp, url, output_root, args.languages)
        for url in args.url
    ]
    manifest_path = output_root / "manifest.json"
    existing: list[dict[str, Any]] = []
    if manifest_path.exists():
        loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
        if isinstance(loaded, list):
            existing = [item for item in loaded if isinstance(item, dict)]
    by_id = {str(item.get("id")): item for item in existing if item.get("id")}
    for item in fetched:
        by_id[str(item["id"])] = item
    manifests = list(by_id.values())
    safe_write_json(manifest_path, manifests)

    missing = 0
    for manifest in fetched:
        count = len(manifest["transcripts"])
        print(
            f"{manifest['id']}\t{count} transcript track(s)\t"
            f"{manifest.get('title') or ''}"
        )
        if count == 0:
            missing += 1
    return 2 if missing else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search YouTube and save complete caption tracks for research."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Search YouTube and emit candidate metadata")
    search.add_argument("--query", required=True)
    search.add_argument("--limit", type=int, default=20)
    search.add_argument("--output", help="Optional JSON Lines output path")
    search.set_defaults(handler=command_search)

    fetch = subparsers.add_parser("fetch", help="Fetch complete caption tracks for selected videos")
    fetch.add_argument("--url", action="append", required=True)
    fetch.add_argument("--output-dir", required=True)
    fetch.add_argument("--languages", default="ja-orig,ja")
    fetch.set_defaults(handler=command_fetch)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.handler(args))
    except subprocess.CalledProcessError as error:
        message = (error.stderr or error.stdout or str(error)).strip()
        print(message, file=sys.stderr)
        return error.returncode or 1


if __name__ == "__main__":
    raise SystemExit(main())
