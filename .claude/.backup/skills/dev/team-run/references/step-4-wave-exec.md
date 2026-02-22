# Step 4: Wave 実行ループ

## 前提

- Step 3b のゲート通過済み（全タスク登録済み）
- `$WORKTREE_PATH` が有効

## DO

各 Wave について繰り返す:

### 4-1: Teammate スポーン

- **実装系ロール**: `Read("references/teammate-spawn-protocol.md")` に従って Teammate をスポーン（run_in_background: true, cwd: $WORKTREE_PATH）
- **レビュー系ロール**: Task(subagent_type: "Explore", model: "opus") で Subagent 実行

### 4-2: Wave 完了判定

- 全タスク TaskList で `completed`
- 各 outputs がファイルとして存在
- worktree にコミットあり

### 4-3: 次 Wave or 完了

完了 → 次 Wave（4-1 に戻る）/ 全 Wave 完了 → Step 5 へ

## エラー時

`Read("references/error-handling.md")` に従って対応

## ゲート

全 Wave の全タスクが `completed`
