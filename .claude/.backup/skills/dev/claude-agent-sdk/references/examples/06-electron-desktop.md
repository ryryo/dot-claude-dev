# #6 デスクトップアプリ（Electron）

**何を作れるか**: Electron でネイティブデスクトップアプリを作り、Claude をバックエンドAIエンジンとして統合。ファイルアップロード、Excelファイル操作、ローカルファイル管理などのGUIアプリ。

**デモソース**: [excel-demo](https://github.com/anthropics/claude-agent-sdk-demos/tree/main/excel-demo)

## アーキテクチャ

```
Renderer Process (React UI)
    ↕ IPC (ipcMain / ipcRenderer)
Main Process
    → query() SDK
        → ツール実行 (Bash, Write, Skill...)
        → 結果を IPC で UI に返す
```

**SDK主要機能**: `query()`, `settingSources`, `allowedTools`, `Skill`, `abortController`

## コード例: Electron Main Process で SDK を使用（TypeScript）

```typescript
import { query, type SDKMessage } from '@anthropic-ai/claude-agent-sdk';
import { ipcMain } from 'electron';

ipcMain.on('claude-code:query', async (event, data) => {
  const abortController = new AbortController();
  const cwd = path.join(process.cwd(), 'agent');

  // ファイルアップロード処理
  if (data.files?.length > 0) {
    for (const file of data.files) {
      const buffer = Buffer.from(file.buffer);
      await fs.promises.writeFile(
        path.join(cwd, 'problems', file.name),
        buffer
      );
    }
  }

  try {
    const queryIterator = query({
      prompt: data.content,
      options: {
        cwd,
        abortController,             // キャンセル可能に
        maxTurns: 100,
        settingSources: ['local', 'project'], // .claude/skills/ を読み込み
        allowedTools: [
          'Bash', 'Edit', 'Read', 'Write', 'MultiEdit',
          'WebSearch', 'Skill', 'TodoWrite',
        ],
      },
    });

    for await (const message of queryIterator) {
      // SDKメッセージをRendererプロセスにIPC転送
      event.reply('claude-code:response', message);
    }

    // 完了後: 新規生成ファイルを検出してUIに通知
    const newFiles = detectNewOutputFiles(cwd, initialFiles);
    if (newFiles.length > 0) {
      event.reply('claude-code:output-files', newFiles);
    }
  } catch (error) {
    event.reply('claude-code:error', error.message);
  }
});
```

## ポイント

- `abortController` でユーザーからのキャンセル操作に対応
- `settingSources: ['local', 'project']` でプロジェクト固有のスキルを読み込み
- IPC経由でSDKメッセージをそのままRendererに転送するシンプルなブリッジ
- `Skill` ツールを `allowedTools` に含めることで `.claude/skills/` のスキルを活用
- ファイルI/Oはメインプロセスで処理し、セキュリティを確保
