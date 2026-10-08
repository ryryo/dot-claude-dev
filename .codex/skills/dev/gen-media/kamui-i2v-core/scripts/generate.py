#!/usr/bin/env python3
"""Kamui MCPでi2v動画を逐次生成する共通スクリプト。"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import mimetypes
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

from kamui_i2v import (
    MCPClient,
    SKILL_ROOT,
    atomic_write_json,
    catalog_models,
    ensure_project_mcp,
    get_pass_key,
    JapaneseArgumentParser,
    probe_media,
    remove_audio,
    require_commands,
    sanitize_task,
    select_models,
    status_name,
    video_url,
)


DEFAULT_LOOP_PROMPT = """このWebサイト画像そのものから、完全につながる控えめな4秒ループを作成してください。カメラは完全に固定します。元の構図、アスペクト比、フレーミング、背景、タイポグラフィ、ロゴ、余白、オブジェクト位置、比率、色、輪郭、すべてのグラフィック要素を入力どおり厳密に保ってください。

既存の小さな環境要素だけを動かしてください。すべての動きは小さく、滑らかで、周期的で、Webサイト内容より目立たないものにします。テキスト、ロゴ、UI、人物、主要オブジェクト、レイアウト位置は完全に固定してください。

最初と最後のフレームは、入力画像と完全に一致させてください。すべての動きは自然に入り、自然に抜け、自然に反転し、最終フレーム前に元の状態へ完全に戻します。新しい物体、消える物体、カメラ移動、ズーム、パン、チルト、揺れ、視差、パース変更、切り抜き、再フレーミング、レイアウト変更、テキストアニメーション、テキスト変形、ロゴ変形、ちらつき、モーフィング、場面転換、音声は禁止です。"""

DEFAULT_MESSAGE_PROMPT = """この入力画像そのものを使って、短いimage-to-videoショットを作成してください。カメラは元の位置に完全に固定します。元の構図、フレーミング、遠近感、背景、色、光の向き、被写体の同一性、物体数、空間関係を保ってください。

被写体は同じポーズを保ったまま、明確で自然な動作を1つ行います。小さく親しみやすいうなずき、自然なまばたき1回、控えめな呼吸です。動きは読み取りやすく、制御され、控えめで、既存フレーム内に収めてください。

