#!/usr/bin/env python3
"""生成行を非破壊で透明化・デスピルし、抽出前のRGBA行を作成する。"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image

ALL_STATES = [
    "idle",
    "running-right",
    "running-left",
    "waving",
    "jumping",
    "failed",
    "waiting",
    "running",
    "review",
]


def parse_states(raw: str) -> list[str]:
    if raw.strip().lower() == "all":
        return ALL_STATES
    states = [item.strip() for item in raw.split(",") if item.strip()]
    unknown = sorted(set(states) - set(ALL_STATES))
    if unknown:
        raise SystemExit(f"不明な状態です: {', '.join(unknown)}")
    return states


def helper_path() -> Path:
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    path = codex_home / "skills/.system/imagegen/scripts/remove_chroma_key.py"
    if not path.is_file():
        raise SystemExit(f"imagegenのクロマキーヘルパーが見つかりません: {path}")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--report-json", required=True)
    parser.add_argument("--states", default="all")
    parser.add_argument("--edge-contract", type=int, default=1)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    input_dir = Path(args.input_dir).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    report_path = Path(args.report_json).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    helper = helper_path()
    results: dict[str, object] = {}

    for state in parse_states(args.states):
        source = input_dir / f"{state}.png"
        output = output_dir / f"{state}.png"
        if not source.is_file():
            raise SystemExit(f"入力行がありません: {source}")
        if output.exists() and not args.force:
            raise SystemExit(f"出力先が存在します: {output}（上書きには--force）")
        command = [
            sys.executable,
            str(helper),
            "--input",
            str(source),
            "--out",
            str(output),
            "--auto-key",
            "border",
            "--soft-matte",
            "--transparent-threshold",
            "12",
            "--opaque-threshold",
            "220",
            "--despill",
            "--edge-contract",
            str(args.edge_contract),
            "--force",
        ]
        subprocess.run(command, check=True, capture_output=True, text=True)
        with Image.open(source) as source_image, Image.open(output) as processed_image:
            processed = processed_image.convert("RGBA")
            if processed.size != source_image.size:
                raise SystemExit(f"前処理で寸法が変わりました: {state}")
            alpha = processed.getchannel("A")
            transparent = sum(1 for value in alpha.getdata() if value == 0)
            total = processed.width * processed.height
            corners = [
                alpha.getpixel((0, 0)),
                alpha.getpixel((processed.width - 1, 0)),
                alpha.getpixel((0, processed.height - 1)),
                alpha.getpixel((processed.width - 1, processed.height - 1)),
            ]
            if any(corner != 0 for corner in corners):
                raise SystemExit(f"透明化後も角が不透明です: {state} {corners}")
            results[state] = {
                "source": str(source),
                "output": str(output),
                "size": list(processed.size),
                "transparent_pixels": transparent,
                "transparent_ratio": round(transparent / total, 6),
                "alpha_extrema": list(alpha.getextrema()),
                "corner_alpha": corners,
                "edge_contract": args.edge_contract,
            }

    report = {"ok": True, "states": results}
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
