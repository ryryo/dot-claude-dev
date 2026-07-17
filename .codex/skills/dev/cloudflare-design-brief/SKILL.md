---
name: cloudflare-design-brief
description: Cloudflare ベースの新規アプリ設計、または既存アプリを Cloudflare 構成へ大きく移行する前に、短い設計メモを作る。Workers、Agents SDK、Durable Objects、D1、KV、R2、Wrangler、Workers 上の Hono などの構成判断を実装前に整理するときに使う。通常の Cloudflare コード修正だけなら、公式 Cloudflare 実装系 skill を使う。
---

# Cloudflare 設計メモ

この skill は、Cloudflare 構成を決める前の軽いアーキテクチャ入口として使う。ユーザーが別途実装計画を求めない限り、実装計画ではなく設計メモを出す。

## 手順

1. 依頼内容とリポジトリ文脈から、対象が Cloudflare ベースの新規アプリ、または Cloudflare への大きな移行か確認する。通常の Cloudflare 実装修正だけなら、該当する Cloudflare 実装系 skill を使う。
2. アーキテクチャを提案する前に、必ず `https://skills.yusuke.run/start.md` を読む。
3. `start.md` を yusukebe skill catalog の正とする。ローカルに固定した skill 名リストへ置き換えず、その時点の `start.md` に列挙された skill リンクをすべて読む。各 skill 内で設計判断に影響する公式 docs、関連 skill、canonical repo への誘導があれば、それも辿って確認する。
4. 読んだ yusukebe skill のうち、今回の Cloudflare 設計に関係するものだけを設計メモへ反映する。関係しないものは判断材料に含めない。
5. Cloudflare 固有の判断では、公式のローカル skill を優先して読む。
   - `cloudflare`: 製品選定とプラットフォーム横断のトレードオフ。
   - `agents-sdk`: stateful AI agent、chat、MCP、schedule、workflow、tool use。
   - `durable-objects`: stateful coordination、realtime room、WebSocket、alarm、SQLite-backed per-entity state。
   - `wrangler`: config、binding、deploy、environment、local development command。
   - `workers-best-practices`: 設計メモを実装へ進める前の品質確認。
6. limit、pricing、API signature、compatibility flag、configuration field に依存する場合は、必ず最新の Cloudflare docs を取得して確認する。

## 設計メモ

設計メモはユーザーの言語で書く。短く、判断に寄せる。

```markdown
## 要件と制約
- ...

## 採用する Cloudflare 構成
- ...

## 採用しない選択肢と理由
- ...

## 次に読む skill / docs
- ...

## 未確認事項
- ...

## 実装に進む前の判断点
- ...
```

## デフォルト

- 要件上 Pages、Containers、外部 backend が明確に必要でなければ、実行基盤は Cloudflare Workers を基本候補にする。
- 新規 Workers 設定では `wrangler.jsonc` を優先する。
- 記憶より公式 Cloudflare skill と docs を優先する。
- 外部 skill の長い内容を設計メモへ転載しない。選んだ source / skill を示し、判断だけ要約する。
