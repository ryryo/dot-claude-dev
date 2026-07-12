#!/usr/bin/env python3
"""承認済み正準画像から192x208のセル基準画像を作成する。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

CELL_SIZE = (192, 208)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--report-json", required=True)
    parser.add_argument("--target-height", type=int, default=190)
    parser.add_argument("--max-width", type=int, default=182)
    parser.add_argument("--bottom", type=int, default=203)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    source_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    report_path = Path(args.report_json).expanduser().resolve()
    if output_path.exists() and not args.force:
        raise SystemExit(f"出力先が存在します: {output_path}（上書きには--force）")

    with Image.open(source_path) as opened:
        source = opened.convert("RGBA")
    bbox = source.getchannel("A").getbbox()
    if bbox is None:
        raise SystemExit("正準画像が完全に透明です")
    sprite = source.crop(bbox)
    scale = min(args.target_height / sprite.height, args.max_width / sprite.width)
    width = max(1, round(sprite.width * scale))
    height = max(1, round(sprite.height * scale))
    sprite = sprite.resize((width, height), Image.Resampling.NEAREST)

    left = (CELL_SIZE[0] - width) // 2
    top = args.bottom - height
    if left < 0 or top < 0 or left + width > CELL_SIZE[0] or top + height > CELL_SIZE[1]:
        raise SystemExit(f"正準セルに収まりません: size={sprite.size}, left={left}, top={top}")
    cell = Image.new("RGBA", CELL_SIZE, (0, 0, 0, 0))
    cell.alpha_composite(sprite, (left, top))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cell.save(output_path)

    report = {
        "ok": True,
        "source": str(source_path),
        "output": str(output_path),
        "source_bbox": list(bbox),
        "cell_size": list(CELL_SIZE),
        "sprite_size": [width, height],
        "sprite_bbox": [left, top, left + width, top + height],
        "scale": round(scale, 6),
        "target_height": args.target_height,
        "bottom": args.bottom,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
