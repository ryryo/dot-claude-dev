# スラッシュコマンドとTodoトラッキング

## 4. スラッシュコマンド

スラッシュコマンドは、`/`で始まる特別なコマンドでClaude Codeセッションを制御する方法を提供する。

### 利用可能なスラッシュコマンドの確認

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Hello Claude",
  options: { maxTurns: 1 }
})) {
  if (message.type === "system" && message.subtype === "init") {
    console.log("Available slash commands:", message.slash_commands);
    // 出力例: ["/compact", "/clear", "/help"]
  }
}
```

### スラッシュコマンドの送信

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "/compact",
  options: { maxTurns: 1 }
})) {
  if (message.type === "result") {
    console.log("Command executed:", message.result);
  }
}
```

### 一般的なスラッシュコマンド

#### `/compact` - 会話履歴の圧縮

重要なコンテキストを保持しながら古いメッセージを要約し、会話履歴のサイズを削減する。

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "/compact",
  options: { maxTurns: 1 }
})) {
  if (message.type === "system" && message.subtype === "compact_boundary") {
    console.log("Compaction completed");
    console.log("Pre-compaction tokens:", message.compact_metadata.pre_tokens);
    console.log("Trigger:", message.compact_metadata.trigger);
  }
}
```

#### `/clear` - 会話のクリア

以前の履歴をすべてクリアして新しい会話を開始する。

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "/clear",
  options: { maxTurns: 1 }
})) {
  if (message.type === "system" && message.subtype === "init") {
    console.log("Conversation cleared, new session started");
    console.log("Session ID:", message.session_id);
  }
}
```

### カスタムスラッシュコマンドの作成

カスタムコマンドはマークダウンファイルとして定義される。

#### ファイルの配置場所

| スコープ | ディレクトリ | 説明 |
|---------|------------|------|
| プロジェクトコマンド | `.claude/commands/` | 現在のプロジェクトでのみ利用可能 |
| 個人コマンド | `~/.claude/commands/` | すべてのプロジェクトで利用可能 |

#### ファイル形式

- ファイル名（`.md`拡張子を除く）がコマンド名になる
- ファイルの内容がコマンドの動作を定義する
- オプションのYAMLフロントマターで設定を提供する

#### 基本的な例

`.claude/commands/refactor.md`:
```
Refactor the selected code to improve readability and maintainability.
Focus on clean code principles and best practices.
```

#### フロントマター付き

`.claude/commands/security-check.md`:
```
---
allowed-tools: Read, Grep, Glob
description: Run security vulnerability scan
model: claude-opus-4-6
---

Analyze the codebase for security vulnerabilities including:
- SQL injection risks
- XSS vulnerabilities
- Exposed credentials
- Insecure configurations
```

#### 引数とプレースホルダー

`.claude/commands/fix-issue.md`:
```
---
argument-hint: [issue-number] [priority]
description: Fix a GitHub issue
---

Fix issue #$1 with priority $2.
Check the issue description and implement the necessary changes.
```

SDKでの使用：
```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "/fix-issue 123 high",
  options: { maxTurns: 5 }
})) {
  // コマンドは $1="123" と $2="high" で処理されます
  if (message.type === "result") {
    console.log("Issue fixed:", message.result);
  }
}
```

#### Bashコマンドの実行

`.claude/commands/git-commit.md`:
```
---
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
description: Create a git commit
---

## Context

- Current status: !`git status`
- Current diff: !`git diff HEAD`

## Task

Create a git commit with appropriate message based on the changes.
```

#### ファイル参照

`@`プレフィックスを使用してファイルの内容を含める：

`.claude/commands/review-config.md`:
```
---
description: Review configuration files
---

Review the following configuration files for issues:
- Package config: @package.json
- TypeScript config: @tsconfig.json
- Environment config: @.env

Check for security issues, outdated dependencies, and misconfigurations.
```

