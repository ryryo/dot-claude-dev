---
name: dev:ideation
description: |
  プロダクトアイデアをJTBD分析→競合調査→SLC仕様書に構造化。
  dev:storyの上流で使用し、何を作るべきかを明確にする。
  「アイデアを整理」「/dev:ideation」で起動。

  Trigger:
  アイデア整理, プロダクト企画, /dev:ideation, ideation, 何を作るべきか
context: fork
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

## 出力先

`docs/ideation/{YYMMDD}-{slug}/` に3ファイルを**順次**保存する。
- `{YYMMDD}`: 実行日（例: `260202`）
- `{slug}`: アイデアを表す短い英語スラッグ（例: `ai-code-review`）

---

## ★ 実行手順（必ずこの順序で実行）

### Step 0: アイデアのヒアリング → スラッグ決定

1. **AskUserQuestion** でプロダクトアイデアを聞き取る
   - 「どんなプロダクトを考えていますか？」
   - 「誰のどんな問題を解決しますか？」
2. アイデアが曖昧な場合は追加質問で具体化
3. アイデアからスラッグ候補を生成し **AskUserQuestion** で確定
4. `mkdir -p docs/ideation/{YYMMDD}-{slug}`

**ゲート**: アイデアの概要が明確で、出力ディレクトリが作成されるまで次に進まない。

以降、`{dir}` = `docs/ideation/{YYMMDD}-{slug}` とする。

### Step 1: 問題定義 → PROBLEM_DEFINITION.md

references/problem-definition.md を Read し、その構成に従って **Write** で `{dir}/PROBLEM_DEFINITION.md` を作成する。

- Step 0 で把握したユーザーのアイデアを元に、JTBDフレームワークで分析
- AskUserQuestion でペインの優先度やターゲットユーザーの認識を確認

**ゲート**: `{dir}/PROBLEM_DEFINITION.md` が存在しなければ次に進まない。

### Step 2: 競合分析 → COMPETITOR_ANALYSIS.md

1. → **Task（sonnet）** に委譲（agents/competitor-analysis.md）
   - 追加コンテキスト: `{dir}/PROBLEM_DEFINITION.md` のパス
2. **Write** で `{dir}/COMPETITOR_ANALYSIS.md` を保存

**ゲート**: `{dir}/COMPETITOR_ANALYSIS.md` が存在しなければ次に進まない。

### Step 3: SLCプロダクト仕様 → PRODUCT_SPEC.md

1. → **Task（opus）** に委譲（agents/slc-ideation.md）
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

- agents/: competitor-analysis.md, slc-ideation.md
- references/: problem-definition.md, jtbd-framework.md, slc-framework.md, product-spec-template.md
