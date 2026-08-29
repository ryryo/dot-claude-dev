#!/usr/bin/env python3
"""Markdownの個別i2v計画を読み取り、Kamui生成を逐次実行する。"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PlanItem:
    number: int
    source_name: str
    duration: int
    task: str
    prompt: str


def section_code(markdown: str, heading: str) -> str:
    match = re.search(
        rf"^### {re.escape(heading)}\s*$.*?^```text\s*\n(.*?)^```\s*$",
        markdown,
        flags=re.MULTILINE | re.DOTALL,
    )
    if not match:
        raise ValueError(f"コードブロックがありません: {heading}")
    return match.group(1).strip()


def parse_plan(path: Path) -> list[PlanItem]:
    markdown = path.read_text(encoding="utf-8")
    prefix = section_code(markdown, "共通先頭")
    suffix = section_code(markdown, "共通末尾")
    headings = list(
        re.finditer(
            r"^### (?P<number>\d+)\. (?P<source>img-[^\n]+\.(?:png|jpg|jpeg|webp))\s*$",
            markdown,
            flags=re.MULTILINE | re.IGNORECASE,
        )
    )
    items = []
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(markdown)
        section = markdown[heading.end() : end]
        duration_match = re.search(r"^- 秒数: (\d+)秒\s*$", section, flags=re.MULTILINE)
        task_match = re.search(r"^- task: `([^`]+)`\s*$", section, flags=re.MULTILINE)
        prompt_match = re.search(
            r"^```text\s*\n(.*?)^```\s*$", section, flags=re.MULTILINE | re.DOTALL
        )
        if not duration_match or not task_match or not prompt_match:
            raise ValueError(f"項目の形式が不正です: {heading.group(0)}")
        duration = int(duration_match.group(1))
        prompt = "\n\n".join(
            (
                prefix.replace("[DURATION]", str(duration)),
                prompt_match.group(1).strip(),
                suffix,
            )
        )
        items.append(
            PlanItem(
                number=int(heading.group("number")),
                source_name=heading.group("source"),
                duration=duration,
                task=task_match.group(1),
                prompt=prompt,
            )
        )
    if not items:
        raise ValueError("実行項目がありません")
    if [item.number for item in items] != list(range(1, len(items) + 1)):
        raise ValueError("項目番号が連続していません")
    if len({item.task for item in items}) != len(items):
        raise ValueError("task名が重複しています")
    return items


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--model", default="seedance-2.0-fast")
    parser.add_argument("--resolution", default="720p")
    parser.add_argument("--start-at", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--comparison", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan_path = args.plan.resolve()
    source_dir = args.source_dir.resolve()
    project = args.project.resolve()
    all_items = parse_plan(plan_path)
    if not 1 <= args.start_at <= len(all_items):
        raise SystemExit(f"--start-atは1〜{len(all_items)}で指定してください")
    items = [item for item in all_items if item.number >= args.start_at]
    missing = [item.source_name for item in items if not (source_dir / item.source_name).is_file()]
    if missing:
        raise SystemExit(f"入力画像がありません: {', '.join(missing)}")

    generate = Path(__file__).resolve().parent / "generate.py"
    total_seconds = sum(item.duration for item in items)
    mode = "dry-run" if args.dry_run else "execute"
    print(
        f"plan={plan_path} items={len(items)}/{len(all_items)} total_seconds={total_seconds} "
        f"model={args.model} resolution={args.resolution} mode={mode}",
        flush=True,
    )
    for item in items:
        output_dir = (
            project
            / "output"
            / "i2v"
            / args.model
            / "note2-image-decoration"
            / item.task
        )
        print(
            f"\n=== [{item.number}/{len(all_items)}] {item.source_name} "
            f"{item.duration}s -> {item.task} ===",
            flush=True,
        )
        command = [
            sys.executable,
            str(generate),
            str(source_dir / item.source_name),
            "--project",
            str(project),
            "--task",
            item.task,
            "--output-dir",
            str(output_dir),
            "--mode",
            "loop",
            "--model",
            args.model,
            "--resolution",
            args.resolution,
            "--duration",
            str(item.duration),
            "--prompt",
            item.prompt,
        ]
        if args.comparison:
            command.append("--comparison")
        if args.dry_run:
            command.append("--dry-run")
        subprocess.run(command, check=True)
    print(f"\n全{len(items)}件を処理しました", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
