#!/usr/bin/env python3
"""状態切り替え時の見かけサイズを確認する遷移GIFを作成する。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image


def image_files(path: Path) -> list[Path]:
    return sorted(p for p in path.iterdir() if p.suffix.lower() in {".png", ".webp"})


def load_frames(root: Path, state: str) -> list[Image.Image]:
    state_dir = root / state
    if not state_dir.is_dir():
        raise SystemExit(f"フレームディレクトリがありません: {state_dir}")
    files = image_files(state_dir)
    if not files:
        raise SystemExit(f"フレームがありません: {state_dir}")
    frames: list[Image.Image] = []
    for path in files:
        with Image.open(path) as opened:
            frames.append(opened.convert("RGBA"))
    return frames


def gif_ready(image: Image.Image) -> Image.Image:
    canvas = Image.new("RGBA", image.size, (0, 0, 0, 0))
    canvas.alpha_composite(image)
    return canvas.convert("P", palette=Image.Palette.ADAPTIVE, colors=255)


def save_gif(frames: list[Image.Image], durations: list[int], output: Path, scale: int) -> None:
    prepared = [
        gif_ready(
            frame.resize(
                (frame.width * scale, frame.height * scale),
                Image.Resampling.NEAREST,
            )
            if scale != 1
            else frame
        )
        for frame in frames
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    prepared[0].save(
        output,
        save_all=True,
        append_images=prepared[1:],
        duration=durations,
        loop=0,
        disposal=2,
        transparency=0,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--report-json", required=True)
    parser.add_argument(
        "--transitions",
        default="idle:jumping:idle,idle:failed:idle",
        help="カンマ区切り。各遷移はコロン区切りの状態列。",
    )
    parser.add_argument("--frame-duration", type=int, default=140)
    parser.add_argument("--boundary-hold", type=int, default=420)
    parser.add_argument("--zoom-scale", type=int, default=3)
    args = parser.parse_args()

    root = Path(args.frames_root).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    results: list[dict[str, object]] = []
    for raw in args.transitions.split(","):
        states = [state.strip() for state in raw.split(":") if state.strip()]
        if len(states) < 2:
            raise SystemExit(f"遷移指定が不正です: {raw}")
        sequence: list[Image.Image] = []
        durations: list[int] = []
        for state in states:
            state_frames = load_frames(root, state)
            sequence.extend(state_frames)
            state_durations = [args.frame_duration] * len(state_frames)
            state_durations[-1] = args.boundary_hold
            durations.extend(state_durations)
        name = "-to-".join(states)
        actual = output_dir / f"{name}.gif"
        zoomed = output_dir / f"{name}@{args.zoom_scale}x.gif"
        save_gif(sequence, durations, actual, 1)
        save_gif(sequence, durations, zoomed, args.zoom_scale)
        results.append(
            {
                "states": states,
                "frames": len(sequence),
                "actual_size": str(actual),
                "zoomed": str(zoomed),
            }
        )
    report = {"ok": True, "transitions": results}
    report_path = Path(args.report_json).expanduser().resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