単一の連続ショットにしてください。カメラ移動、ズーム、パン、チルト、揺れ、再フレーミング、切り抜き、パース変更、場面転換、トランジション、新しい物体、消える物体、テキスト、字幕、ロゴ、UI、モーフィング、手の変形、余分な指、顔の歪み、過剰な動きは禁止です。"""


def image_data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def detect_aspect_ratio(path: Path) -> str | None:
    info = probe_media(path)
    width = int(info.get("width", 0))
    height = int(info.get("height", 0))
    if not width or not height:
        return None
    ratio = width / height
    options = {"21:9": 21 / 9, "16:9": 16 / 9, "4:3": 4 / 3, "1:1": 1, "3:4": 3 / 4, "9:16": 9 / 16}
    name, expected = min(options.items(), key=lambda item: abs(item[1] - ratio))
    return name if abs(expected - ratio) / expected <= 0.01 else None


def fingerprint(data: dict) -> str:
    encoded = json.dumps(data, ensure_ascii=False, sort_keys=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(url, timeout=300) as response, path.open("wb") as target:
        while chunk := response.read(1024 * 1024):
            target.write(chunk)


def update_manifest(task_dir: Path, task: str, source: Path, prompt: str) -> None:
    entries = []
    models = catalog_models()
    for video in sorted(task_dir.glob("*.mp4")):
        model = models.get(video.stem, {})
        entries.append(
            {
                "model": video.stem,
                "display_name": model.get("display_name", video.stem),
                "file": video.name,
                "media": probe_media(video),
            }
        )
    atomic_write_json(
        task_dir / "manifest.json",
        {
            "task": task,
            "source_image": str(source),
            "prompt": prompt,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "videos": entries,
        },
    )


def run_follow_up(script: str, task_dir: Path) -> None:
    subprocess.run([sys.executable, str(SKILL_ROOT / "scripts" / script), str(task_dir)], check=True)


def parse_args() -> argparse.Namespace:
    parser = JapaneseArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, nargs="?", help="入力画像のパス")
    parser.add_argument("--task", help="出力タスク名。小文字英数字とハイフンを使う")
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="対象プロジェクトのルート")
    parser.add_argument("--output-dir", type=Path, help="出力先ディレクトリ")
    parser.add_argument("--output-root", type=Path, help="出力ルート。配下にタスク名ディレクトリを作成する")
    parser.add_argument("--mode", choices=["loop", "message"], default="loop", help="生成モード")
    parser.add_argument("--model", action="append", dest="models", help="使用するモデルslug。複数指定可")
    parser.add_argument("--all-models", action="store_true", help="有効な全モデルを実行する")
    parser.add_argument("--duration", type=int, help="生成秒数")
    parser.add_argument("--resolution", help="解像度")
    parser.add_argument("--aspect-ratio", help="アスペクト比")
    parser.add_argument("--end-image", type=Path, help="終了フレーム用画像")
    prompt_group = parser.add_mutually_exclusive_group()
    prompt_group.add_argument("--prompt", help="直接指定するプロンプト")
    prompt_group.add_argument("--prompt-file", type=Path, help="プロンプトファイル")
    parser.add_argument("--comparison", action="store_true", help="比較HTMLを作成する")
    parser.add_argument("--no-setup-mcp", action="store_true", help="MCP設定の自動更新を省略する")
    parser.add_argument("--poll-interval", type=float, default=5.0, help="ポーリング間隔秒")
    parser.add_argument("--max-polls", type=int, default=240, help="最大ポーリング回数")
    parser.add_argument("--overwrite", action="store_true", help="既存結果を上書きして再生成する")
    parser.add_argument("--dry-run", action="store_true", help="生成せず実行計画だけ表示する")
    parser.add_argument("--list-models", action="store_true", help="モデル一覧を表示する")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.list_models:
        for model in sorted(catalog_models().values(), key=lambda item: item["price_usd_per_second"]):
            print(
                f"{model['slug']}\t{model['display_name']}\t"
                f"${model['price_usd_per_second']}/秒\t既定{model['default_resolution']}"
            )
        return 0
    if not args.source or not args.task:
        raise SystemExit("sourceと--taskが必要です")
    if args.output_dir and args.output_root:
        raise SystemExit("--output-dirと--output-rootは同時に指定できません")

    project = args.project.resolve()
    task = sanitize_task(args.task)
    output_root = args.output_root.resolve() if args.output_root else project / "output"
    task_dir = (
        args.output_dir.resolve() if args.output_dir else output_root / task
    )
    source = args.source.resolve()
    if not source.is_file():
        raise SystemExit(f"入力画像がありません: {source}")
    require_commands("ffmpeg", "ffprobe")

    if args.all_models:
        selected = [
            model
            for model in catalog_models().values()
            if model.get("enabled") and (args.mode != "loop" or model.get("supports_loop"))
        ]
    else:
        selected = select_models(args.models, args.mode)

    duration = args.duration or 4
    for model in selected:
        if not model["min_duration"] <= duration <= model["max_duration"]:
            raise SystemExit(
                f"{model['slug']}は{duration}秒に対応しません "
                f"({model['min_duration']}〜{model['max_duration']}秒)"
            )

    prompt = (
        args.prompt_file.read_text(encoding="utf-8").strip()
        if args.prompt_file
        else args.prompt or (DEFAULT_LOOP_PROMPT if args.mode == "loop" else DEFAULT_MESSAGE_PROMPT)
    )
    detected_ratio = args.aspect_ratio or detect_aspect_ratio(source)
    plan = {
        "project": str(project),
        "output_dir": str(task_dir),
        "task": task,
        "source": str(source),
        "mode": args.mode,
        "duration": duration,
        "detected_aspect_ratio": detected_ratio,
        "models": [
            {
                "slug": model["slug"],
                "resolution": args.resolution or model["default_resolution"],
                "estimated_cost_usd": round(model["price_usd_per_second"] * duration, 4),
            }
            for model in selected
        ],
        "execution": "直列",
    }
    print(json.dumps(plan, ensure_ascii=False, indent=2), flush=True)
    if args.dry_run:
        return 0

    if not args.no_setup_mcp:
        ensure_project_mcp(project, selected)
    pass_key = get_pass_key(project)
    if not pass_key:
        raise SystemExit(
            f"{project / '.env.local'}のKAMUI_CODE_PASS_KEYへキーを設定してください"
        )

    metadata_root = task_dir / "_metadata"
    assets_dir = task_dir / "_assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    source_copy = assets_dir / f"source-image{source.suffix.lower()}"
    shutil.copy2(source, source_copy)
    data_uri = image_data_uri(source)
    end_source = args.end_image.resolve() if args.end_image else source
    end_data_uri = image_data_uri(end_source)

    for index, model in enumerate(selected, start=1):
        slug = model["slug"]
        output_file = task_dir / f"{slug}.mp4"
        metadata_dir = metadata_root / slug
        metadata_dir.mkdir(parents=True, exist_ok=True)
        if output_file.exists() and not args.overwrite:
            print(f"[{index}/{len(selected)}] {slug}: 保存済みのためスキップ", flush=True)
            continue
        if args.overwrite:
            output_file.unlink(missing_ok=True)
            (metadata_dir / "submit-response.json").unlink(missing_ok=True)
            (metadata_dir / "result.json").unlink(missing_ok=True)

        parameters = model["parameters"]
        submit_args: dict[str, object] = {
            "prompt": prompt,
            parameters["image_field"]: data_uri,
            parameters["duration_field"]: str(duration),
        }
        if args.mode == "loop" or args.end_image:
            submit_args[parameters["end_image_field"]] = end_data_uri
        if parameters.get("audio_field"):
            submit_args[parameters["audio_field"]] = False
        resolution = args.resolution or model["default_resolution"]
        if parameters.get("resolution_field"):
            if resolution not in model["resolutions"]:
                raise SystemExit(f"{slug}は解像度{resolution}に対応しません")
            submit_args[parameters["resolution_field"]] = resolution
        if detected_ratio and parameters.get("aspect_ratio_field"):
            if detected_ratio in model["aspect_ratios"]:
                submit_args[parameters["aspect_ratio_field"]] = detected_ratio
            else:
                print(f"[{index}/{len(selected)}] {slug}: {detected_ratio}指定非対応のため比率を省略", flush=True)

        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        request_record = {
            "model": slug,
            "server_id": model["mcp"]["server_id"],
            "source_image": str(source),
            "source_sha256": source_hash,
            "prompt": prompt,
            "duration": duration,
            "resolution": resolution,
            "aspect_ratio": detected_ratio,
            "mode": args.mode,
        }
        request_record["fingerprint"] = fingerprint(request_record)
        request_path = metadata_dir / "request.json"
        if request_path.exists() and not args.overwrite:
            existing = json.loads(request_path.read_text(encoding="utf-8"))
            if existing.get("fingerprint") != request_record["fingerprint"]:
                raise SystemExit(f"{slug}の既存リクエスト条件と異なります。再生成には--overwriteを使ってください")
        else:
            atomic_write_json(request_path, request_record)

        print(f"[{index}/{len(selected)}] {slug}: MCP初期化", flush=True)
        client = MCPClient(model["mcp"]["url"], pass_key)
        client.initialize()
        submit_path = metadata_dir / "submit-response.json"
        if submit_path.exists():
            submit = json.loads(submit_path.read_text(encoding="utf-8"))
            request_id = submit.get("request_id")
            print(f"[{index}/{len(selected)}] {slug}: {request_id}を再開", flush=True)
        else:
            print(f"[{index}/{len(selected)}] {slug}: 送信", flush=True)
            submit = client.call(model["mcp"]["submit_tool"], submit_args)
            atomic_write_json(submit_path, submit)
            request_id = submit.get("request_id")
        if not request_id:
            raise RuntimeError(f"{slug}: request_idがありません: {submit}")

        final_status = None
        for poll in range(1, args.max_polls + 1):
            time.sleep(args.poll_interval)
            status = client.call(model["mcp"]["status_tool"], {"request_id": request_id})
            name = status_name(status)
            final_status = status
            if poll == 1 or poll % 6 == 0 or name not in {"IN_PROGRESS", "IN_QUEUE", "QUEUED", "PROCESSING"}:
                print(f"[{index}/{len(selected)}] {slug}: ポーリング {poll} {name}", flush=True)
            if name in {"COMPLETED", "SUCCEEDED", "SUCCESS", "DONE"}:
                break
            if name in {"FAILED", "ERROR", "CANCELLED", "CANCELED"}:
                raise RuntimeError(f"{slug}: 生成失敗: {status}")
        else:
            raise TimeoutError(f"{slug}: タイムアウト: {final_status}")

        result = client.call(model["mcp"]["result_tool"], {"request_id": request_id})
        atomic_write_json(metadata_dir / "result.json", result)
        raw_path = metadata_dir / "raw.mp4"
        download(video_url(result), raw_path)
        media = remove_audio(raw_path, output_file)
        print(
            f"[{index}/{len(selected)}] {slug}: 保存 {output_file} "
            f"({media.get('width')}x{media.get('height')}, {media.get('duration')}秒)",
            flush=True,
        )
        update_manifest(task_dir, task, source, prompt)

    update_manifest(task_dir, task, source, prompt)
    run_follow_up("inspect_videos.py", task_dir)
    if args.comparison or len(list(task_dir.glob("*.mp4"))) > 1:
        run_follow_up("build_comparison.py", task_dir)
    print(f"完了: {task_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
