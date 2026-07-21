#!/usr/bin/env python3
"""固定カメラ人物動画へ参考画像風の日本語テロップを焼き込む。"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from kamui_i2v import atomic_write_json, probe_media, require_commands


DEFAULT_LINE1 = "サブスクで明朗会計"
DEFAULT_LINE2 = "勧誘一切無し"


def run_text(command: list[str]) -> str:
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return completed.stdout.strip()


def choose_font(explicit: str | None) -> str:
    if explicit:
        return explicit
    candidates = [
        "Hiragino Sans:style=W9",
        "Hiragino Sans:style=W8",
        "Hiragino Kaku Gothic StdN:style=W8",
        "Hiragino Kaku Gothic ProN:style=W6",
        "Arial Unicode MS",
    ]
    for family in candidates:
        try:
            path = run_text(["fc-match", "-f", "%{file}", family])
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
        if path and Path(path).exists():
            return path
    fallbacks = [
        "/System/Library/Fonts/ヒラギノ角ゴシック W9.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for path in fallbacks:
        if Path(path).exists():
            return path
    raise RuntimeError("日本語フォントが見つかりません。--font-fileを指定してください")


def escape_drawtext_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def hex_color(value: str) -> str:
    cleaned = value.strip().lstrip("#")
    if len(cleaned) not in {6, 8} or any(char not in "0123456789abcdefABCDEF" for char in cleaned):
        raise ValueError(f"色はRRGGBBまたはRRGGBBAAで指定してください: {value}")
    return cleaned.upper()


def build_filter(args: argparse.Namespace, width: int, height: int, font: str) -> str:
    font_size1 = round(height * args.font_scale1)
    font_size2 = round(height * args.font_scale2)
    pad_x = round(width * args.box_pad_x_ratio)
    pad_y = round(height * args.box_pad_y_ratio)
    y1 = round(height * args.y1_ratio)
    y2 = round(height * args.y2_ratio)
    bg = f"0x{hex_color(args.bg_color)}@{args.bg_opacity}"
    text = f"0x{hex_color(args.text_color)}"
    border = f"0x{hex_color(args.border_color)}"
    font_q = font.replace("\\", "\\\\").replace(":", "\\:")
    line1 = escape_drawtext_text(args.line1)
    line2 = escape_drawtext_text(args.line2)
    return ",".join(
        [
            (
                f"drawtext=fontfile='{font_q}':text='{line1}':"
                f"x=(w-text_w)/2:y={y1 + pad_y - round(font_size1 * 0.06)}:"
                f"fontsize={font_size1}:fontcolor={text}:borderw={args.border_width}:bordercolor={border}:"
                f"box=1:boxcolor={bg}:boxborderw={pad_x}"
            ),
            (
                f"drawtext=fontfile='{font_q}':text='{line2}':"
                f"x=(w-text_w)/2:y={y2 + pad_y - round(font_size2 * 0.06)}:"
                f"fontsize={font_size2}:fontcolor={text}:borderw={args.border_width}:bordercolor={border}:"
                f"box=1:boxcolor={bg}:boxborderw={pad_x}"
            ),
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--line1", default=DEFAULT_LINE1)
    parser.add_argument("--line2", default=DEFAULT_LINE2)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--font-file")
    parser.add_argument("--bg-color", default="FFF176")
    parser.add_argument("--bg-opacity", type=float, default=0.97)
    parser.add_argument("--text-color", default="17120F")
    parser.add_argument("--border-color", default="FFFFFF")
    parser.add_argument("--border-width", type=int, default=6)
    parser.add_argument("--font-scale1", type=float, default=0.083)
    parser.add_argument("--font-scale2", type=float, default=0.089)
    parser.add_argument("--y1-ratio", type=float, default=0.594)
    parser.add_argument("--y2-ratio", type=float, default=0.761)
    parser.add_argument("--box-pad-x-ratio", type=float, default=0.022)
    parser.add_argument("--box-pad-y-ratio", type=float, default=0.012)
    parser.add_argument("--min-box-width-ratio", type=float, default=0.50)
    parser.add_argument("--max-box-width-ratio", type=float, default=0.78)
    parser.add_argument("--crf", type=int, default=18)
    parser.add_argument("--contact-sheet", action="store_true", default=True)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    require_commands("ffmpeg", "ffprobe")
    video = args.video.resolve()
    if not video.is_file():
        raise SystemExit(f"動画がありません: {video}")
    media = probe_media(video)
    width = int(media.get("width") or 0)
    height = int(media.get("height") or 0)
    if not width or not height:
        raise SystemExit(f"動画サイズを取得できません: {video}")

    output = args.out.resolve() if args.out else video.parent / "_telop" / f"{video.stem}-telop.mp4"
    telop_dir = output.parent
    telop_dir.mkdir(parents=True, exist_ok=True)
    if output.exists() and not args.overwrite:
        raise SystemExit(f"出力が既にあります。上書きするには--overwriteを指定してください: {output}")

    font = choose_font(args.font_file)
    vf = build_filter(args, width, height, font)
    temporary = output.with_name(f".{output.stem}.tmp.mp4")
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(video),
            "-vf",
            vf,
            "-map",
            "0:v:0",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            str(args.crf),
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(temporary),
        ],
        check=True,
    )
    temporary.replace(output)

    sheet = telop_dir / f"{output.stem}-contact-sheet.jpg"
    if args.contact_sheet:
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(output),
                "-vf",
                "fps=1,scale=360:-1,tile=5x1",
                "-frames:v",
                "1",
                str(sheet),
            ],
            check=True,
        )

    request_path = telop_dir / f"{output.stem}-request.json"
    atomic_write_json(
        request_path,
        {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": str(video),
            "output": str(output),
            "contact_sheet": str(sheet) if sheet.exists() else None,
            "font": font,
            "ffmpeg_filter": vf,
            "options": {
                key: value
                for key, value in vars(args).items()
                if key not in {"video", "out", "font_file", "contact_sheet"}
            },
        },
    )
    final_media = probe_media(output)
    if final_media.get("audio_streams"):
        raise RuntimeError(f"音声が残っています: {output}")
    print(output)
    if sheet.exists():
        print(sheet)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
