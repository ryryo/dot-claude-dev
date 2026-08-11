#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("validate_story_ledger.py")
SPEC = importlib.util.spec_from_file_location("validate_story_ledger", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


VALID_STORY = """\
# User Stories

## US-01: 中断した作業を再開できる

- 状態: `todo`
- 優先度: `P0`
- 活動: 制作を再開する

### きっかけ

編集途中で離席した利用者から、戻ると入力が消えていると相談があった。

### 利用者の目的

保存済みの作業へ戻りたい。

### 対象範囲

保存と再読込を対象にする。

### 通常導線

一覧から対象を開く。

### 例外・復旧

再読込後も同じ状態へ戻る。

### 受け入れ条件

- [ ] `US-01-01` 保存済みの状態を再読込できる。
  - 例: project-aを再読込すると入力「春の告知」が表示される。

### 検証

- 自動テスト: 未実施
- 実画面: 未実施
- 実サービス: 対象外
- 未確認条件: `US-01-01`
- 証拠: なし
"""

VALID_EVIDENCE = """\
# US-01 再開 Evidence

- 検証日: 2026-08-11
- 基準commit: abc1234
- 対象ストーリー: US-01
- 対象条件: US-01-01
- 関連PLAN: 260811_resume.md
- 実行環境: local

## 入力と外部サービス

- 外部サービス／model: 対象外
- 費用区分と承認: 対象外

## Journey結果

- normal: pass
- exception: 対象外
- failure／cancel／retry: 対象外
- reload／再起動／再訪: pass

## 判定

- 結果: pass
- 未確認事項: なし
"""


class StoryLedgerValidationTest(unittest.TestCase):
    def make_root(self, ledger: str) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        (root / "docs" / "PLAN").mkdir(parents=True)
        (root / "docs" / "EVIDENCE").mkdir(parents=True)
        (root / "docs" / "USER_STORIES.md").write_text(ledger, encoding="utf-8")
        return temporary, root

    def issues_for(self, ledger: str) -> list[str]:
        temporary, root = self.make_root(ledger)
        self.addCleanup(temporary.cleanup)
        return MODULE.collect_issues(root / "docs" / "USER_STORIES.md")

    def test_accepts_an_empty_template(self) -> None:
        self.assertEqual(
            self.issues_for("# User Stories\n\n```md\n## US-XX: title\n```\n"),
            [],
        )

    def test_accepts_a_valid_story_and_known_plan_references(self) -> None:
        temporary, root = self.make_root(VALID_STORY)
        self.addCleanup(temporary.cleanup)
        (root / "docs" / "PLAN" / "260811_resume.md").write_text(
            "# Plan\n\n対象: US-01\n条件: US-01-01\n", encoding="utf-8"
        )
        self.assertEqual(MODULE.collect_issues(root / "docs" / "USER_STORIES.md"), [])

    def test_accepts_a_project_local_ledger_and_sibling_plan_references(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        scope = Path(temporary.name) / "docs" / "PLAN" / "migration"
        (scope / "EVIDENCE").mkdir(parents=True)
        ledger = scope / "USER_STORIES.md"
        ledger.write_text(VALID_STORY, encoding="utf-8")
        (scope / "260811_resume.md").write_text(
            "# Plan\n\n対象: US-01\n条件: US-01-01\n", encoding="utf-8"
        )
        self.assertEqual(MODULE.collect_issues(ledger), [])

    def test_accepts_verified_when_every_condition_is_checked(self) -> None:
        verified = (
            VALID_STORY.replace("`todo`", "`verified`")
            .replace("- [ ] `US-01-01`", "- [x] `US-01-01`")
            .replace("- 未確認条件: `US-01-01`", "- 未確認条件: なし")
        )
        self.assertEqual(self.issues_for(verified), [])

    def test_rejects_duplicate_story_ids(self) -> None:
        issues = self.issues_for(VALID_STORY + "\n" + VALID_STORY.split("\n", 2)[2])
        self.assertTrue(any("duplicate story ID US-01" in issue for issue in issues))

    def test_rejects_invalid_status_priority_and_missing_section(self) -> None:
        invalid = VALID_STORY.replace("`todo`", "`complete`").replace("`P0`", "`urgent`")
        invalid = invalid.replace("### 例外・復旧\n\n再読込後も同じ状態へ戻る。\n\n", "")
        issues = self.issues_for(invalid)
        self.assertTrue(any("invalid 状態" in issue for issue in issues))
        self.assertTrue(any("invalid 優先度" in issue for issue in issues))
        self.assertTrue(any("missing section: 例外・復旧" in issue for issue in issues))

    def test_rejects_a_story_without_きっかけ(self) -> None:
        invalid = VALID_STORY.replace(
            "### きっかけ\n\n編集途中で離席した利用者から、戻ると入力が消えていると相談があった。\n\n",
            "",
        )
        issues = self.issues_for(invalid)
        self.assertTrue(any("missing section: きっかけ" in issue for issue in issues))

    def test_rejects_missing_or_malformed_condition_ids(self) -> None:
        missing = VALID_STORY.replace("`US-01-01` 保存済み", "保存済み", 1)
        malformed = VALID_STORY.replace("`US-01-01` 保存済み", "`US-01-A` 保存済み", 1)
        self.assertTrue(any("condition ID" in issue for issue in self.issues_for(missing)))
        self.assertTrue(any("condition ID" in issue for issue in self.issues_for(malformed)))

    def test_rejects_duplicate_and_wrong_prefix_condition_ids(self) -> None:
        duplicate = VALID_STORY.replace(
            "### 検証",
            "- [ ] `US-01-01` 別の端末でも再読込できる。\n"
            "  - 例: project-aを別タブで開くと同じ入力が表示される。\n\n"
            "### 検証",
        )
        wrong_prefix = VALID_STORY.replace("US-01-01", "US-02-01")
        self.assertTrue(any("duplicate condition ID US-01-01" in issue for issue in self.issues_for(duplicate)))
        self.assertTrue(any("does not belong to US-01" in issue for issue in self.issues_for(wrong_prefix)))

    def test_rejects_missing_or_empty_examples(self) -> None:
        missing = VALID_STORY.replace(
            "  - 例: project-aを再読込すると入力「春の告知」が表示される。\n", ""
        )
        empty = VALID_STORY.replace(
            "  - 例: project-aを再読込すると入力「春の告知」が表示される。",
            "  - 例: ",
        )
        self.assertTrue(any("concrete example" in issue for issue in self.issues_for(missing)))
        self.assertTrue(any("concrete example" in issue for issue in self.issues_for(empty)))

    def test_rejects_checked_condition_with_unresolved_example(self) -> None:
        invalid = (
            VALID_STORY.replace("- [ ] `US-01-01`", "- [x] `US-01-01`")
            .replace("project-aを再読込すると入力「春の告知」が表示される。", "未確定（復元する項目）")
            .replace("- 未確認条件: `US-01-01`", "- 未確認条件: なし")
        )
        self.assertTrue(any("unresolved example" in issue for issue in self.issues_for(invalid)))

    def test_rejects_missing_extra_or_duplicate_unverified_ids(self) -> None:
        missing = VALID_STORY.replace("- 未確認条件: `US-01-01`", "- 未確認条件: なし")
        extra = VALID_STORY.replace(
            "- 未確認条件: `US-01-01`", "- 未確認条件: `US-01-01`, `US-01-02`"
        )
        duplicate = VALID_STORY.replace(
            "- 未確認条件: `US-01-01`", "- 未確認条件: `US-01-01`, `US-01-01`"
        )
        self.assertTrue(any("未確認条件 does not match" in issue for issue in self.issues_for(missing)))
        self.assertTrue(any("未確認条件 does not match" in issue for issue in self.issues_for(extra)))
        self.assertTrue(any("duplicate 未確認条件" in issue for issue in self.issues_for(duplicate)))

    def test_rejects_verified_story_with_unchecked_condition(self) -> None:
        invalid = VALID_STORY.replace("`todo`", "`verified`")
        self.assertTrue(any("verified but has unchecked" in issue for issue in self.issues_for(invalid)))

    def test_rejects_unknown_story_and_condition_references(self) -> None:
        temporary, root = self.make_root(VALID_STORY)
        self.addCleanup(temporary.cleanup)
        (root / "docs" / "PLAN" / "260811_unknown.md").write_text(
            "対象: US-02\n条件: US-01-02\n", encoding="utf-8"
        )
        (root / "docs" / "EVIDENCE" / "260811_US-03_unknown.md").write_text(
            "対象: US-03\n条件: US-01-03\n", encoding="utf-8"
        )
        issues = MODULE.collect_issues(root / "docs" / "USER_STORIES.md")
        self.assertTrue(any("unknown story ID US-02" in issue for issue in issues))
        self.assertTrue(any("unknown story ID US-03" in issue for issue in issues))
        self.assertTrue(any("unknown condition ID US-01-02" in issue for issue in issues))
        self.assertTrue(any("unknown condition ID US-01-03" in issue for issue in issues))

    def test_accepts_complete_evidence_metadata(self) -> None:
        temporary, root = self.make_root(VALID_STORY)
        self.addCleanup(temporary.cleanup)
        (root / "docs" / "EVIDENCE" / "260811_US-01_resume.md").write_text(
            VALID_EVIDENCE, encoding="utf-8"
        )
        self.assertEqual(MODULE.collect_issues(root / "docs" / "USER_STORIES.md"), [])

    def test_rejects_missing_evidence_metadata(self) -> None:
        temporary, root = self.make_root(VALID_STORY)
        self.addCleanup(temporary.cleanup)
        (root / "docs" / "EVIDENCE" / "260811_US-01_resume.md").write_text(
            VALID_EVIDENCE.replace("- 基準commit: abc1234\n", ""), encoding="utf-8"
        )
        issues = MODULE.collect_issues(root / "docs" / "USER_STORIES.md")
        self.assertTrue(any("missing evidence field: 基準commit" in issue for issue in issues))

    def test_rejects_empty_acceptance_and_verification_sections(self) -> None:
        invalid = VALID_STORY.replace(
            "- [ ] `US-01-01` 保存済みの状態を再読込できる。\n"
            "  - 例: project-aを再読込すると入力「春の告知」が表示される。",
            "受け入れ条件は未記入。",
        )
        invalid = invalid.replace(
            "- 自動テスト: 未実施\n"
            "- 実画面: 未実施\n"
            "- 実サービス: 対象外\n"
            "- 未確認条件: `US-01-01`\n"
            "- 証拠: なし",
            "検証項目は未記入。",
        )
        issues = self.issues_for(invalid)
        self.assertTrue(any("acceptance checkbox" in issue for issue in issues))
        self.assertTrue(any("verification field: 自動テスト" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
