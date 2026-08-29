# Delegation Brief Template

Cursor Agent または subagent に渡すプロンプトは、次の形を基本にする。

```text
作業場所:
<absolute workspace path>

対象:
- PLAN: <absolute path to docs/PLAN/.../tasks.json>
- Gate: <Gate id and title>
- Todo: <Todo id and title>
- Acceptance Criteria: <AC ids>

まず読む:
- <absolute path to relevant tasks.json>
- <absolute path to spec.md if useful>
- <reference implementation or source files>

重要:
- tasks.json が正です。spec.md は補助または生成物として扱ってください。
- docs/PLAN 配下の tasks.json と spec.md は編集しないでください。
- 自分に割り当てられたファイルだけを変更してください。
- 他エージェントの変更、既存未コミット変更、対象外ディレクトリを戻さないでください。
- commit / push はしないでください。

目的:
<what this agent should complete>

担当ファイル:
- <path>
- <path>

範囲外:
- <path or behavior>
- docs/PLAN の更新
- Gate PASS 判定
- 最終統合
- commit / push

完了条件:
- <verification command>
- <expected observable result>

完了時の報告:
- 変更ファイル
- 対応した Gate/Todo/AC
- 実行した検証コマンドと結果
- 残課題または未検証事項
```

## Rules

- 実在確認したパスだけを書く。
- write scope を重複させない。重複が避けられない場合は委任しない。
- 高複雑度の統合作業を低複雑度タスクとして渡さない。
- 検証コマンドが存在するか事前に確認する。
- 委任結果を受けた後の統合、AC 更新、review、PASS 判定は main Codex が行う。
