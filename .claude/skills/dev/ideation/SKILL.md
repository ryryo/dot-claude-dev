---
name: dev:ideation
description: |
  プロダクトアイデアをJTBD分析→競合調査→SLC仕様書に構造化。
  dev:storyの上流で使用し、何を作るべきかを明確にする。
  「アイデアを整理」「/dev:ideation」で起動。

  Trigger:
  アイデア整理, プロダクト企画, /dev:ideation, ideation, 何を作るべきか
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Task
  - AskUserQuestion
  - WebSearch
  - WebFetch
---

# アイデア → プロダクト仕様書（dev:ideation）

## エージェント委譲ルール

**⚠️ 分析・調査・設計は必ずTaskエージェントに委譲する。自分で実行しない。**

呼び出しパターン（全ステップ共通）:
```
agentContent = Read(".claude/skills/dev/ideation/agents/{agent}.md")
Task({ prompt: agentContent + 追加コンテキスト, subagent_type: "general-purpose", model: {指定モデル} })
```

| Step | agent | model | 追加コンテキスト |
|------|-------|-------|-----------------|
| 1 | problem-definition.md | opus | ユーザーのアイデア |
| 2 | competitor-analysis.md | sonnet | PROBLEM_DEFINITION.mdのパス |
| 3 | slc-ideation.md | opus | PROBLEM_DEFINITION.md + COMPETITOR_ANALYSIS.mdのパス |

## 出力先

`docs/ideation/{YYYYMMDD}-{slug}/` に3ファイルを**順次**保存する。
- `{YYYYMMDD}`: 実行日（例: `20260202`）
- `{slug}`: アイデアを表す短い英語スラッグ（例: `ai-code-review`）

---

## ★ 実行手順（必ずこの順序で実行）

### Step 0: アイデアのヒアリング → スラッグ決定

1. **AskUserQuestion** でプロダクトアイデアを聞き取る
   - 「どんなプロダクトを考えていますか？」
   - 「誰のどんな問題を解決しますか？」
2. アイデアが曖昧な場合は追加質問で具体化
3. アイデアからスラッグ候補を生成し **AskUserQuestion** で確定
4. `mkdir -p docs/ideation/{YYYYMMDD}-{slug}`

**ゲート**: アイデアの概要が明確で、出力ディレクトリが作成されるまで次に進まない。

以降、`{dir}` = `docs/ideation/{YYYYMMDD}-{slug}` とする。

### Step 1: 問題定義 → PROBLEM_DEFINITION.md

1. → **エージェント委譲**（problem-definition.md / opus）
   - 追加コンテキスト: ユーザーのアイデア + 出力先 `{dir}/PROBLEM_DEFINITION.md`
2. **Write** で `{dir}/PROBLEM_DEFINITION.md` を保存

**ゲート**: `{dir}/PROBLEM_DEFINITION.md` が存在しなければ次に進まない。

### Step 2: 競合分析 → COMPETITOR_ANALYSIS.md

1. → **エージェント委譲**（competitor-analysis.md / sonnet）
   - 追加コンテキスト: `{dir}/PROBLEM_DEFINITION.md` のパス
2. **Write** で `{dir}/COMPETITOR_ANALYSIS.md` を保存

**ゲート**: `{dir}/COMPETITOR_ANALYSIS.md` が存在しなければ次に進まない。

### Step 3: SLCプロダクト仕様 → PRODUCT_SPEC.md

1. → **エージェント委譲**（slc-ideation.md / opus）
   - 追加コンテキスト: `{dir}/PROBLEM_DEFINITION.md` + `{dir}/COMPETITOR_ANALYSIS.md` のパス
2. **Write** で `{dir}/PRODUCT_SPEC.md` を保存

**ゲート**: `{dir}/PRODUCT_SPEC.md` が存在しなければ次に進まない。

### Step 4: ユーザー確認

---

## 完了条件

以下3ファイルがすべて `{dir}/` に保存されていること:

| ファイル | Step |
|----------|------|
| `{dir}/PROBLEM_DEFINITION.md` | Step 1 |
| `{dir}/COMPETITOR_ANALYSIS.md` | Step 2 |
| `{dir}/PRODUCT_SPEC.md` | Step 3 |

- ユーザーが仕様書を承認済み

## 参照

- agents/: problem-definition.md, competitor-analysis.md, slc-ideation.md
- references/: jtbd-framework.md, slc-framework.md, product-spec-template.md
