# プロンプト雛形

Cursor CLI worker に渡す prompt の雛形。実際に使う前に、対象 repository の絶対パス、HEAD、scope、read / write scope、検証コマンドへ置き換える。

## 新規監査プロンプト

```text
Task Summary:
R01-A1 - <scope name> のフロントエンド新規監査

あなたはこの repository 内で動く Cursor CLI worker agent です。

Worker:
cursor-cli-agent

Workspace:
<absolute workspace path>

Task ID:
R01-A1

Goal:
指定範囲を read-only で新規監査し、挙動変更なしで直す価値があるフロントエンドリファクタリング対象だけを報告してください。

Expected baseline:
- `git rev-parse --short HEAD` は `<expected short sha>` であること。
- `git status --short` は空であること。
- 一致しない場合は `BLOCKED: baseline mismatch` とだけ報告して停止してください。

Read first:
- <absolute workspace path>/.codex/skills/dev/front-end-refactor-loop/references/front-end-design-patterns/decision-matrix.md
- <必要な個別 reference>
- <対象ファイルまたはディレクトリ>

Read scope:
- <対象範囲>
- 対象画面に直接関係する shared hooks / stores / utilities

Forbidden:
- ファイル編集
- commit、push、PR 作成、branch 切替
- このスキル配下以外の既存スキル資産の参照
- 対象範囲外の一般論だけの報告

監査観点:
- container / presentational boundary
- pure selectors / hooks
- render hot path
- stable dependencies
- derived state / recomputation
- module boundary
- lazy loading / code splitting
- 不要な再計算、不要な再描画、不要な large object state

出力形式:
- 変更する価値のある問題がない場合は、正確に `NO_FINDINGS` と書き、何を調査したかを短く添える。
- 問題がある場合は、影響度順に findings を列挙する。
- 各 finding には file path、line reference、なぜ問題か、挙動維持で直せる refactor target を含める。
- 各 finding に `performance_sensitive: yes/no` を付ける。
- `performance_sensitive: yes` の場合は、影響し得るコストを render count / commit duration / recomputation / bundle size / canvas or image sync work / list or grid update / queue or timer churn のどれかで短く示す。
```

## 実装委譲プロンプト

```text
Task Summary:
R01-I1 - <scope name> の挙動維持リファクタリング実装

あなたはこの repository 内で動く Cursor CLI worker agent です。

Worker:
cursor-cli-agent

Workspace:
<absolute workspace path>

Task ID:
R01-I1

Goal:
main Codex が採用済みの finding だけを、挙動変更なしで実装してください。

Read first:
- <absolute workspace path>/.codex/skills/dev/front-end-refactor-loop/references/front-end-design-patterns/decision-matrix.md
- <必要な個別 reference>
- <対象ファイル>
- <関連 test>

Write scope:
- Allowed:
  - <allowed path>
- Forbidden:
  - docs/PLAN/**
  - .codex/skills/**
  - 明示的に許可された task report 以外の .codex/tmp/**
  - 明示的に許可されていない package-lock.json
  - allowed write scope 外のファイル

Constraints:
- 機能、UI 仕様、公開 API、データ形式、保存形式、URL、イベント順、外部 API 呼び出しを変えない。
- stage、commit、push、PR 作成、branch 切替、planning / progress file 更新をしない。
- 関係ない既存変更を戻さない。
- 大きな抽象化や依存追加をしない。
- 対象 repository の既存規約に合わせる。

Verification:
- Run: <focused command>
- 実行できない場合は、理由と代わりに確認した内容を具体的に報告してください。

Final report:
- TASK_ID: R01-I1
- 変更したファイル
- 変更内容の要約
- 実行した検証と結果
- main Codex に残した作業
```
