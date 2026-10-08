#!/usr/bin/env python3
"""i2v出力の技術仕様とループ境界を検査する。"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from kamui_i2v import JapaneseArgumentParser, atomic_write_json, probe_media, require_commands


def frame_rate(value: str | None) -> float:
    if not value:
        return 0
    numerator, _, denominator = value.partition("/")
    return float(numerator) / float(denominator or 1)


def boundary_ssim(video: Path, media: dict) -> float | None:
    frames = int(media.get("nb_frames") or 0)
    if frames <= 1:
        duration = float(media.get("duration") or 0)
        frames = round(duration * frame_rate(media.get("r_frame_rate")))
    if frames <= 1:
        return None
    last = frames - 1
    with tempfile.TemporaryDirectory(prefix="i2v-inspect-") as directory:
        temporary = Path(directory)
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
                f"select=eq(n\\,0)+eq(n\\,{last})",
                "-vsync",
                "0",
                str(temporary / "boundary-%d.png"),
            ],
            check=True,
        )
        first = temporary / "boundary-1.png"
        final = temporary / "boundary-2.png"
        if not first.exists() or not final.exists():
            return None
        completed = subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-i",
                str(first),
                "-i",
                str(final),
                "-lavfi",
                "[0:v][1:v]ssim",
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            text=True,
        )
        match = re.search(r"All:([0-9.]+)", completed.stderr)
        return float(match.group(1)) if match else None


def make_contact_sheet(video: Path, media: dict, output: Path) -> None:
    frames = int(media.get("nb_frames") or 0)
    if frames <= 1:
        duration = float(media.get("duration") or 0)
        frames = round(duration * frame_rate(media.get("r_frame_rate")))
    if frames <= 1:
        return
    indices = sorted({round((frames - 1) * position / 4) for position in range(5)})
    selection = "+".join(f"eq(n\\,{index})" for index in indices)
    output.parent.mkdir(parents=True, exist_ok=True)
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
            f"select={selection},scale=320:-2,tile={len(indices)}x1",
            "-frames:v",
            "1",
            str(output),
        ],
        check=True,
    )


def scene_change_count(video: Path, threshold: float = 0.20) -> int:
    completed = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(video),
            "-vf",
            f"select='gt(scene,{threshold})',showinfo",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
    )
    return len(re.findall(r"showinfo.*pts_time:", completed.stderr))


def main() -> int:
    parser = JapaneseArgumentParser(description=__doc__)
    parser.add_argument("task_dir", type=Path, help="i2v出力ディレクトリ")
    args = parser.parse_args()
    task_dir = args.task_dir.resolve()
    require_commands("ffmpeg", "ffprobe")
    if not task_dir.is_dir():
        raise SystemExit(f"出力ディレクトリがありません: {task_dir}")

    source = next((path for path in (task_dir / "_assets").glob("source-image.*")), None)
    source_info = probe_media(source) if source else {}
    source_width = int(source_info.get("width") or 0)
    source_height = int(source_info.get("height") or 0)
    source_ratio = source_width / source_height if source_height else None

    reports = []
    inspection_dir = task_dir / "_inspection"
    for video in sorted(task_dir.glob("*.mp4")):
        media = probe_media(video)
        width = int(media.get("width") or 0)
        height = int(media.get("height") or 0)
        output_ratio = width / height if height else None
        ratio_error = (
            abs(output_ratio - source_ratio) / source_ratio
            if output_ratio and source_ratio
            else None
        )
        request_path = task_dir / "_metadata" / video.stem / "request.json"
        request = (
            json.loads(request_path.read_text(encoding="utf-8"))
            if request_path.exists()
            else {}
        )
        expected_duration = request.get("duration")
        actual_duration = float(media.get("duration") or 0)
        ssim = boundary_ssim(video, media)
        contact_sheet = inspection_dir / f"{video.stem}-contact-sheet.jpg"
        make_contact_sheet(video, media, contact_sheet)
        cuts = scene_change_count(video)
        warnings = []
        if media.get("audio_streams"):
            warnings.append("音声ストリームが残っています")
        if ratio_error is not None and ratio_error > 0.01:
            warnings.append(f"入力との比率差が{ratio_error * 100:.2f}%あります")
        if expected_duration and abs(actual_duration - float(expected_duration)) > 0.25:
            warnings.append("要求時間との差が0.25秒を超えています")
        if ssim is not None and ssim < 0.95:
            warnings.append("先頭・末尾SSIMが0.95未満です")
        if cuts:
            warnings.append(f"急な場面変化を{cuts}件検出しました")
        reports.append(
            {
                "model": video.stem,
                "file": video.name,
                "media": media,
                "source_aspect_ratio": source_ratio,
                "output_aspect_ratio": output_ratio,
                "aspect_ratio_error": ratio_error,
                "boundary_ssim": ssim,
                "scene_change_count": cuts,
                "contact_sheet": str(contact_sheet.relative_to(task_dir)),
                "warnings": warnings,
            }
        )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task_dir": str(task_dir),
        "source_image": str(source) if source else None,
        "videos": reports,
        "note": "SSIMと場面変化検出は補助指標です。文字、構図、動きの連続性はコンタクトシートとループ再生で目視確認してください。",
    }
    atomic_write_json(task_dir / "inspection.json", report)
    for item in reports:
        warning = " / ".join(item["warnings"]) or "警告なし"
        print(
            f"{item['model']}: {item['media'].get('width')}x{item['media'].get('height')} "
            f"音声={item['media'].get('audio_streams')} "
            f"SSIM={item['boundary_ssim']} 場面変化={item['scene_change_count']} {warning}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
