# 実装パターン横断リファレンス

複数のユースケースで共通して使われる SDK の実装パターン集。

---

## パターン1: ストリーミング出力の消費

全ユースケースで共通する基本パターン。SDKメッセージの `type` フィールドで処理を分岐する。

```typescript
for await (const message of queryIterator) {
  switch (message.type) {
    case 'system':
      // subtype: 'init' → session_id 取得
      break;
    case 'assistant':
      // message.content: text | tool_use のブロック配列
      for (const block of message.message.content) {
        if (block.type === 'text') { /* テキスト出力 */ }
        if (block.type === 'tool_use') { /* ツール呼び出し情報 */ }
      }
      break;
    case 'result':
      // subtype: 'success' | 'error'
      // total_cost_usd, duration_ms でコスト・時間を取得
      break;
  }
}
```

---

## パターン2: フック（Hooks）の活用

| フック | タイミング | 主な用途 |
|--------|----------|---------|
| `PreToolUse` | ツール実行前 | 書き込み先制限、危険コマンドのブロック |
| `PostToolUse` | ツール実行後 | ツール結果のログ記録、追跡 |

### TypeScript

```typescript
// matcher で対象ツールをフィルタ（正規表現パターン）
hooks: {
  PreToolUse: [{
    matcher: 'Write|Edit',
    hooks: [async (input) => {
      // input.tool_name, input.tool_input にアクセス
      return { continue: true }; // or { decision: 'block', stopReason: '...' }
    }]
  }]
}
```

### Python

```python
# HookMatcher で対象ツールをフィルタ
hooks = {
    'PreToolUse': [
        HookMatcher(
            matcher=None,  # None = 全ツール
            hooks=[my_hook_function]
        )
    ]
}

# フック関数の署名
async def my_hook(hook_input, tool_use_id, context):
    return {'continue_': True}
```

---

## パターン3: セッション Resume

V1 API（`query()`）でもセッションIDを保存して `resume` オプションで会話を継続できる。

```typescript
// 初回: セッションIDを取得
for await (const msg of query({ prompt: '...' })) {
  if (msg.type === 'system' && msg.subtype === 'init') {
    savedSessionId = msg.session_id;
  }
}

// 2回目以降: resume で継続
for await (const msg of query({
  prompt: 'Follow-up question...',
  options: { resume: savedSessionId }
})) { /* ... */ }
```

---

## パターン4: Skill 連携

`.claude/skills/` にスキルファイルを配置し、`settingSources` で読み込むことで、エージェントにドメイン知識を注入できる。

### ディレクトリ構造

```
project/
├── .claude/
│   └── skills/
│       └── xlsx/
│           ├── SKILL.md        ← スキル定義
│           └── recalc.py       ← 補助スクリプト
├── agent/
│   └── (エージェントの作業ディレクトリ)
└── main.ts
```

### コード例

```typescript
query({
  prompt: '...',
  options: {
    settingSources: ['local', 'project'],  // スキルを読み込み
    allowedTools: ['Skill', 'Bash', 'Write', 'Read'],  // Skill ツールを許可
  },
});
```
