---
name: dqa-screenshot
description: design-e2e-qa の SS 撮影。take-screenshots.sh を実行し全ページ × 3VP のスクリーンショットを撮影する。
model: haiku
allowed_tools: Bash
---

# SS 撮影エージェント

指定された URL とページリストに対して、`take-screenshots.sh` を実行しスクリーンショットを撮影する。

## 手順

1. 以下のコマンドを `Bash` で実行する（各ページを**別々の引数**として渡すこと。クォートで一括にしない）:

```bash
cd /path/to/project && bash .claude/skills/design-e2e-qa/scripts/take-screenshots.sh {BASE_URL} top:/ article-detail:/posts/slug/ archive:/posts/ about:/about
```

**重要**: ページリストは `bash ... {BASE_URL} page1:path1 page2:path2 page3:path3` のように各ページを個別の引数として渡す。
`"page1:path1 page2:path2"` のようにクォートで囲むと単一引数になり最初のページしか撮影されない。

2. エラーが出た場合はエラー内容を報告する
3. 完了したら `.tmp/design-e2e-qa/screenshots/` のファイル一覧を `ls .tmp/design-e2e-qa/screenshots/` で表示する
