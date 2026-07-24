#!/usr/bin/env python3
"""Magnific APIでローカル画像からi2v動画を生成する。"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


SKILL_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = SKILL_ROOT / "references" / "models.json"
API_BASE = "https://api.magnific.com"
API_KEY_NAME = "MAGNIFIC_API_KEY"
UPLOAD_REQUEST_PATH = "/v1/ai/uploads/request-url"
MAX_IMAGE_BYTES = 10 * 1024 * 1024


class JapaneseArgumentParser(argparse.ArgumentParser):
    def format_help(self) -> str:
        return (
            super()
            .format_help()
            .replace("usage:", "使い方:")
            .replace("positional arguments:", "位置引数:")
            .replace("options:", "オプション:")
            .replace("show this help message and exit", "このヘルプを表示して終了する")
        )


def read_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_api_key(project: Path) -> str:
    if value := os.environ.get(API_KEY_NAME):
        return value
    for env_path in (project / ".env.local", project / ".env", Path.cwd() / ".env.local", Path.cwd() / ".env"):
        if value := read_dotenv(env_path).get(API_KEY_NAME):
            return value
    raise RuntimeError(
        f"{API_KEY_NAME} がありません。プロジェクトの .env.local か環境変数に設定してください。"
    )


def load_catalog() -> dict[str, Any]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def catalog_models() -> dict[str, dict[str, Any]]:
    return {model["slug"]: model for model in load_catalog()["models"]}


def default_model() -> dict[str, Any]:
    catalog = load_catalog()
    fallback = catalog.get("defaults", {}).get("fallback_model")
    models = catalog_models()
    if isinstance(fallback, str) and fallback in models and models[fallback].get("api"):
        return models[fallback]
    candidates = [
        model
        for model in catalog["models"]
        if model.get("enabled") and model.get("supports_i2v") and model.get("api")
    ]
    if not candidates:
        raise RuntimeError("API対応の既定モデルがありません。")
    return candidates[0]


def select_models(slugs: list[str] | None, all_models: bool = False) -> list[dict[str, Any]]:
    models = catalog_models()
    if all_models:
        return [
            model
            for model in models.values()
            if model.get("enabled") and model.get("supports_i2v") and model.get("api")
        ]
    if not slugs:
        return [default_model()]
    selected = []
    for slug in slugs:
        if slug not in models:
            raise RuntimeError(f"未登録モデル: {slug}")
        model = models[slug]
        if not model.get("api"):
            raise RuntimeError(f"API非対応モデルです: {slug}")
        selected.append(model)
    return selected


def atomic_write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def request_json(
    method: str,
    url: str,
    *,
    api_key: str | None = None,
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    request_headers = dict(headers or {})
    payload = None
    if body is not None:
        payload = json.dumps(body).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    if api_key:
        request_headers["x-magnific-api-key"] = api_key
    request = Request(url, data=payload, headers=request_headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            data = response.read()
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {error.code}: {detail}") from error
    except URLError as error:
        raise RuntimeError(f"通信に失敗しました: {error.reason}") from error
    return json.loads(data.decode("utf-8"))


def put_bytes(url: str, headers: dict[str, str], path: Path) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise RuntimeError("upload_url がHTTPSではありません。")
    request = Request(url, data=path.read_bytes(), headers=headers, method="PUT")
    try:
        with urlopen(request, timeout=120) as response:
            response.read()
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"画像アップロード失敗 HTTP {error.code}: {detail}") from error
    except URLError as error:
        raise RuntimeError(f"画像アップロード通信失敗: {error.reason}") from error


def download_file(url: str, output: Path) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise RuntimeError("生成物URLがHTTPSではありません。")
    request = Request(url, method="GET")
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urlopen(request, timeout=300) as response:
            with tempfile.NamedTemporaryFile("wb", dir=output.parent, delete=False) as handle:
                shutil.copyfileobj(response, handle)
                temporary = Path(handle.name)
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"動画ダウンロード失敗 HTTP {error.code}: {detail}") from error
    except URLError as error:
        raise RuntimeError(f"動画ダウンロード通信失敗: {error.reason}") from error
    temporary.replace(output)


def detect_image_content_type(path: Path) -> str:
    content_type = mimetypes.guess_type(path.name)[0]
    if content_type == "image/jpg":
        content_type = "image/jpeg"
    if content_type not in {"image/png", "image/jpeg", "image/webp"}:
        raise RuntimeError("入力画像はPNG、JPEG、WebPのいずれかにしてください。")
    return content_type


def upload_image(api_key: str, source: Path) -> tuple[str, dict[str, Any]]:
    if not source.is_file():
        raise RuntimeError(f"入力画像がありません: {source}")
    if source.stat().st_size <= 0:
        raise RuntimeError("入力画像が空です。")
    if source.stat().st_size > MAX_IMAGE_BYTES:
        raise RuntimeError("入力画像は10MB以下にしてください。")

    content_type = detect_image_content_type(source)
    ticket = request_json(
        "POST",
        f"{API_BASE}{UPLOAD_REQUEST_PATH}",
        api_key=api_key,
        body={"files": [{"content_type": content_type}]},
    )
    file_info = (ticket.get("files") or [None])[0]
    if not isinstance(file_info, dict):
        raise RuntimeError("アップロードURL応答が不正です。")
    upload_url = file_info.get("upload_url")
    asset_url = file_info.get("asset_url")
    headers = file_info.get("headers") or {}
    if not isinstance(upload_url, str) or not isinstance(asset_url, str):
        raise RuntimeError("アップロードURL応答に必要なURLがありません。")
    if not isinstance(headers, dict):
        raise RuntimeError("アップロードURL応答のheadersが不正です。")
    if "Content-Type" not in headers:
        headers["Content-Type"] = content_type
    put_bytes(upload_url, {str(k): str(v) for k, v in headers.items()}, source)
    return asset_url, file_info


def task_detail(response: dict[str, Any]) -> dict[str, Any]:
    detail = response.get("data")
    if not isinstance(detail, dict):
        raise RuntimeError(f"タスク応答が不正です: {response}")
    return detail


def normalize_status(status: Any) -> str:
    value = str(status or "").upper()
    if value in {"CREATED", "PENDING", "PROCESSING", "IN_PROGRESS"}:
        return "in_progress"
    if value in {"COMPLETED", "SUCCESS", "SUCCEEDED"}:
        return "completed"
    if value in {"FAILED", "ERROR"}:
        return "failed"
    return value.lower() or "unknown"


def create_task(
    api_key: str,
    model: dict[str, Any],
    asset_url: str,
    prompt: str,
    args: argparse.Namespace,
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    api = model["api"]
    parameters = api.get("parameters", {})
    duration = int(args.duration or model.get("duration_values", [5])[0])
    if duration not in model.get("duration_values", []):
        raise RuntimeError(f"{model['slug']}は{duration}秒に対応しません。")
    aspect_ratio = args.aspect_ratio or model.get("default_aspect_ratio")
    aspect_ratio = normalize_aspect_ratio(model, aspect_ratio)
    create_path = create_path_for_model(model, args.resolution)

    body: dict[str, Any] = {
        "prompt": prompt
    }
    duration_field = parameters.get("duration_field")
    if duration_field:
        body[duration_field] = str(duration) if api.get("duration_type") == "string" else duration
    aspect_ratio_field = parameters.get("aspect_ratio_field")
    if aspect_ratio_field and aspect_ratio:
        body[aspect_ratio_field] = aspect_ratio
    audio_field = parameters.get("audio_field")
    if audio_field:
        body[audio_field] = args.audio
    if parameters.get("camera_fixed_field"):
        body[parameters["camera_fixed_field"]] = args.camera_fixed
    if parameters.get("seed_field") and args.seed is not None:
        body[parameters["seed_field"]] = args.seed
    if parameters.get("safety_field"):
        body[parameters["safety_field"]] = not args.disable_safety_checker

    image_parameter = parameters.get("image_field", "image")
    body[image_parameter] = asset_url
    end_image_field = parameters.get("end_image_field")
    if args.end_image_url and end_image_field:
        body[end_image_field] = args.end_image_url
    elif args.end_image_url and not end_image_field:
        raise RuntimeError(f"{model['slug']}は終了画像に対応していません。")
    negative_prompt_field = parameters.get("negative_prompt_field")
    if negative_prompt_field and args.negative_prompt:
        body[negative_prompt_field] = args.negative_prompt
    cfg_scale_field = parameters.get("cfg_scale_field")
    if cfg_scale_field:
        body[cfg_scale_field] = args.cfg_scale

    response = request_json(
        "POST",
        f"{API_BASE}{create_path}",
        api_key=api_key,
        body=body,
        timeout=60,
    )
    detail = task_detail(response)
    task_id = detail.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        raise RuntimeError(f"task_id がありません: {response}")
    return task_id, body, response


def create_path_for_model(model: dict[str, Any], resolution: str | None) -> str:
    api = model["api"]
    if "create_path" in api:
        return api["create_path"]
    paths = api.get("create_paths_by_resolution")
    if not isinstance(paths, dict):
        raise RuntimeError(f"{model['slug']}のcreate endpointが不正です。")
    selected_resolution = resolution or model.get("default_resolution")
    if selected_resolution not in paths:
        raise RuntimeError(
            f"{model['slug']}は解像度{selected_resolution}に対応しません。"
        )
    return paths[selected_resolution]


def normalize_aspect_ratio(model: dict[str, Any], value: str | None) -> str | None:
    if value is None:
        return None
    aliases = model.get("aspect_ratio_aliases", {})
    normalized = aliases.get(value, value)
    supported = model.get("aspect_ratios", [])
    if supported and normalized not in supported:
        raise RuntimeError(f"{model['slug']}はaspect_ratio={value}に対応しません。")
    if not supported:
        return None
    return normalized


def poll_task(
    api_key: str,
    model: dict[str, Any],
    task_id: str,
    interval: int,
    timeout_seconds: int,
) -> dict[str, Any]:
    api = model["api"]
    deadline = time.monotonic() + timeout_seconds
    poll_path = str(api["poll_path"]).format(task_id=task_id)
    while True:
        response = request_json(
            "GET",
            f"{API_BASE}{poll_path}",
            api_key=api_key,
            timeout=60,
        )
        detail = task_detail(response)
        status = normalize_status(detail.get("status"))
        print(f"{datetime.now().strftime('%H:%M:%S')} {task_id} {status}")
        if status == "completed":
            return response
        if status == "failed":
            raise RuntimeError(f"生成に失敗しました: {detail.get('error') or response}")
        if time.monotonic() > deadline:
            raise RuntimeError(f"生成待ちがタイムアウトしました: {task_id}")
        time.sleep(interval)


def prompt_from_args(args: argparse.Namespace) -> str:
    if args.prompt_file:
        return args.prompt_file.read_text(encoding="utf-8").strip()
    if args.prompt:
        return args.prompt.strip()
    raise RuntimeError("--prompt または --prompt-file が必要です。")


def run_ffprobe(path: Path) -> dict[str, Any] | None:
    if shutil.which("ffprobe") is None:
        return None
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=index,codec_type,codec_name,width,height,r_frame_rate",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def main() -> int:
    parser = JapaneseArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path, nargs="?", help="成果物を保存するプロジェクトルート")
    parser.add_argument("task", nargs="?", help="output/<task>/ に使うタスク名")
    parser.add_argument("source_image", type=Path, nargs="?", help="開始画像のパス")
    parser.add_argument("--prompt", help="動画生成プロンプト")
    parser.add_argument("--prompt-file", type=Path, help="動画生成プロンプトファイル")
    parser.add_argument("--model", action="append", dest="models", help="models.jsonのslug。複数指定可")
    parser.add_argument("--all-models", action="store_true", help="有効なAPIモデルをすべて直列実行する")
    parser.add_argument("--list-models", action="store_true", help="モデル一覧を表示する")
    parser.add_argument("--duration", type=int)
    parser.add_argument("--resolution", help="モデルが対応する解像度")
    parser.add_argument("--aspect-ratio")
    parser.add_argument("--audio", action="store_true", help="ネイティブ音声生成を有効にする")
    parser.add_argument("--camera-fixed", action="store_true", help="対応モデルで固定カメラ指定を送る")
    parser.add_argument("--seed", type=int, help="対応モデルのseed")
    parser.add_argument("--disable-safety-checker", action="store_true", help="対応モデルの安全フィルタを無効にする")
    parser.add_argument("--negative-prompt", default="blur, distort, and low quality")
    parser.add_argument("--cfg-scale", type=float, default=0.5)
    parser.add_argument("--end-image-url", help="終了フレーム画像URL")
    parser.add_argument("--dry-run", action="store_true", help="生成せず実行計画だけ表示する")
    parser.add_argument("--poll-interval", type=int, default=15)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    args = parser.parse_args()

    if args.list_models:
        for model in select_models(None, all_models=True):
            print(
                f"{model['slug']}\t{model['display_name']}\t"
                f"既定={model.get('default_resolution')}\t秒={model.get('duration_values')}"
            )
        return 0
    if not args.project_root or not args.task or not args.source_image:
        raise SystemExit("project_root、task、source_imageが必要です。")
    project = args.project_root.resolve()
    task_dir = project / "output" / args.task
    selected_models = select_models(args.models, all_models=args.all_models)
    prompt = prompt_from_args(args)
    plan = {
        "project": str(project),
        "task_dir": str(task_dir),
        "source_image": str(args.source_image.resolve()),
        "duration": args.duration,
        "resolution": args.resolution,
        "aspect_ratio": args.aspect_ratio,
        "models": [
            {
                "slug": model["slug"],
                "display_name": model["display_name"],
                "resolution": args.resolution or model.get("default_resolution"),
                "endpoint": create_path_for_model(model, args.resolution),
            }
            for model in selected_models
        ],
    }
    print(json.dumps(plan, ensure_ascii=False, indent=2), flush=True)
    if args.dry_run:
        return 0
    api_key = load_api_key(project)

    task_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = task_dir / "_assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    source_copy = assets_dir / f"source-image{args.source_image.suffix.lower()}"
    shutil.copy2(args.source_image, source_copy)

    print("開始画像をMagnific uploadsへアップロードします")
    asset_url, upload_response = upload_image(api_key, source_copy)
    for index, model in enumerate(selected_models, start=1):
        print(f"[{index}/{len(selected_models)}] {model['slug']} タスク作成")
        task_id, create_body, create_response = create_task(
            api_key, model, asset_url, prompt, args
        )
        final_response = poll_task(
            api_key, model, task_id, args.poll_interval, args.timeout_seconds
        )
        generated = task_detail(final_response).get("generated")
        if not isinstance(generated, list) or not generated or not isinstance(generated[0], str):
            raise RuntimeError(f"生成物URLがありません: {final_response}")

        output_path = task_dir / f"{model['slug']}.mp4"
        print(f"[{index}/{len(selected_models)}] 生成MP4をダウンロードします")
        download_file(generated[0], output_path)
        probe = run_ffprobe(output_path)

        metadata = {
            "provider": "Magnific API",
            "model": model["display_name"],
            "model_slug": model["slug"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source_image": str(source_copy),
            "prompt": prompt,
            "request": create_body,
            "upload": {
                "asset_url": asset_url,
                "file_id": upload_response.get("file_id"),
                "asset_url_expires_in": upload_response.get("asset_url_expires_in"),
            },
            "task_id": task_id,
            "create_response": create_response,
            "final_response": final_response,
            "output_url": generated[0],
            "output_path": str(output_path),
            "ffprobe": probe,
        }
        atomic_write_json(task_dir / "_metadata" / model["slug"] / "request.json", metadata)
        print(f"保存しました: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
