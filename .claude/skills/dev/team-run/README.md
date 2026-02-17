# プロジェクト側 Hooks 設定ガイド

`dev:team-run` で Agent Teams を使う際、プロジェクト側で品質ゲート hooks を設定すると、Teammate の成果物品質を自動で担保できる。

## 設定場所

プロジェクトルートの `.claude/settings.json` に追加する。

## 設定例

### JavaScript / TypeScript

```json
{
  "hooks": {
    "TaskCompleted": [
      {
        "type": "command",
        "command": "npm run lint && npm run build && npm test"
      }
    ],
    "TeammateIdle": [
      {
        "type": "command",
        "command": "npm run lint && npm run build"
      }
    ]
  }
}
```

### PHP (Laravel)

```json
{
  "hooks": {
    "TaskCompleted": [
      {
        "type": "command",
        "command": "composer run lint && php artisan test"
      }
    ],
    "TeammateIdle": [
      {
        "type": "command",
        "command": "composer run lint"
      }
    ]
  }
}
```

### Python

```json
{
  "hooks": {
    "TaskCompleted": [
      {
        "type": "command",
        "command": "ruff check . && pytest"
      }
    ],
    "TeammateIdle": [
      {
        "type": "command",
        "command": "ruff check ."
      }
    ]
  }
}
```

## hooks の動作

| hook | 発火タイミング | exit code 0 | exit code 2 |
|------|---------------|-------------|-------------|
| **TaskCompleted** | Teammate がタスクを「完了」にする直前 | 完了を許可 | 完了をブロック → Teammate が修正を継続 |
| **TeammateIdle** | Teammate がアイドルになる直前 | アイドルを許可 | アイドルをブロック → Teammate が修正を継続 |

## 注意事項

- コマンド型のみ対応（prompt 型 / agent 型は不可）
- コマンドはプロジェクトルートから実行される
- Worktree 使用時は `cd` でパスを合わせる必要がある場合がある
