#!/usr/bin/env python3
"""pstack-thermosの配置を診断し、管理対象だけを適用する。"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
AGENT_FILES = (
    "poteto-agent.toml", "comment-sicko.toml", "pstack-skeptic.toml",
    "pstack-architect.toml", "pstack-minimalist.toml",
    "thermos-correctness.toml", "thermos-quality.toml",
)
SCHEMA = "pstack-thermos-install-v1"
LEGACY_SCHEMA = "pstack-ja-install-v1"
LINK = "skills/pstack-thermos"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected(root: Path, include_skill: bool = True) -> dict[str, dict[str, str]]:
    entries = {LINK: {"kind": "symlink", "target": str(root)}} if include_skill else {}
    for filename in AGENT_FILES:
        source = root / "assets/agents" / filename
        agent = tomllib.loads(source.read_text())
        if not all(agent.get(key) for key in ("name", "description", "developer_instructions")):
            raise ValueError(f"担当設定に必要な項目がありません: {source}")
        if filename != "poteto-agent.toml" and agent.get("sandbox_mode") != "read-only":
            raise ValueError(f"レビュー担当が読み取り専用ではありません: {source}")
        entries[f"agents/{filename}"] = {"kind": "file", "sha256": digest(source)}
    return entries


def matches(path: Path, item: dict[str, str]) -> bool:
    if item["kind"] == "symlink":
        return path.is_symlink() and os.readlink(path) == item["target"]
    return path.is_file() and not path.is_symlink() and digest(path) == item["sha256"]


def receipt_path(destination: Path) -> Path:
    return destination / "pstack-thermos/install.json"


def read_receipt(destination: Path, root: Path) -> dict | None:
    path = receipt_path(destination)
    legacy_path = destination / "pstack/install.json"
    if (path.exists() or path.is_symlink()) and (legacy_path.exists() or legacy_path.is_symlink()):
        raise ValueError("新旧の管理記録が両方あります。配置元と管理対象を確認してください。")
    legacy = not (path.exists() or path.is_symlink()) and (legacy_path.exists() or legacy_path.is_symlink())
    if legacy:
        path = legacy_path
    if not path.exists() and not path.is_symlink():
        return None
    if path.is_symlink():
        raise ValueError(f"管理記録がリンクになっています: {path}")
    receipt = json.loads(path.read_text())
    source = root.with_name("pstack") if legacy else root
    if receipt.get("schema") != (LEGACY_SCHEMA if legacy else SCHEMA) or receipt.get("source") != str(source):
        raise ValueError(f"管理記録の形式または配布元が一致しません: {path}")
    entries = receipt.get("entries")
    desired = expected(root)
    if legacy:
        desired = {key: item for key, item in desired.items() if key not in
                   (LINK, "agents/thermos-correctness.toml", "agents/thermos-quality.toml")}
        desired["skills/pstack"] = {"kind": "symlink", "target": str(source)}
    allowed = (set(desired),) if legacy else (set(desired), set(desired) - {LINK})
    if not isinstance(entries, dict) or set(entries) not in allowed:
        raise ValueError(f"管理対象の一覧が一致しません: {path}")
    for relative, item in entries.items():
        if not isinstance(item, dict) or item.get("kind") not in ("file", "symlink"):
            raise ValueError(f"管理記録の内容が不正です: {path}")
        if item["kind"] != desired[relative]["kind"]:
            raise ValueError(f"管理対象の種類が一致しません: {path}")
        if item["kind"] == "file" and not re.fullmatch(r"[0-9a-f]{64}", str(item.get("sha256", ""))):
            raise ValueError(f"管理記録にハッシュがありません: {path}")
        if item["kind"] == "symlink" and item.get("target") != str(source):
            raise ValueError(f"管理記録のリンク先が一致しません: {path}")
    return {**receipt, "legacy": legacy}


def reused_skill(destination: Path, root: Path, receipt: dict | None) -> Path | None:
    """共有入口は参照するだけにし、補助が所有する個別入口とは区別する。"""
    shared = destination / "skills/dev/pstack-thermos"
    direct = destination / LINK
    for path in (shared, direct):
        if path == direct and receipt and LINK in receipt["entries"]:
            continue
        if path.is_dir() and (path / "SKILL.md").is_file():
            if path.resolve() == root.resolve():
                return path
    return None


def safe_destination(destination: Path, manage_skills: bool = True) -> None:
    paths = (destination, destination / "agents",
             destination / "pstack", destination / "pstack-thermos")
    for path in paths:
        if path.is_symlink() or (path.exists() and not path.is_dir()):
            raise ValueError(f"配置先が通常のディレクトリではありません: {path}")
    skills = destination / "skills"
    if (manage_skills and skills.is_symlink()) or (skills.exists() and not skills.is_dir()):
        raise ValueError(f"配置先が通常のディレクトリではありません: {skills}")


def plan(destination: Path, root: Path, action: str) -> tuple[dict, list[dict], dict | None]:
    safe_destination(destination, manage_skills=False)
    receipt = read_receipt(destination, root)
    shared = destination / "skills/dev/pstack-thermos"
    if action != "uninstall" and (shared / "SKILL.md").is_file() and shared.resolve() != root.resolve():
        raise ValueError(f"同名の共有スキルが別の配布元を参照しています: {shared}")
    desired = expected(root, include_skill=reused_skill(destination, root, receipt) is None)
    # Uninstall touches only recorded entries, even if the shared skill disappeared.
    paths = dict.fromkeys(receipt["entries"] if action == "uninstall" and receipt else
                          [*desired, *(receipt["entries"] if receipt else {})])
    safe_destination(destination, manage_skills=any(path.startswith("skills/") for path in paths))
    rows = []
    for relative in paths:
        new = desired.get(relative)
        path = destination / relative
        old = receipt["entries"].get(relative) if receipt else None
        exists = path.exists() or path.is_symlink()
        if not exists:
            state = "不足" if receipt else "未設定"
        elif not old:
            state = "競合（管理外の設定）"
        elif not matches(path, old):
            state = "競合（配置後に変更あり）"
        elif new is None:
            state = "管理対象の旧入口（取り外し対象）"
        elif matches(path, new):
            state = "配置済み"
        else:
            state = "更新あり"
        rows.append({"path": str(path), "relative": relative, "state": state})
    if action == "update" and receipt is None:
        raise ValueError("更新対象の管理記録がありません。初回は install を使ってください。")
    if action == "uninstall" and receipt is None:
        raise ValueError("管理記録がないため取り外しません。")
    if action == "install" and receipt and receipt["legacy"]:
        raise ValueError("旧pstackの管理記録があります。checkで診断し、updateで統合版へ移してください。")
    return desired, rows, receipt


def trust_state(project: Path | None) -> str:
    if project is None:
        return "ユーザー共通の配置。各プロジェクトで信頼を確認してください。"
    home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    config = home / "config.toml"
    if not config.exists():
        return "未確認。Codexの画面で対象プロジェクトの信頼を確認してください。"
    try:
        data = tomllib.loads(config.read_text())
    except (OSError, tomllib.TOMLDecodeError):
        return "設定ファイルを読み取れません。Codexの画面で確認してください。"
    trusted = data.get("projects", {}).get(str(project), {}).get("trust_level")
    return "設定上は信頼済み" if trusted == "trusted" else "設定上は信頼を確認できません。Codexの画面で確認してください。"


def apply(destination: Path, root: Path, action: str) -> list[dict]:
    desired, rows, receipt = plan(destination, root, action)
    conflicts = [row["path"] for row in rows if row["state"].startswith("競合")]
    if conflicts:
        raise ValueError("既存設定を保持して停止します:\n" + "\n".join(conflicts))
    destination.mkdir(parents=True, exist_ok=True)
    lock = destination / ".pstack-ja-setup.lock"
    try:
        handle = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise ValueError(f"別の設定処理が実行中です。残ったロックは実行状況を確認してください: {lock}")
    os.close(handle)
    backups: dict[Path, bytes | str | None] = {}
    temporary: set[Path] = set()
    record_path = receipt_path(destination)
    try:
        desired, rows, receipt = plan(destination, root, action)
        if any(row["state"].startswith("競合") for row in rows):
            raise ValueError("診断後に配置先が変更されたため停止します。")
        legacy_record = destination / "pstack/install.json" if receipt and receipt["legacy"] else None
        targets = [destination / row["relative"] for row in rows] + [record_path]
        if legacy_record:
            targets.append(legacy_record)
        for path in targets:
            backups[path] = os.readlink(path) if path.is_symlink() else path.read_bytes() if path.exists() else None
        if action == "uninstall":
            for path in targets:
                if path.exists() or path.is_symlink():
                    path.unlink()
        else:
            for row in rows:
                if row["relative"] not in desired:
                    path = destination / row["relative"]
                    if path.exists() or path.is_symlink():
                        path.unlink()
            for relative, item in desired.items():
                path = destination / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                if matches(path, item):
                    continue
                if item["kind"] == "symlink":
                    path.symlink_to(root, target_is_directory=True)
                else:
                    temp = path.with_name(path.name + ".pstack-tmp")
                    with temp.open("xb") as stream:
                        temporary.add(temp)
                        stream.write((root / "assets" / relative).read_bytes())
                    temp.replace(path)
            record_path.parent.mkdir(parents=True, exist_ok=True)
            # Reused shared paths are deliberately absent from the ownership record.
            record = {"schema": SCHEMA, "source": str(root), "entries": desired}
            temp = record_path.with_suffix(".tmp")
            with temp.open("x") as stream:
                temporary.add(temp)
                json.dump(record, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
            temp.replace(record_path)
            if legacy_record:
                legacy_record.unlink()
    except Exception:
        for path, data in backups.items():
            if path.exists() or path.is_symlink():
                if path.is_dir() and not path.is_symlink():
                    continue
                path.unlink()
            if isinstance(data, str):
                path.symlink_to(data, target_is_directory=True)
            elif isinstance(data, bytes):
                path.write_bytes(data)
        raise
    finally:
        for temp in temporary:
            if temp.exists():
                temp.unlink()
        lock.unlink()
    if action == "uninstall":
        return [{**row, "state": "取り外し済み"} for row in rows]
    return plan(destination, root, "check")[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="pstack-thermosの診断・初回配置・更新・取り外し")
    parser.add_argument("action", choices=("check", "install", "update", "uninstall"))
    parser.add_argument("--scope", choices=("project", "user"), default="project")
    parser.add_argument("--project", type=Path)
    parser.add_argument("--json", action="store_true", help="診断結果をJSONで出力する")
    args = parser.parse_args()
    if args.scope == "project":
        if args.project is None or not args.project.is_dir():
            parser.error("存在する対象ディレクトリを --project で指定してください。")
        project = args.project.resolve()
        destination = project / ".codex"
    else:
        if args.project is not None:
            parser.error("--scope user と --project は同時に指定できません。")
        project = None
        destination = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).absolute()
    try:
        if args.action == "check":
            _, rows, _ = plan(destination, ROOT, args.action)
        else:
            rows = apply(destination, ROOT, args.action)
        report = {"action": args.action, "destination": str(destination), "entries": rows,
                  "trust": trust_state(project), "codex_cli": bool(shutil.which("codex")),
                  "runtime_verification": "未実施。新しいチャットで7担当の検出・起動を確認してください。"}
        receipt = read_receipt(destination, ROOT)
        shared = reused_skill(destination, ROOT, receipt)
        if shared:
            report["reused_skill"] = str(shared)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(f"対象: {destination}")
            for row in rows:
                print(f"{row['state']}: {row['path']}")
            if shared:
                print(f"既存のスキル入口を再利用（管理対象外）: {shared}")
            if args.action != "check":
                print("取り外しました。" if args.action == "uninstall" else "配置を適用しました。")
            print(report["trust"])
            print(report["runtime_verification"])
        return 1 if any(row["state"].startswith("競合") for row in rows) else 0
    except (OSError, ValueError, tomllib.TOMLDecodeError) as error:
        print(f"pstack-thermosの設定を適用できません: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