#### 名前空間による整理

```
.claude/commands/
├── frontend/
│   ├── component.md      # /component (project:frontend) を作成
│   └── style-check.md     # /style-check (project:frontend) を作成
├── backend/
│   ├── api-test.md        # /api-test (project:backend) を作成
│   └── db-migrate.md      # /db-migrate (project:backend) を作成
└── review.md              # /review (project) を作成
```

サブディレクトリはコマンドの説明に表示されるが、コマンド名自体には影響しない。

#### コードレビューコマンドの例

`.claude/commands/code-review.md`:
```
---
allowed-tools: Read, Grep, Glob, Bash(git diff:*)
description: Comprehensive code review
---

## Changed Files
!`git diff --name-only HEAD~1`

## Detailed Changes
!`git diff HEAD~1`

## Review Checklist

Review the above changes for:
1. Code quality and readability
2. Security vulnerabilities
3. Performance implications
4. Test coverage
5. Documentation completeness

Provide specific, actionable feedback organized by priority.
```

#### テストランナーコマンドの例

`.claude/commands/test.md`:
```
---
allowed-tools: Bash, Read, Edit
argument-hint: [test-pattern]
description: Run tests with optional pattern
---

Run tests matching pattern: $ARGUMENTS

1. Detect the test framework (Jest, pytest, etc.)
2. Run tests with the provided pattern
3. If tests fail, analyze and fix them
4. Re-run to verify fixes
```

---

## 5. Todoトラッキング

Todo追跡は、タスクを管理しユーザーに進捗を表示するための構造化された方法を提供する。

### Todoのライフサイクル

1. タスクが特定されたときに`pending`として**作成**される
2. 作業が開始されたときに`in_progress`に**アクティブ化**される
3. タスクが正常に完了したときに**完了**する
4. グループ内のすべてのタスクが完了したときに**削除**される

### Todoが自動作成される条件

- 3つ以上の異なるアクションを必要とする**複雑な複数ステップのタスク**
- 複数の項目が言及されている**ユーザー提供のタスクリスト**
- 進捗追跡の恩恵を受ける**重要な操作**
- ユーザーがtodo整理を求める**明示的な要求**

### Todo変更の監視

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "React アプリのパフォーマンスを最適化し、todoで進捗を追跡する",
  options: { maxTurns: 15 }
})) {
  if (message.type === "tool_use" && message.name === "TodoWrite") {
    const todos = message.input.todos;

    console.log("Todoステータス更新:");
    todos.forEach((todo, index) => {
      const status = todo.status === "completed" ? "done" :
                    todo.status === "in_progress" ? "working" : "pending";
      console.log(`${index + 1}. ${status} ${todo.content}`);
    });
  }
}
```

### リアルタイム進捗表示

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

class TodoTracker {
  private todos: any[] = [];

  displayProgress() {
    if (this.todos.length === 0) return;

    const completed = this.todos.filter(t => t.status === "completed").length;
    const inProgress = this.todos.filter(t => t.status === "in_progress").length;
    const total = this.todos.length;

    console.log(`\n進捗: ${completed}/${total} 完了`);
    console.log(`現在作業中: ${inProgress} タスク\n`);

    this.todos.forEach((todo, index) => {
      const icon = todo.status === "completed" ? "done" :
                  todo.status === "in_progress" ? "working" : "pending";
      const text = todo.status === "in_progress" ? todo.activeForm : todo.content;
      console.log(`${index + 1}. ${icon} ${text}`);
    });
  }

  async trackQuery(prompt: string) {
    for await (const message of query({
      prompt,
      options: { maxTurns: 20 }
    })) {
      if (message.type === "tool_use" && message.name === "TodoWrite") {
        this.todos = message.input.todos;
        this.displayProgress();
      }
    }
  }
}

const tracker = new TodoTracker();
await tracker.trackQuery("todoを使用して完全な認証システムを構築する");
```
