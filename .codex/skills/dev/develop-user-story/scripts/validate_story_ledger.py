#!/usr/bin/env python3
"""Validate a Markdown user-story ledger and its PLAN/EVIDENCE references."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


STORY_HEADING = re.compile(r"^## (US-\d{2,}):\s+\S.*$", re.MULTILINE)
STORY_REFERENCE = re.compile(r"\bUS-\d{2,}\b")
CONDITION_REFERENCE = re.compile(r"\bUS-\d{2,}-\d{2,}\b")
STATUS = re.compile(r"^- 状態: `(todo|doing|implemented|verified|blocked)`\s*$", re.MULTILINE)
PRIORITY = re.compile(r"^- 優先度: `(P0|P1|P2)`\s*$", re.MULTILINE)
CHECKBOX = re.compile(r"^- \[[ xX]\]\s+\S", re.MULTILINE)
CHECKBOX_LINE = re.compile(r"^- \[(?P<mark>[ xX])\]\s+(?P<header>.*)$")
CONDITION_HEADER = re.compile(
    r"^`(?P<condition_id>US-\d{2,}-\d{2,})`\s+(?P<description>\S.*)$"
)
EXAMPLE_LINE = re.compile(r"^\s+- 例:\s*(?P<example>.*)$")
REQUIRED_SECTIONS = (
    "きっかけ",
    "利用者の目的",
    "対象範囲",
    "通常導線",
    "例外・復旧",
    "受け入れ条件",
    "検証",
)
REQUIRED_VERIFICATION_FIELDS = (
    "自動テスト",
    "実画面",
    "実サービス",
    "未確認条件",
    "証拠",
)
REQUIRED_EVIDENCE_FIELDS = (
    "検証日",
    "基準commit",
    "対象ストーリー",
    "対象条件",
    "関連PLAN",
    "実行環境",
    "外部サービス／model",
    "費用区分と承認",
    "normal",
    "exception",
    "failure／cancel／retry",
    "reload／再起動／再訪",
    "結果",
    "未確認事項",
)


@dataclass(frozen=True)
class StoryBlock:
    story_id: str
    line: int
    body: str


@dataclass(frozen=True)
class ConditionItem:
    condition_id: str | None
    checked: bool
    line: int
    examples: tuple[str, ...]


def strip_fenced_code(text: str) -> str:
    """Remove fenced examples while preserving line numbers."""
    result: list[str] = []
    fence: str | None = None
    for line in text.splitlines(keepends=True):
        marker = line.lstrip()[:3]
        if fence is None and marker in {"```", "~~~"}:
            fence = marker
            result.append("\n" if line.endswith("\n") else "")
        elif fence is not None:
            if marker == fence:
                fence = None
            result.append("\n" if line.endswith("\n") else "")
        else:
            result.append(line)
    return "".join(result)


def parse_story_blocks(text: str) -> list[StoryBlock]:
    clean = strip_fenced_code(text)
    matches = list(STORY_HEADING.finditer(clean))
    blocks: list[StoryBlock] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(clean)
        blocks.append(
            StoryBlock(
                story_id=match.group(1),
                line=clean.count("\n", 0, match.start()) + 1,
                body=clean[match.end() : end],
            )
        )
    return blocks


def section_body(story_body: str, title: str) -> str:
    pattern = re.compile(
        rf"^### {re.escape(title)}\s*$\n(?P<body>.*?)(?=^### |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(story_body)
    return match.group("body") if match else ""


def parse_condition_items(acceptance: str, block_line: int) -> list[ConditionItem]:
    lines = acceptance.splitlines()
    starts = [index for index, line in enumerate(lines) if CHECKBOX_LINE.match(line)]
    items: list[ConditionItem] = []
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(lines)
        checkbox = CHECKBOX_LINE.match(lines[start])
        assert checkbox is not None
        header = CONDITION_HEADER.match(checkbox.group("header"))
        examples = tuple(
            match.group("example").strip()
            for line in lines[start + 1 : end]
            if (match := EXAMPLE_LINE.match(line)) is not None
            and match.group("example").strip()
        )
        items.append(
            ConditionItem(
                condition_id=header.group("condition_id") if header else None,
                checked=checkbox.group("mark").lower() == "x",
                line=block_line + start,
                examples=examples,
            )
        )
    return items


def unverified_field(verification: str) -> str | None:
    match = re.search(r"^- 未確認条件:\s*(\S.*)$", verification, re.MULTILINE)
    return match.group(1).strip() if match else None


def validate_story_block(
    block: StoryBlock, ledger: Path
) -> tuple[list[str], list[ConditionItem]]:
    prefix = f"{ledger}:{block.line}: {block.story_id}"
    issues: list[str] = []
    status_match = STATUS.search(block.body)
    if not status_match:
        issues.append(f"{prefix} has a missing or invalid 状態 field")
    if not PRIORITY.search(block.body):
        issues.append(f"{prefix} has a missing or invalid 優先度 field")

    for title in REQUIRED_SECTIONS:
        if not re.search(rf"^### {re.escape(title)}\s*$", block.body, re.MULTILINE):
            issues.append(f"{prefix} is missing section: {title}")

    acceptance = section_body(block.body, "受け入れ条件")
    if not CHECKBOX.search(acceptance):
        issues.append(f"{prefix} must contain at least one acceptance checkbox")
    conditions = parse_condition_items(acceptance, block.line)
    for condition in conditions:
        condition_prefix = f"{ledger}:{condition.line}: {block.story_id}"
        if condition.condition_id is None:
            issues.append(
                f"{condition_prefix} acceptance checkbox must start with a valid condition ID"
            )
            continue
        if not condition.condition_id.startswith(f"{block.story_id}-"):
            issues.append(
                f"{condition_prefix} condition ID {condition.condition_id} "
                f"does not belong to {block.story_id}"
            )
        if not condition.examples:
            issues.append(
                f"{condition_prefix} {condition.condition_id} must contain a concrete example"
            )
        if condition.checked and any("未確定" in example for example in condition.examples):
            issues.append(
                f"{condition_prefix} {condition.condition_id} is checked with an unresolved example"
            )

    verification = section_body(block.body, "検証")
    for field in REQUIRED_VERIFICATION_FIELDS:
        if not re.search(
            rf"^- {re.escape(field)}:\s*\S.*$", verification, re.MULTILINE
        ):
            issues.append(f"{prefix} is missing verification field: {field}")

    valid_conditions = [item for item in conditions if item.condition_id is not None]
    unchecked = {
        item.condition_id for item in valid_conditions if not item.checked
    }
    pending_value = unverified_field(verification)
    pending_ids: list[str] = []
    if pending_value is not None:
        pending_ids = CONDITION_REFERENCE.findall(pending_value)
        if len(pending_ids) != len(set(pending_ids)):
            issues.append(f"{prefix} has duplicate 未確認条件 IDs")
        if pending_value != "なし" and not pending_ids:
            issues.append(f"{prefix} has an invalid 未確認条件 field")
        if set(pending_ids) != unchecked:
            issues.append(
                f"{prefix} 未確認条件 does not match unchecked acceptance conditions "
                f"(expected {sorted(unchecked)}, found {sorted(set(pending_ids))})"
            )

    if status_match and status_match.group(1) == "verified" and unchecked:
        issues.append(
            f"{prefix} is verified but has unchecked acceptance conditions: {sorted(unchecked)}"
        )
    return issues, conditions


def evidence_directory(ledger: Path) -> Path:
    return ledger.parent / "EVIDENCE"


def evidence_files(ledger: Path) -> list[Path]:
    directory = evidence_directory(ledger)
    if not directory.is_dir():
        return []
    return sorted(
        path
        for path in directory.rglob("*.md")
        if not path.name.startswith("_")
    )


def referenced_markdown_files(ledger: Path) -> list[Path]:
    base = ledger.parent
    plan_directory = base / "PLAN"
    files: set[Path] = set(evidence_files(ledger))
    if plan_directory.is_dir():
        files.update(plan_directory.rglob("*.md"))
    else:
        files.update(base.glob("*.md"))
    return sorted(
        path
        for path in files
        if path != ledger and not path.name.startswith("_")
    )


def validate_evidence_metadata(path: Path) -> list[str]:
    text = strip_fenced_code(path.read_text(encoding="utf-8"))
    issues: list[str] = []
    for field in REQUIRED_EVIDENCE_FIELDS:
        if not re.search(rf"^- {re.escape(field)}:\s*\S.*$", text, re.MULTILINE):
            issues.append(f"{path}: missing evidence field: {field}")
    return issues


def collect_issues(ledger: Path) -> list[str]:
    ledger = ledger.resolve()
    if not ledger.is_file():
        return [f"{ledger}: missing user-story ledger"]

    text = ledger.read_text(encoding="utf-8")
    blocks = parse_story_blocks(text)
    issues: list[str] = []
    seen: dict[str, int] = {}
    condition_locations: dict[str, int] = {}
    for block in blocks:
        if block.story_id in seen:
            issues.append(
                f"{ledger}:{block.line}: duplicate story ID {block.story_id} "
                f"(first declared at line {seen[block.story_id]})"
            )
        else:
            seen[block.story_id] = block.line
        block_issues, conditions = validate_story_block(block, ledger)
        issues.extend(block_issues)
        for condition in conditions:
            if condition.condition_id is None:
                continue
            if condition.condition_id in condition_locations:
                issues.append(
                    f"{ledger}:{condition.line}: duplicate condition ID "
                    f"{condition.condition_id} (first declared at line "
                    f"{condition_locations[condition.condition_id]})"
                )
            else:
                condition_locations[condition.condition_id] = condition.line

    known_ids = set(seen)
    known_condition_ids = set(condition_locations)
    for path in referenced_markdown_files(ledger):
        clean = strip_fenced_code(path.read_text(encoding="utf-8"))
        for reference in sorted(set(STORY_REFERENCE.findall(clean)) - known_ids):
            issues.append(f"{path}: references unknown story ID {reference}")
        for reference in sorted(
            set(CONDITION_REFERENCE.findall(clean)) - known_condition_ids
        ):
            issues.append(f"{path}: references unknown condition ID {reference}")
    for path in evidence_files(ledger):
        issues.extend(validate_evidence_metadata(path))
    return issues


def main() -> int:
    if len(sys.argv) != 2:
        print(
            "usage: validate_story_ledger.py <path/to/USER_STORIES.md>",
            file=sys.stderr,
        )
        return 2
    ledger = Path(sys.argv[1]).resolve()
    issues = collect_issues(ledger)
    if issues:
        for issue in issues:
            print(issue, file=sys.stderr)
        return 1

    story_count = len(parse_story_blocks(ledger.read_text(encoding="utf-8")))
    print(f"story-ledger: ok ({story_count} stories; ledger={ledger})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
