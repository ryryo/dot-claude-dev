---
name: ui-design-concepts
description: Create project UI concept proposals as generated bitmap mockups under docs/DESIGN. Use when the user asks to make UI案, design concepts, existing UI brush-ups, Eagle-like UI explorations, or multiple visual directions with prompts saved alongside the images.
---

# UI Design Concepts

このリポジトリで、実装前の UI 案を画像として作るための手順。
成果物は必ず `docs/DESIGN/{YYMMDD}_{slug}/` の 1 フォルダにまとめる。画像数は 3 枚をデフォルトにし、ユーザー指示や検討状況に応じて増減する。`prompts.md` は常に残す。

## Workflow

1. 要件を短く整理する。
   - 対象プロダクト、対象画面、ユーザー、主要 workflow、参考 UI、守るべきデザインシステム、言語、避ける表現を確認する。
   - 指示が不足している場合だけ、`AGENTS.md`、`docs/PLAN`、`docs/DESIGN`、既存 UI、README などからプロジェクト固有の制約を拾う。

2. 既存 UI の扱いを決める。
   - 既存 UI のブラッシュアップ、改善案、見た目の調整、情報設計の改善が目的なら、現在の UI のスクリーンショットを取る。
   - デザイン一新、まだ UI がない新規ページ、参考 UI だけを元にした探索では、現在 UI のスクリーンショットは不要。
   - スクリーンショットを使う場合は、残す構造、変える構造、崩してよい部分をプロンプトに明示する。

3. 出力フォルダを作る。
   - 形式は `docs/DESIGN/{YYMMDD}_{slug}/`。
   - 例: `docs/DESIGN/260615_eagle_ui_concepts/`。
   - 既存フォルダがある場合は上書きせず、`_v2` などの suffix を付ける。

4. 必要な場合だけ現在 UI を撮影する。
   - 既存 UI のブラッシュアップなら、生成案を作る前にスクリーンショットを取る。
   - スクリーンショットは同じ出力フォルダに `current_ui.png` などの名前で保存する。
   - `prompts.md` に参照元 URL、viewport、撮影日時を書く。

5. 方向性と枚数を決める。
   - ユーザーが枚数を指定していなければ 3 案を作る。
   - ユーザーが枚数、粒度、比較対象、モバイル/デスクトップ、状態差分などを指定した場合はそれを優先する。
   - 判断材料が少ない初回探索では 3 案を維持する。既に有力案があり細部だけ詰める場合は 1-2 案に減らしてよい。画面種別やペルソナが複数あり、比較が必要な場合は 4 案以上に増やしてよい。
   - 方向性は重複させず、同じ題材でも情報密度、ナビゲーション、選択状態、詳細表示、操作密度を変える。

6. 画像を生成する。
   - `imagegen` skill/tool を使う。
   - 1 プロンプトにつき 1 枚生成し、決めた枚数分だけ分けて実行する。
   - 生成後、画像ファイルを `docs/DESIGN/{folder}/` にコピーまたは移動する。
   - ファイル名は `concept_01_dense_library.png` のように、番号と方向性が分かる名前にする。

7. `prompts.md` を作る。
   - 含める内容:
     - 作成日
     - 出力ファイル一覧
     - 現在 UI のスクリーンショットを使った場合は、そのファイル、URL、viewport
     - 各 concept の狙い
     - 画像生成に使ったプロンプト全文
     - 参考にした制約やデザイン前提
   - 後から再生成しやすいように、プロンプトは要約ではなく実際に使った文面を残す。

8. 検証して報告する。
   - `ls -lh docs/DESIGN/{folder}` で決めた枚数の画像と `prompts.md` があることを確認する。
   - 必要なら `view_image` で画像が破損していないことを確認する。
   - 最終報告ではフォルダ、各画像、`prompts.md` の絶対パスを示す。

## Context Rules

プロンプトには、確認できた制約だけを入れる。

- Design system: 指定がある場合だけ、HeroUI Pro、Tailwind、shadcn/ui などの名前と作法を入れる。
- Theme: 指定がある場合だけ、Mouve light などのテーマ名、色調を入れる。
- Typography: 指定がある場合だけ、Noto Sans JP などのフォントを入れる。
- Product domain: 資料から確認できた業務、オブジェクト、状態、操作を画面内ラベルへ反映する。
- Existing UI: 既存 UI を改善する場合は、現在の構造を踏まえて崩す部分と残す部分を分ける。

参考 UI が指定された場合は、ブランドや見た目を丸写しせず、情報設計、密度、ナビゲーション、操作モデルだけを抽出する。

例: Eagle 風の UI 案なら、画像アセット管理ツールとして、左のコレクション/タグ、中央のサムネイルグリッド、右の inspector、上部の検索/フィルタ/表示切替を検討する。ただし、これは Eagle 指定時だけの参照パターンであり、他の UI 案に常に適用しない。
