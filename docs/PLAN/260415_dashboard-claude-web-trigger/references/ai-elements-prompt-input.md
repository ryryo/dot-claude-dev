# ai-elements PromptInput — 実装に必要な API 要点

> 元は外部リポジトリ `vercel/ai-elements` のコンポーネント。本仕様書では `npx shadcn@latest add @ai-elements/prompt-input` でこのリポにコピーされる前提。インストール先: `dashboard/components/ai-elements/prompt-input.tsx`。本ドキュメントは**実装時に必要な API 形だけを抜粋**したリファレンス。

## 提供される主要コンポーネント

```tsx
import {
  PromptInput,
  PromptInputBody,
  PromptInputTextarea,
  PromptInputToolbar,
  PromptInputTools,
  PromptInputSubmit,
  PromptInputAttachment,        // 添付ファイルが必要な場合のみ
  PromptInputAttachments,
  PromptInputActionMenu,        // 設定メニューが必要な場合のみ
  PromptInputModelSelect,       // モデル切替が必要な場合のみ
} from '@/components/ai-elements/prompt-input';
```

## 最小構成（本仕様書で使う形）

```tsx
<PromptInput
  onSubmit={(message) => {
    // message は { text: string, files?: File[] } の形
    // 本仕様書では files は使わず text だけ参照する
    handleSubmit();
  }}
  className="border"
>
  <PromptInputTextarea
    value={prompt}
    onChange={(e) => setPrompt(e.target.value)}
    placeholder="Claude に依頼するタスクを入力..."
    disabled={loading}
  />
  <PromptInputToolbar>
    <div className="flex-1" />
    <PromptInputSubmit
      disabled={!canSubmit}
      status={loading ? 'streaming' : undefined}
    />
  </PromptInputToolbar>
</PromptInput>
```

## 主要 props

### `<PromptInput>`

| prop | 型 | 説明 |
| --- | --- | --- |
| `onSubmit` | `(message: { text: string; files?: File[] }) => void` | Submit ボタン押下 / Enter 押下時に呼ばれる |
| `className` | `string` | 既存のラッパー枠線を上書きしたい場合 |

### `<PromptInputTextarea>`

通常の `<textarea>` props をすべて受け付ける（controlled で OK）。`value` / `onChange` で外部 state にバインド。`disabled` で送信中は入力不可に。

### `<PromptInputSubmit>`

| prop | 型 | 説明 |
| --- | --- | --- |
| `status` | `'submitted' \| 'streaming' \| 'ready' \| 'error' \| undefined` | アイコンと挙動が変わる。`'streaming'` 中は loader / cancel に切り替わる |
| `disabled` | `boolean` | フォーム未充足時は true |

`status` が `streaming` のとき、内部でクリック時に AbortController.abort() を呼ぶ実装が含まれることがあるので、本仕様書では cancel ボタンとして使わず単に loader 表示用に使う。

## このリポでの想定挙動

- 添付・モデル切替・アクションメニューは **すべて使わない**（最小構成）。
- Submit のキー入力は ai-elements 標準（Enter 送信、Shift+Enter 改行）に従う。
- `onSubmit` のコールバックは `e.preventDefault()` 不要（ai-elements 内部で form を扱う）。

## 注意

- shadcn registry 経由でコピーされたコンポーネントは、**手書き編集を加えるとアップデート時に上書きされる**。本仕様書では一切手を加えず、外側のラッパー（SessionLauncherDialog）から制御するだけにする。
- `npx shadcn@latest add @ai-elements/prompt-input` 実行時、peer dep として `@ai-sdk/react` 等が install される可能性がある。本仕様書では import だけして利用しないため、bundle サイズに注意するなら別途 tree-shaking 確認すること。

## 参考リンク（実装中の Web 参照用）

- リポジトリ: https://github.com/vercel/ai-elements
- ドキュメント: https://elements.ai-sdk.dev/components/prompt-input
