#!/usr/bin/env python3
"""Codexペットを仮パッケージし、承認後にバックアップ付きで正式反映する。"""

from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_run_summary(raw_path: str | None, **values: object) -> None:
    if not raw_path:
        return
    path = Path(raw_path).expanduser().resolve()
    current = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    current.update(values)
    write_json(path, current)


def stage(args: argparse.Namespace) -> None:
    spritesheet = Path(args.spritesheet).expanduser().resolve()
    candidate = Path(args.candidate_dir).expanduser().resolve()
    if candidate.exists():
        if not args.force:
            raise SystemExit(f"候補ディレクトリが存在します: {candidate}（上書きには--force）")
        shutil.rmtree(candidate)
    candidate.mkdir(parents=True)
    shutil.copy2(spritesheet, candidate / "spritesheet.webp")
    write_json(
        candidate / "pet.json",
        {
            "id": args.pet_id,
            "displayName": args.display_name,
            "description": args.description,
            "spritesheetPath": "spritesheet.webp",
        },
    )
    update_run_summary(
        args.run_summary,
        acceptance_status="provisional",
        candidate_package=str(candidate),
        in_app_accepted=False,
    )
    write_json(
        candidate / "acceptance.json",
        {
            "status": "provisional",
            "pet_id": args.pet_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "in_app_accepted": False,
        },
    )
    print(json.dumps({"ok": True, "status": "provisional", "candidate": str(candidate)}, ensure_ascii=False))


