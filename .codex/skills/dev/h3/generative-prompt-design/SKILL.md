---
name: generative-prompt-design
description: 画像・動画の生成Promptを新規設計し、失敗したPromptを生成サービス固有の形式へ変換する前に状況から再構築する。カメラ、構図、ポーズ、場所、家具、背景、光、人物数、参照素材の責務、動作、ショット順を作成または変更するときに使う。誤字、台詞の正確な表記、schema、生成内容を変えない時刻だけの修正には使わない。
---

# Generative Prompt Design

完成Promptを書く前に、利用者が得たい画面、参照素材の責務、物理空間、被写体、撮影、時間、合否判定を一つの設計契約へ閉じる。生成サービス固有の書式は後段で適用する。

## 必ず読む資料

1. 新規Promptと実質的な改訂では、[生成Promptの設計契約](references/design-contract.md)と[肯定的再構築](references/positive-reconstruction.md)を最初から最後まで読む。
2. 誤字、正確な台詞表記、schema、生成内容を変えない時刻だけの修正では、この二資料を再読せず局所修正してよい。
3. その後、下の経路から依頼に直接必要なPrompt資料だけを読む。全カタログを一律に読まない。

## Prompt資料の選択

すべての語彙・パターン資料は`references/prompts/`に置く。中核の判断手順と、必要時だけ使うPrompt素材を混ぜない。

- 人物、衣装、複数の参照素材を扱う: [人物・衣装・参照素材](references/prompts/person-reference-and-outfit.md)。複数参照またはショット間の同一性がある場合だけ[参照素材と連続性](references/prompts/reference-continuity.md)も読む。
- 若い成人女性の人物固有形状を扱う: 必要な部位だけ[体型](references/prompts/young-adult-woman-body.md)、[顔](references/prompts/young-adult-woman-face.md)、[肌・髪・化粧](references/prompts/young-adult-woman-skin-hair.md)、[姿勢・動作](references/prompts/young-adult-woman-pose-motion.md)から選ぶ。他の年齢、性別、非人間へ転用しない。
- 場所、家具、背景、撮影者、カメラ、構図、複数ショットを扱う: [状況・カメラ・空間](references/prompts/shot-situation-camera-and-space.md)。旅、デート、撮影スタジオなどの構成例が必要な場合だけ[撮影シナリオ](references/prompts/shot-scenario-playbooks.md)を追加する。
- SNS撮影の状況語彙が必要: 設計契約で撮る理由から終了フレームまでを閉じた後にだけ[SNS撮影状況](references/prompts/influencer-shot-situations.md)を使う。
- 撮影らしさ、端末、レンズ、焦点、露出の語彙が必要: [撮影らしさとカメラ表現](references/prompts/capture-realism.md)から必要な項目だけを使う。

個別カタログは設計の代わりではない。語彙を先に拾ってから状況を組み立てない。

## 変更分類

次だけを細微な変更として扱う。

- 誤字、句読点、台詞の正確な表記
- 生成サービスのschema、フィールド名、参照ラベルの形式修正
- 生成内容、動作順、音声との因果を変えない時刻調整

カメラ、構図、ポーズ、場所、家具、背景、光、人物数、参照素材の責務、動作、ショット順の作成・変更は実質的設計である。旧文への「禁止」「追加」「変更」で済ませず、影響する状況全体を肯定形で再構築する。

## 作業手順

### 1. 実物を観察する

- 参照素材と既存成果物を実際に見る。Prompt内の語句を成果の証拠にしない。
- 観測した事実、利用者が維持したい成果、原因仮説、今回の設計判断を分ける。
- 遮蔽、切り取り、別角度で見えない部分を観測事実にしない。

### 2. 影響範囲を決める

[肯定的再構築](references/positive-reconstruction.md)の伝播表を使う。場所や家具の用途を変えるなら全ショットの平面、人物動線、カメラ位置まで戻る。衣装構造なら全ショット共通の前後面、開口部、肩紐、層まで戻る。競合する旧前提は完成文へ持ち込まない。

### 3. 設計契約を閉じる

[生成Promptの設計契約](references/design-contract.md)を埋める。

- 参照素材ごとに許可する属性、優先順位、転写しない属性、見えないため未確定の属性を決める。
- 一つの場所なら、用途、建築上のつながり、区画、家具の利用者と用途、通路、光源を一つの平面へ置く。
- 被写体の固有形状、衣装構造、接地と重心、カメラによる見え方を分ける。
- 動画では初期状態、きっかけ、被写体の反応、記録画面の反応、終了フレームを尺内へ置く。

### 4. 肯定形へ再構築する

望む画面を自然に必要とする場所の用途、家具の用途、支持面、出来事、撮影の起点を書く。否定表現は参照素材から転写しない属性、権利・安全境界、生成サービス固有の禁止欄に限定し、背景、人数、ポーズ、カメラを成立させる主要設計にしない。

### 5. 成果物で合否を決める

位置、画面占有、切り取り、接地、前後関係、背景移動、動作順、保持時間、音で合格条件を書く。全条件に答えがあり競合がない場合だけ`DESIGN_STATUS: PASS`とする。`REBUILD`または`BLOCKED`のまま完成Promptへ進まない。

### 6. 生成サービス形式へ変換する

設計契約がPASSになった後で、指定サービスの専用スキルまたは公式schemaへ変換する。MiniMax H3では`$h3-prompt-writing`を使う。このスキル内にモデル別の挿入位置一覧を重複して持たない。

## 後段へ渡すもの

1. 完成した設計契約
2. 参照素材の許可属性、優先順位、転写しない属性
3. 破棄した旧前提
4. 成果物で判定する合格条件
5. 画像／動画、尺、比率、参照上限、文字数など生成先の境界

## 保守

Prompt資料はLabの人物Prompt辞典とShot Prompt Guideのデータモジュールから同期する。生成済みMarkdownを直接編集しない。

~~~sh
node scripts/sync-lab-guides.mjs --check --source-root /absolute/path/to/influencer-studio
node scripts/sync-lab-guides.mjs --write --source-root /absolute/path/to/influencer-studio
~~~

通常のPrompt設計は生成済み資料だけで完結させ、Labのrepositoryが手元にあることを前提にしない。

## 境界

- このスキルはPrompt内容の設計と監査を行う。画像・動画生成、API実行、課金、配備の権限を含まない。
- 実生成の成功は語句一致ではなく成果物で確認する。
- 生成サービス固有の書式、キュー、Run／Job、費用管理は対応する変換スキルまたは実行スキルへ委ねる。
