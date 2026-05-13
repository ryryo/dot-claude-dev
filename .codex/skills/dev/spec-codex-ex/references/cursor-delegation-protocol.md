# Cursor Delegation Protocol

Cursor Agent へ委任する場合は、期待成果物、編集範囲、禁止事項、検証、報告形式を明示した詳細な作業契約を渡す。

## Availability Check

`spec-codex-run` 実行時に、Cursor Agent を使うかを都度判断する。

1. ユーザーが明示的に不使用を選んだ場合は使わない。
2. 次を実行して利用可否を確認する。
   ```bash
   cursor-agent about
   cursor-agent models
   cursor-agent -p --mode ask --output-format text --workspace <workspace> "Respond with exactly: ok"
   ```
3. 未ログイン、契約なし、モデルなし、最小実行失敗の場合は Codex 単独にフォールバックする。
4. 利用する場合の基本形:
   ```bash
   cursor-agent -p --mode ask --output-format text --workspace <workspace> --model <model> "<prompt>"
   ```
5. 調査だけなら `--mode ask` または `--mode plan` を使う。編集を委任する場合は write scope と禁止事項を明示する。

## Suitable Tasks

- 純粋関数、validator、formatter、schema、単体テスト。
- 小さな adapter や helper。
- 局所的な docs 調査。
- write scope が明確で、他 Gate や共通 state に干渉しない作業。
- 検証コマンドが明確な作業。

## Do Not Delegate

- `docs/PLAN` の状態更新。
- `tasks.json` 更新。
- `spec.md` generated 領域同期。
- Gate PASS 判定。
- 最終統合、commit、push。
- routing、共通 state、export pipeline、実ブラウザ最終検証など高結合な作業。

## Prompt Requirements

Cursor 向けプロンプトには必ず含める。

- 作業場所。
- 対象 Gate / Todo / AC。
- 読むべき参照ファイル。
- 変更してよいファイルまたはディレクトリ。
- 触ってはいけないファイル。
- 既存変更を戻さないこと。
- 検証コマンド。
- 完了報告フォーマット。

実装結論を過剰に誘導しない。期待する結果、制約、検証条件を渡し、具体的な局所実装は担当エージェントに任せる。

## tasks.json Hints

Todo に optional `delegation` を付けてよい。

```json
{
  "delegation": {
    "eligible": true,
    "agent": "cursor-agent",
    "mode": "ask",
    "writeScope": ["src/validators/email.ts", "src/validators/email.test.ts"],
    "verification": ["pnpm test src/validators/email.test.ts"],
    "promptProfile": "detailed-worker"
  }
}
```

このフィールドは dashboard 互換のため optional とし、存在しなくても `spec-codex-run` は通常 v3 として実行する。