def preview(args: argparse.Namespace) -> None:
    candidate = Path(args.candidate_dir).expanduser().resolve()
    manifest = json.loads((candidate / "pet.json").read_text(encoding="utf-8"))
    original_id = manifest["id"]
    preview_id = args.preview_id or f"{original_id}-candidate"
    codex_home = Path(args.codex_home or os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser().resolve()
    pets_root = codex_home / "pets"
    destination = pets_root / preview_id
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    staging = pets_root / f".{preview_id}.staging-{timestamp}"
    staging.mkdir(parents=True, exist_ok=False)
    preview_manifest = dict(manifest)
    preview_manifest["id"] = preview_id
    preview_manifest["displayName"] = f"{manifest['displayName']} (Candidate)"
    write_json(staging / "pet.json", preview_manifest)
    shutil.copy2(candidate / "spritesheet.webp", staging / "spritesheet.webp")
    replaced = None
    if destination.exists():
        replaced = pets_root / ".backups" / f"{preview_id}--{timestamp}"
        replaced.parent.mkdir(parents=True, exist_ok=True)
        os.replace(destination, replaced)
    os.replace(staging, destination)
    write_json(
        candidate / "acceptance.json",
        {
            "status": "preview_installed",
            "pet_id": original_id,
            "preview_id": preview_id,
            "preview_destination": str(destination),
            "installed_at": datetime.now(timezone.utc).isoformat(),
            "in_app_accepted": False,
        },
    )
    update_run_summary(
        args.run_summary,
        acceptance_status="preview_installed",
        candidate_package=str(candidate),
        preview_destination=str(destination),
        in_app_accepted=False,
    )
    print(
        json.dumps(
            {
                "ok": True,
                "status": "preview_installed",
                "preview_id": preview_id,
                "destination": str(destination),
                "replaced": str(replaced) if replaced else None,
            },
            ensure_ascii=False,
        )
    )


def promote(args: argparse.Namespace) -> None:
    if not args.confirm_in_app_accepted:
        raise SystemExit("正式反映には--confirm-in-app-acceptedが必要です")
    candidate = Path(args.candidate_dir).expanduser().resolve()
    manifest = json.loads((candidate / "pet.json").read_text(encoding="utf-8"))
    acceptance_path = candidate / "acceptance.json"
    prior_acceptance = json.loads(acceptance_path.read_text(encoding="utf-8")) if acceptance_path.is_file() else {}
    if prior_acceptance.get("status") != "preview_installed":
        raise SystemExit("正式反映前にpreviewサブコマンドで候補をアプリへ一時配置してください")
    pet_id = manifest["id"]
    codex_home = Path(args.codex_home or os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser().resolve()
    pets_root = codex_home / "pets"
    destination = pets_root / pet_id
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = pets_root / ".backups" / f"{pet_id}--{timestamp}"
    staging = pets_root / f".{pet_id}.staging-{timestamp}"
    staging.mkdir(parents=True, exist_ok=False)
    shutil.copy2(candidate / "pet.json", staging / "pet.json")
    shutil.copy2(candidate / "spritesheet.webp", staging / "spritesheet.webp")
    backup_created = False
    try:
        if destination.exists():
            backup.parent.mkdir(parents=True, exist_ok=True)
            os.replace(destination, backup)
            backup_created = True
        os.replace(staging, destination)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        if backup_created and not destination.exists():
            os.replace(backup, destination)
        raise
    write_json(
        acceptance_path,
        {
            "status": "in_app_accepted",
            "pet_id": pet_id,
            "accepted_at": datetime.now(timezone.utc).isoformat(),
            "in_app_accepted": True,
            "destination": str(destination),
            "backup": str(backup) if backup_created else None,
        },
    )
    if not args.keep_preview and prior_acceptance.get("preview_destination"):
        preview_destination = Path(prior_acceptance["preview_destination"]).expanduser().resolve()
        if preview_destination.parent == pets_root and preview_destination != destination and preview_destination.is_dir():
            shutil.rmtree(preview_destination)
    update_run_summary(
        args.run_summary,
        acceptance_status="in_app_accepted",
        candidate_package=str(candidate),
        in_app_accepted=True,
        package=str(destination),
        backup=str(backup) if backup_created else None,
    )
    print(
        json.dumps(
            {
                "ok": True,
                "status": "in_app_accepted",
                "destination": str(destination),
                "backup": str(backup) if backup_created else None,
            },
            ensure_ascii=False,
        )
    )


def rollback(args: argparse.Namespace) -> None:
    codex_home = Path(args.codex_home or os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser().resolve()
    pets_root = codex_home / "pets"
    destination = pets_root / args.pet_id
    backups_root = pets_root / ".backups"
    if args.backup_dir:
        backup = Path(args.backup_dir).expanduser().resolve()
    else:
        candidates = sorted(backups_root.glob(f"{args.pet_id}--*"), reverse=True)
        if not candidates:
            raise SystemExit(f"バックアップがありません: {args.pet_id}")
        backup = candidates[0]
    if not backup.is_dir():
        raise SystemExit(f"バックアップがありません: {backup}")
    replaced = None
    if destination.exists():
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        replaced = backups_root / f"{args.pet_id}--replaced--{timestamp}"
        os.replace(destination, replaced)
    os.replace(backup, destination)
    update_run_summary(
        args.run_summary,
        acceptance_status="rolled_back",
        package=str(destination),
        replaced=str(replaced) if replaced else None,
    )
    print(json.dumps({"ok": True, "destination": str(destination), "replaced": str(replaced) if replaced else None}, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    stage_parser = subparsers.add_parser("stage")
    stage_parser.add_argument("--spritesheet", required=True)
    stage_parser.add_argument("--candidate-dir", required=True)
    stage_parser.add_argument("--pet-id", required=True)
    stage_parser.add_argument("--display-name", required=True)
    stage_parser.add_argument("--description", required=True)
    stage_parser.add_argument("--force", action="store_true")
    stage_parser.add_argument("--run-summary")
    stage_parser.set_defaults(func=stage)

    preview_parser = subparsers.add_parser("preview")
    preview_parser.add_argument("--candidate-dir", required=True)
    preview_parser.add_argument("--codex-home")
    preview_parser.add_argument("--preview-id")
    preview_parser.add_argument("--run-summary")
    preview_parser.set_defaults(func=preview)

    promote_parser = subparsers.add_parser("promote")
    promote_parser.add_argument("--candidate-dir", required=True)
    promote_parser.add_argument("--codex-home")
    promote_parser.add_argument("--confirm-in-app-accepted", action="store_true")
    promote_parser.add_argument("--keep-preview", action="store_true")
    promote_parser.add_argument("--run-summary")
    promote_parser.set_defaults(func=promote)

    rollback_parser = subparsers.add_parser("rollback")
    rollback_parser.add_argument("--pet-id", required=True)
    rollback_parser.add_argument("--codex-home")
    rollback_parser.add_argument("--backup-dir")
    rollback_parser.add_argument("--run-summary")
    rollback_parser.set_defaults(func=rollback)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
