#!/usr/bin/env python3
"""採用i2v動画を修復し、Web配信用MP4・WebM・posterを作成する。"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from kamui_i2v import atomic_write_json, probe_media, require_commands


def encode_mp4(
    source: Path,
    output: Path,
    repair: str,
    trim_end: float,
    crossfade_duration: float,
    crf: int,
) -> None:
    media = probe_media(source)
    duration = float(media.get("duration") or 0)
    frames = int(media.get("nb_frames") or 0)
    base = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(source)]
    mapping = ["-map", "0:v:0"]

    if repair == "trim":
        target = duration - trim_end
        if target <= 0.5:
            raise ValueError("trim後の動画が0.5秒以下になります")
        mapping += ["-t", f"{target:.6f}"]
    elif repair == "crossfade":
        fade = crossfade_duration
        if fade <= 0 or fade >= duration / 3:
            raise ValueError("crossfade-durationは0より大きく動画時間の1/3未満にしてください")
        middle_end = duration - fade
        filter_complex = (
            f"[0:v]split=3[headsrc][middlesrc][tailsrc];"
            f"[headsrc]trim=start=0:end={fade:.6f},settb=AVTB,setpts=PTS-STARTPTS[head];"
            f"[middlesrc]trim=start={fade:.6f}:end={middle_end:.6f},settb=AVTB,setpts=PTS-STARTPTS[middle];"
            f"[tailsrc]trim=start={middle_end:.6f}:end={duration:.6f},settb=AVTB,setpts=PTS-STARTPTS[tail];"
            f"[tail][head]xfade=transition=fade:duration={fade:.6f}:offset=0[seam];"
            f"[middle][seam]concat=n=2:v=1:a=0,format=yuv420p[outv]"
        )
        base += ["-filter_complex", filter_complex]
        mapping = ["-map", "[outv]"]
    elif repair == "pingpong":
        if frames <= 2:
            raise ValueError("ping-pongにはフレーム数情報が必要です")
        filter_complex = (
            f"[0:v]split=2[forward][reversesrc];"
            f"[forward]setpts=PTS-STARTPTS[f];"
            f"[reversesrc]reverse,trim=start_frame=1:end_frame={frames - 1},setpts=PTS-STARTPTS[r];"
            f"[f][r]concat=n=2:v=1:a=0,format=yuv420p[outv]"
        )
        base += ["-filter_complex", filter_complex]
        mapping = ["-map", "[outv]"]
    elif repair != "none":
        raise ValueError(f"未対応のrepairです: {repair}")

    temporary = output.with_name(f".{output.stem}.tmp.mp4")
    command = base + mapping + [
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        str(crf),
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(temporary),
    ]
    subprocess.run(command, check=True)
    temporary.replace(output)


def encode_webm(source: Path, output: Path, crf: int) -> None:
    temporary = output.with_name(f".{output.stem}.tmp.webm")
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-map",
            "0:v:0",
            "-an",
            "-c:v",
            "libvpx-vp9",
            "-crf",
            str(crf),
            "-b:v",
            "0",
            "-row-mt",
            "1",
            "-deadline",
            "good",
            "-cpu-used",
            "2",
            str(temporary),
        ],
        check=True,
    )
    temporary.replace(output)


def make_poster(source: Path, output: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-frames:v",
            "1",
            "-c:v",
            "libwebp",
            "-quality",
            "85",
            str(output),
        ],
        check=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_dir", type=Path)
    parser.add_argument("--model", action="append", dest="models")
    parser.add_argument("--repair", choices=["none", "trim", "crossfade", "pingpong"], default="none")
    parser.add_argument("--trim-end", type=float, default=0.25)
    parser.add_argument("--crossfade-duration", type=float, default=0.3)
    parser.add_argument("--crf", type=int, default=20)
    parser.add_argument("--webm-crf", type=int, default=32)
    parser.add_argument("--no-webm", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    require_commands("ffmpeg", "ffprobe")
    task_dir = args.task_dir.resolve()
    if not task_dir.is_dir():
        raise SystemExit(f"出力ディレクトリがありません: {task_dir}")
    videos = (
        [task_dir / f"{model}.mp4" for model in args.models]
        if args.models
        else sorted(task_dir.glob("*.mp4"))
    )
    missing = [str(video) for video in videos if not video.exists()]
    if missing:
        raise SystemExit(f"動画がありません: {', '.join(missing)}")
    if not videos:
        raise SystemExit("処理対象のMP4がありません")

    delivery_dir = task_dir / "_delivery"
    delivery_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = delivery_dir / "delivery-manifest.json"
    previous = {}
    if manifest_path.exists():
        previous_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        previous = {item["model"]: item for item in previous_data.get("videos", [])}
    records = []
    for video in videos:
        model = video.stem
        mp4 = delivery_dir / f"{model}.mp4"
        webm = delivery_dir / f"{model}.webm"
        poster = delivery_dir / f"{model}-poster.webp"
        if mp4.exists() and not args.overwrite:
            expected = {
                "repair": args.repair,
                "trim_end": args.trim_end,
                "crossfade_duration": args.crossfade_duration,
                "crf": args.crf,
                "webm_crf": args.webm_crf if not args.no_webm else None,
            }
            actual = previous.get(model)
            if not actual or any(actual.get(key) != value for key, value in expected.items()):
                raise SystemExit(
                    f"{model}: 既存の配信MP4と指定条件が一致しません。"
                    "条件を変更する場合は--overwriteを指定してください"
                )
            print(f"{model}: 配信MP4が存在するためスキップ")
        else:
            encode_mp4(video, mp4, args.repair, args.trim_end, args.crossfade_duration, args.crf)
        if not args.no_webm and (args.overwrite or not webm.exists()):
            encode_webm(mp4, webm, args.webm_crf)
        elif args.no_webm and args.overwrite:
            webm.unlink(missing_ok=True)
        if args.overwrite or not poster.exists():
            make_poster(mp4, poster)
        media = probe_media(mp4)
        if media.get("audio_streams"):
            raise RuntimeError(f"音声が残っています: {mp4}")
        records.append(
            {
                "model": model,
                "source": video.name,
                "repair": args.repair,
                "trim_end": args.trim_end,
                "crossfade_duration": args.crossfade_duration,
                "crf": args.crf,
                "webm_crf": args.webm_crf if not args.no_webm else None,
                "mp4": mp4.name,
                "webm": webm.name if webm.exists() else None,
                "poster": poster.name,
                "media": media,
            }
        )
        print(f"{model}: {mp4}")

    atomic_write_json(
        manifest_path,
        {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "repair": args.repair,
            "videos": records,
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
