#!/usr/bin/env python3
"""Kamui i2vスキルの共通処理。外部Pythonパッケージは使用しない。"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


SKILL_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = SKILL_ROOT / "references" / "models.json"
PASS_KEY_NAME = "KAMUI_CODE_PASS_KEY"


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


def compact_json_for_error(data: Any) -> str:
    def scrub(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: scrub(item) for key, item in value.items()}
        if isinstance(value, list):
            return [scrub(item) for item in value]
        if isinstance(value, str):
            if value.startswith("data:image/"):
                return value[:64] + "...<data-uri-omitted>"
            if len(value) > 1200:
                return value[:1200] + "...<truncated>"
        return value

    return json.dumps(scrub(data), ensure_ascii=False, indent=2)


def load_catalog() -> dict[str, Any]:
    with CATALOG_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def catalog_models() -> dict[str, dict[str, Any]]:
    return {model["slug"]: model for model in load_catalog()["models"]}


def select_models(slugs: list[str] | None, mode: str = "loop") -> list[dict[str, Any]]:
    models = catalog_models()
    if slugs:
        missing = [slug for slug in slugs if slug not in models]
        if missing:
            raise ValueError(f"未登録モデル: {', '.join(missing)}")
        selected = [models[slug] for slug in slugs]
    else:
        candidates = [
            model
            for model in models.values()
            if model.get("enabled") and (mode != "loop" or model.get("supports_loop"))
        ]
        if not candidates:
            raise ValueError("既定条件を満たすモデルがありません")
        selected = [
            min(
                candidates,
                key=lambda model: (
                    float(model.get("price_usd_per_second", float("inf"))),
                    model["slug"],
                ),
            )
        ]

    if mode == "loop":
        unsupported = [model["slug"] for model in selected if not model.get("supports_loop")]
        if unsupported:
            raise ValueError(f"ループ非対応モデル: {', '.join(unsupported)}")
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


def get_pass_key(project: Path) -> str | None:
    return os.environ.get(PASS_KEY_NAME) or read_dotenv(project / ".env.local").get(
        PASS_KEY_NAME
    )


def source_mcp_config_path() -> Path | None:
    seen: set[Path] = set()
    for root in (Path.cwd(), SKILL_ROOT):
        for parent in (root, *root.parents):
            if parent in seen:
                continue
            seen.add(parent)
            candidate = parent / ".mcp.json"
            if candidate.exists():
                return candidate
    return None


def ensure_project_mcp(project: Path, models: list[dict[str, Any]]) -> dict[str, Any]:
    project.mkdir(parents=True, exist_ok=True)
    config_path = project / ".mcp.json"
    seeded_from: str | None = None
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(f"{config_path}が不正なJSONです: {error}") from error
    elif source_path := source_mcp_config_path():
        try:
            config = json.loads(source_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(f"{source_path}が不正なJSONです: {error}") from error
        if not isinstance(config, dict):
            raise ValueError(f"{source_path}のルートはオブジェクトである必要があります")
        seeded_from = str(source_path)
    else:
        config = {}
    servers = config.setdefault("mcpServers", {})
    if not isinstance(servers, dict):
        raise ValueError(f"{config_path}のmcpServersはオブジェクトである必要があります")

    added: list[str] = []
    for model in models:
        mcp = model["mcp"]
        servers[mcp["server_id"]] = {
            "type": "http",
            "url": mcp["url"],
            "description": mcp["description"],
            "headers": {"KAMUI-CODE-PASS": "${KAMUI_CODE_PASS_KEY}"},
        }
        added.append(mcp["server_id"])
    atomic_write_json(config_path, config)

    env_path = project / ".env.local"
    if not env_path.exists():
        env_path.write_text(
            "# Kamui Code MCP認証キー（コミット禁止）\n"
            "KAMUI_CODE_PASS_KEY=\n",
            encoding="utf-8",
        )
    elif PASS_KEY_NAME not in read_dotenv(env_path):
        with env_path.open("a", encoding="utf-8") as handle:
            if env_path.stat().st_size:
                handle.write("\n")
            handle.write("# Kamui Code MCP認証キー（コミット禁止）\n")
            handle.write("KAMUI_CODE_PASS_KEY=\n")

    gitignore_path = project / ".gitignore"
    existing = gitignore_path.read_text(encoding="utf-8") if gitignore_path.exists() else ""
    ignored = any(
        line.strip() in {".env.local", "/.env.local", ".env.*.local"}
        for line in existing.splitlines()
    )
    if not ignored:
        with gitignore_path.open("a", encoding="utf-8") as handle:
            if existing and not existing.endswith("\n"):
                handle.write("\n")
            handle.write("\n# ローカル秘密情報\n.env.local\n")

    return {
        "config": str(config_path),
        "seeded_from": seeded_from,
        "servers": added,
        "env": str(env_path),
    }


def require_commands(*commands: str) -> None:
    missing = [command for command in commands if shutil.which(command) is None]
    if missing:
        raise RuntimeError(f"必要なコマンドがありません: {', '.join(missing)}")


def run_json(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(completed.stdout)


def probe_media(path: Path) -> dict[str, Any]:
    data = run_json(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=index,codec_type,codec_name,width,height,r_frame_rate,nb_frames,pix_fmt:format=duration,size",
            "-of",
            "json",
            str(path),
        ]
    )
    video = next(
        (stream for stream in data.get("streams", []) if stream.get("codec_type") == "video"),
        {},
    )
    audio_count = sum(
        1 for stream in data.get("streams", []) if stream.get("codec_type") == "audio"
    )
    output = dict(video)
    output.update(data.get("format", {}))
    output["audio_streams"] = audio_count
    return output


def remove_audio(raw_path: Path, output_path: Path) -> dict[str, Any]:
    info = probe_media(raw_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if info["audio_streams"] == 0:
        raw_path.replace(output_path)
    else:
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(raw_path),
                "-map",
                "0:v:0",
                "-an",
                "-c:v",
                "copy",
                "-movflags",
                "+faststart",
                str(output_path),
            ],
            check=True,
        )
        raw_path.unlink()
    final_info = probe_media(output_path)
    if final_info["audio_streams"]:
        raise RuntimeError(f"音声除去に失敗しました: {output_path}")
    return final_info


def sanitize_task(value: str) -> str:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", value):
        raise ValueError("taskは小文字英数字で始まる80文字以内のハイフン区切りにしてください")
    return value


class MCPClient:
    def __init__(self, endpoint: str, pass_key: str):
        self.endpoint = endpoint
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "KAMUI-CODE-PASS": pass_key,
        }
        self.call_id = 0

    def _post(self, payload: dict[str, Any], timeout: int = 180) -> dict[str, Any]:
        request = Request(
            self.endpoint,
            data=json.dumps(payload).encode(),
            headers=self.headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                session_id = response.headers.get("Mcp-Session-Id")
                if session_id:
                    self.headers["Mcp-Session-Id"] = session_id
                body = response.read().decode()
                content_type = response.headers.get("Content-Type", "")
        except HTTPError as error:
            body = error.read().decode(errors="replace")
            raise RuntimeError(f"MCP HTTP {error.code}: {body[:1000]}") from error
        except URLError as error:
            raise RuntimeError(f"MCP接続エラー: {error}") from error

        if "text/event-stream" in content_type:
            data_lines = [line[5:].strip() for line in body.splitlines() if line.startswith("data:")]
            if not data_lines:
                raise RuntimeError("MCP SSE応答にdataがありません")
            body = data_lines[-1]
        return json.loads(body)

    def initialize(self) -> None:
        self.call_id += 1
        response = self._post(
            {
                "jsonrpc": "2.0",
                "id": self.call_id,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "kamui-i2v-core", "version": "1.0.0"},
                },
            }
        )
        if "error" in response:
            raise RuntimeError(response["error"])

    def call(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self.call_id += 1
        response = self._post(
            {
                "jsonrpc": "2.0",
                "id": self.call_id,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments},
            }
        )
        if "error" in response:
            raise RuntimeError(response["error"])
        result = response.get("result", {})
        if result.get("isError"):
            raise RuntimeError(result)
        for content in result.get("content", []):
            if content.get("type") != "text":
                continue
            text = content.get("text", "")
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"text": text}
        return result


def status_name(status: dict[str, Any]) -> str:
    return str(status.get("status", status.get("state", "unknown"))).upper()


def video_url(result: dict[str, Any]) -> str:
    video = result.get("video")
    if isinstance(video, dict) and video.get("url"):
        return str(video["url"])
    raise ValueError(f"結果に動画URLがありません: {compact_json_for_error(result)}")
