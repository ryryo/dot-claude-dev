# 出典の更新と検査

取り込んだ基点とファイルの対応は [provenance.json](provenance.json)。元のpstackのCursor基点と分類は [UPSTREAM.json](UPSTREAM.json)に保持する。

上流から直接上書きせず、差分を固定した版と比較する。権限、対象、例外、終了条件を保って日本語の手順を更新し、変更パスと分類を記録する。プラグインの配布設定や個別のスキル入口を再導入しない。内部手順はreferences、実行補助はscripts、配置する設定はassetsに置く。

## 配置と実行補助の回帰検査

配布物のルートで実行する。

```sh
python3 scripts/validate.py
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 -m unittest discover -s scripts/maintenance -p 'test_*.py'
node --test scripts/pstack/poteto-mode/check-plan.test.mjs scripts/pstack/poteto-mode/worktree-audit.test.mjs scripts/pstack/show-me-your-work/log.test.mjs
```

TypeScript補助は `scripts/pstack/poteto-mode` でlockを固定して依存を用意し、`bun test orch watch-pr` と `bun run typecheck` を実行する。

文章は制約と条件を原文へ照合し、参照の存在を機械検査する。構造検査と配置テストの成功は、実際のエージェント起動やレビュー品質を証明しない。

## 実担当の試験

`python3 scripts/maintenance/smoke_agents.py --repo <project>` は、委譲と実行が許可され、新しいチャットで担当を検出できる環境に限って使う。呼び出し元の上位指示と、現在のCodex CLIの対応を確認する。配置済みを起動成功へ読み替えない。

二担当のレビュー品質を確認する場合は、許可された固定差分を両担当へ渡し、起動・読み取り専用・根拠の追跡・統合判断を確認する。過去の成功や模擬試験は現在の実動作の証拠にしない。
