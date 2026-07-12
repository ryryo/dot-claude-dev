#!/usr/bin/env python3
"""状態行ごとの共通倍率で身長・足元・ジャンプ幅を検証・正規化する。"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from PIL import Image

CELL_WIDTH = 192
CELL_HEIGHT = 208
ROW_SPECS = [
    ("idle", 0, 6),
    ("running-right", 1, 8),
    ("running-left", 2, 8),
    ("waving", 3, 4),
    ("jumping", 4, 5),
    ("failed", 5, 8),
    ("waiting", 6, 6),
    ("running", 7, 6),
    ("review", 8, 6),
]
FRAME_COUNTS = {state: count for state, _row, count in ROW_SPECS}


def parse_states(raw: str) -> list[str]:
    all_states = list(FRAME_COUNTS)
    if raw.strip().lower() == "all":
        return all_states
    states = [item.strip() for item in raw.split(",") if item.strip()]
    unknown = sorted(set(states) - set(all_states))
    if unknown:
        raise SystemExit(f"不明な状態です: {', '.join(unknown)}")
    return states


def alpha_bbox(image: Image.Image) -> tuple[int, int, int, int]:
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError("透明な空フレームは正規化できません")
    return bbox


def load_from_atlas(path: Path, states: list[str]) -> dict[str, list[Image.Image]]:
    with Image.open(path) as opened:
        atlas = opened.convert("RGBA")
    expected = (CELL_WIDTH * 8, CELL_HEIGHT * 9)
    if atlas.size != expected:
        raise SystemExit(f"アトラスは{expected[0]}x{expected[1]}が必要です: {atlas.size}")
    rows: dict[str, list[Image.Image]] = {}
    for state, row, count in ROW_SPECS:
        if state not in states:
            continue
        rows[state] = [
            atlas.crop((column * CELL_WIDTH, row * CELL_HEIGHT, (column + 1) * CELL_WIDTH, (row + 1) * CELL_HEIGHT))
            for column in range(count)
        ]
    return rows


def load_from_frames(root: Path, states: list[str]) -> dict[str, list[Image.Image]]:
    rows: dict[str, list[Image.Image]] = {}
    for state in states:
        state_dir = root / state
        files = sorted(p for p in state_dir.iterdir() if p.suffix.lower() in {".png", ".webp"}) if state_dir.is_dir() else []
        expected = FRAME_COUNTS[state]
        if len(files) < expected:
            raise SystemExit(f"{state}は{expected}フレーム必要です: {len(files)}")
        frames: list[Image.Image] = []
        for path in files[:expected]:
            with Image.open(path) as opened:
                frame = opened.convert("RGBA")
            if frame.size != (CELL_WIDTH, CELL_HEIGHT):
                raise SystemExit(f"セル寸法が不正です: {path} {frame.size}")
            frames.append(frame)
        rows[state] = frames
    return rows


def resize_sprite(cell: Image.Image, scale: float) -> Image.Image:
    bbox = alpha_bbox(cell)
    sprite = cell.crop(bbox)
    size = (max(1, round(sprite.width * scale)), max(1, round(sprite.height * scale)))
    return sprite.resize(size, Image.Resampling.NEAREST)


def place_sprite(sprite: Image.Image, bottom: int, min_top: int, max_bottom: int) -> Image.Image:
    target = Image.new("RGBA", (CELL_WIDTH, CELL_HEIGHT), (0, 0, 0, 0))
    left = (CELL_WIDTH - sprite.width) // 2
    top = bottom - sprite.height
    if top < min_top:
        top = min_top
    if top + sprite.height > max_bottom:
        top = max_bottom - sprite.height
    if left < 0 or top < 0 or left + sprite.width > CELL_WIDTH or top + sprite.height > CELL_HEIGHT:
        raise ValueError(f"正規化後にセルを超えます: size={sprite.size}, left={left}, top={top}")
    target.alpha_composite(sprite, (left, top))
    return target


def normalize(rows: dict[str, list[Image.Image]], states: list[str], args: argparse.Namespace) -> dict[str, object]:
    if "idle" not in rows and args.target_height is None:
        raise SystemExit("idleを含めない場合は--target-heightが必要です")
    target = args.target_height or max(alpha_bbox(frame)[3] - alpha_bbox(frame)[1] for frame in rows["idle"])
    target_width = args.target_width or (
        max(alpha_bbox(frame)[2] - alpha_bbox(frame)[0] for frame in rows["idle"])
        if "idle" in rows
        else None
    )
    errors: list[str] = []
    warnings: list[str] = []
    prepared: dict[str, dict[str, object]] = {}

    for state in states:
        frames = rows[state]
        boxes = [alpha_bbox(frame) for frame in frames]
        heights = [box[3] - box[1] for box in boxes]
        widths = [box[2] - box[0] for box in boxes]
        row_max = max(heights)
        required_scale = target / row_max
        normal_limit = args.jump_max_scale if state == "jumping" else args.max_scale
        if required_scale > normal_limit and not args.allow_large_correction:
            errors.append(
                f"{state}: 必要倍率{required_scale:.3f}が上限{normal_limit:.3f}を超えます。後補正せず再生成してください"
            )
            scale = normal_limit
        elif required_scale > normal_limit:
            scale = min(required_scale, args.repair_max_scale)
            warnings.append(f"{state}: 修復モードで大幅補正{scale:.3f}を適用します")
        elif required_scale < args.min_scale:
            errors.append(
                f"{state}: 必要倍率{required_scale:.3f}が下限{args.min_scale:.3f}未満です。大きすぎるため再生成してください"
            )
            scale = args.min_scale
        else:
            scale = required_scale

        if state == "jumping":
            bottoms = [box[3] for box in boxes]
            landing = max(bottoms[0], bottoms[-1])
            apex = min(bottoms)
            span = max(1, landing - apex)
            desired_bottoms = [
                args.max_bottom - round(args.jump_amplitude * (landing - bottom) / span)
                for bottom in bottoms
            ]
        else:
            desired_bottoms = [min(box[3], args.max_bottom) for box in boxes]
        prepared[state] = {
            "frames": frames,
            "heights": heights,
            "widths": widths,
            "row_max": row_max,
            "required_scale": required_scale,
            "scale": scale,
            "desired_bottoms": desired_bottoms,
        }

    report_rows: dict[str, object] = {}
    if not errors or args.allow_large_correction:
        output_root = Path(args.output_frames_root).expanduser().resolve()
        if output_root.exists():
            if not args.force:
                raise SystemExit(f"出力先が存在します: {output_root}（上書きには--force）")
            shutil.rmtree(output_root)
        for state in states:
            values = prepared[state]
            state_dir = output_root / state
            state_dir.mkdir(parents=True, exist_ok=True)
            output_heights: list[int] = []
            output_widths: list[int] = []
            output_bottoms: list[int] = []
            for index, (frame, bottom) in enumerate(zip(values["frames"], values["desired_bottoms"])):
                normalized = place_sprite(
                    resize_sprite(frame, float(values["scale"])),
                    int(bottom),
                    args.min_top,
                    args.max_bottom,
                )
                bbox = alpha_bbox(normalized)
                output_heights.append(bbox[3] - bbox[1])
                output_widths.append(bbox[2] - bbox[0])
                output_bottoms.append(bbox[3])
                normalized.save(state_dir / f"frame-{index:02d}.png")

            height_ratio = max(output_heights) / target
            min_width_ratio = min(output_widths) / target_width if target_width is not None else None
            vertical_range = max(output_bottoms) - min(output_bottoms)
            if state == "jumping":
                if height_ratio < args.jump_min_height_ratio:
                    errors.append(
                        f"jumping: 正規化後の最大身長比{height_ratio:.3f}が下限{args.jump_min_height_ratio:.3f}未満です"
                    )
                if target_width is not None:
                    assert min_width_ratio is not None
                    if min_width_ratio < args.jump_min_width_ratio:
                        errors.append(
                            f"jumping: 最小横幅比{min_width_ratio:.3f}が下限{args.jump_min_width_ratio:.3f}未満です。カメラ引きまたは全体縮小を疑ってください"
                        )
                if not args.jump_min_amplitude <= vertical_range <= args.jump_max_amplitude:
                    errors.append(
                        f"jumping: 上下幅{vertical_range}pxが許容範囲{args.jump_min_amplitude}-{args.jump_max_amplitude}px外です"
                    )
            else:
                tolerance = args.height_tolerance
                if abs(height_ratio - 1.0) > tolerance:
                    errors.append(f"{state}: 最大身長比{height_ratio:.3f}が±{tolerance:.3f}を超えます")
                baseline_limit = args.directional_baseline_range if state in {"running-right", "running-left"} else args.static_baseline_range
                if vertical_range > baseline_limit:
                    errors.append(f"{state}: 足元変動{vertical_range}pxが上限{baseline_limit}pxを超えます")
            report_rows[state] = {
                "input_heights": values["heights"],
                "input_widths": values["widths"],
                "input_max_height": values["row_max"],
                "required_scale": round(float(values["required_scale"]), 6),
                "applied_scale": round(float(values["scale"]), 6),
                "output_heights": output_heights,
                "output_widths": output_widths,
                "output_bottoms": output_bottoms,
                "output_max_height_ratio": round(height_ratio, 6),
                "output_min_width_ratio": round(min_width_ratio, 6) if min_width_ratio is not None else None,
                "output_vertical_range": vertical_range,
            }
    else:
        for state in states:
            values = prepared[state]
            report_rows[state] = {
                "input_heights": values["heights"],
                "input_widths": values["widths"],
                "input_max_height": values["row_max"],
                "required_scale": round(float(values["required_scale"]), 6),
                "normal_scale_limit": args.jump_max_scale if state == "jumping" else args.max_scale,
            }

    return {
        "ok": not errors,
        "target_height": target,
        "target_width": target_width,
        "jump_amplitude": args.jump_amplitude,
        "allow_large_correction": args.allow_large_correction,
        "errors": errors,
        "warnings": warnings,
        "rows": report_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input-atlas")
    source.add_argument("--input-frames-root")
    parser.add_argument("--output-frames-root", required=True)
    parser.add_argument("--report-json", required=True)
    parser.add_argument("--states", default="all")
    parser.add_argument("--target-height", type=int)
    parser.add_argument("--target-width", type=int)
    parser.add_argument("--max-scale", type=float, default=1.12)
    parser.add_argument("--jump-max-scale", type=float, default=1.15)
    parser.add_argument("--min-scale", type=float, default=0.90)
    parser.add_argument("--repair-max-scale", type=float, default=1.40)
    parser.add_argument("--allow-large-correction", action="store_true")
    parser.add_argument("--height-tolerance", type=float, default=0.05)
    parser.add_argument("--jump-min-height-ratio", type=float, default=0.92)
    parser.add_argument("--jump-min-width-ratio", type=float, default=0.88)
    parser.add_argument("--jump-amplitude", type=int, default=10)
    parser.add_argument("--jump-min-amplitude", type=int, default=8)
    parser.add_argument("--jump-max-amplitude", type=int, default=16)
    parser.add_argument("--static-baseline-range", type=int, default=4)
    parser.add_argument("--directional-baseline-range", type=int, default=12)
    parser.add_argument("--min-top", type=int, default=5)
    parser.add_argument("--max-bottom", type=int, default=203)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    states = parse_states(args.states)
    rows = (
        load_from_atlas(Path(args.input_atlas).expanduser().resolve(), states)
        if args.input_atlas
        else load_from_frames(Path(args.input_frames_root).expanduser().resolve(), states)
    )
    report = normalize(rows, states, args)
    report_path = Path(args.report_json).expanduser().resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
