---
name: dqa-screenshot
description: design-e2e-qa の SS 撮影。take-screenshots.sh を実行し全ページ × 3VP のスクリーンショットを撮影する。
model: haiku
allowed_tools: Bash
---

# SS 撮影エージェント

指定された URL とページリストに対して、`take-screenshots.sh` を実行しスクリーンショットを撮影する。

## 撮影パターン

### 静的ページ（デフォルト）

認証不要で、URL を開くだけで撮影できるページ。

```bash
cd /path/to/project && bash .claude/skills/design-e2e-qa/scripts/take-screenshots.sh {BASE_URL} top:/ article-detail:/posts/slug/ archive:/posts/ about:/about
```

### ステートフル UI（認証・インタラクション必要）

認証やインタラクション後の状態を撮影する場合、`--before-script` でページ操作スクリプトを指定する。

```bash
cd /path/to/project && bash .claude/skills/design-e2e-qa/scripts/take-screenshots.sh \
  --before-script .claude/e2e/login.js \
  {BASE_URL} dashboard:/dashboard profile:/profile
```

before-script は `export default async (page) => {}` 形式の ESM ファイル。Puppeteer の page オブジェクトを直接操作して認証・ナビゲーション・インタラクションを行う。

## 手順

1. 上記いずれかのコマンドを `Bash` で実行する（各ページを**別々の引数**として渡すこと。クォートで一括にしない）

**重要**: ページリストは `bash ... {BASE_URL} page1:path1 page2:path2 page3:path3` のように各ページを個別の引数として渡す。
`"page1:path1 page2:path2"` のようにクォートで囲むと単一引数になり最初のページしか撮影されない。

2. エラーが出た場合はエラー内容を報告する
3. 完了したら `.tmp/design-e2e-qa/screenshots/` のファイル一覧を `ls .tmp/design-e2e-qa/screenshots/` で表示する

## 備考

- VP（ビューポート）の切り替えは `screenshot.js` が内部で処理する（desktop/tablet/mobile の 3VP を自動撮影）
- `--width`/`--height` を明示指定すると単一 VP モードになる（take-screenshots.sh では使用しない）
