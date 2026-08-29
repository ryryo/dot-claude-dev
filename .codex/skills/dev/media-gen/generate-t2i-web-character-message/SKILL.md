---
name: generate-t2i-web-character-message
description: 人物のキャラクターシート、参考画像、または要件テキストから、Web掲載用の固定カメラ短尺image-to-videoに投入する人物メッセージ静止画を生成・選定・目視確認する。人物が商品や資料を見せる1枚絵、うなずき・まばたき・サムズアップなどの動画化前ソース画像、CTA付近の人物画像、キャラクター同一性を保ったポーズ画像が必要なときに使用する。
---

# 人物メッセージ動画用静止画生成

## ゴール

Kamui i2vへ投入できる「動画化したい1枚絵」を作る。キャラクターシート、参考画像、要件テキストをそのままi2vへ渡さず、人物ID、ポーズ、持ち物、表情、構図が1枚に整理された採用画像を生成する。

人物メッセージ動画そのものは作らない。動画化は [generate-i2v-character-message](../generate-i2v-character-message/SKILL.md) を読む。

## 原則

- 1枚絵の時点でメッセージ、人物、持ち物、表情を確定する。
- 動画で動かす前提の小さな動作が成立する静止ポーズにする。
- 人物は1人を基本にする。複数人物が必要な場合だけ明示的に入れる。
- テロップ、ロゴ、UI、不要な文字を画像内へ入れない。
- 下部テロップを後入れする場合は、顔、手、持ち物を隠さない余白を残す。
- 実写風では、過度なAI光沢、完璧すぎるスタジオ背景、素材写真感を避ける。
- 人物の視線、手、持ち物、画面や紙面などの表示面が、1枚の中で物理的に成立するようにする。
- 生成して終わらず、必ず目視確認し、i2v入力に耐えない場合は修正生成する。

## 入力素材

入力素材の扱いは [source-image-guide.md](references/source-image-guide.md) を読む。

優先順位:

1. キャラクターシート + 構図要件
2. 人物参考画像 + 構図要件
3. 要件テキストだけ

すでに採用済みの動画用1枚絵がある場合、このスキルではなく [generate-i2v-character-message](../generate-i2v-character-message/SKILL.md) を使う。

## 出力規約

Image Gen共通の出力契約は [imagegen-core](../imagegen-core/SKILL.md) を読む。保存先、候補画像、修正生成、メタデータ、報告形式はimagegen-coreの規約に従い、このスキル側で再定義しない。

## 生成手順

### 1. 動画化する静止ポーズを決める

次を1つずつ決める。

- 人物ID: 年齢感、髪型、服装、表情、雰囲気
- 構図: バストアップ、上半身、全身、視線方向、余白
- 持ち物: 資料、商品、スマホ、カードなど
- 物理関係: カメラ位置、人物の向き、視線対象、操作対象、表示面、非表示面
- 動画化時の小さな動作: うなずき、まばたき、親指を少し強調、資料を少し見せる
- 動かさない要素: 背景、服装、持ち物、ロゴや文字の不使用
- 比率: 掲載枠に合わせる。根拠がなければ4:3を優先する。

### 1.1 物理整合性を先に決める

人物が物を見る、話す、持つ、指す、見せる画像では、プロンプト作成前に次を明文化する。

- カメラ位置: 誰のどちら側から、どの高さで見るか
- 人物の向き: 顔、胴体、手がどちらを向いているか
- 視線対象: 人物が実際に見ている対象は何か
- 操作対象: 手が触れる、持つ、指す対象は何か
- 表示面: 画面、紙面、ラベルなど、情報が出てよい面はどこか
- 非表示面: 情報が出てはいけない面はどこか
- 見せる情報: 読ませる、ぼかす、形だけ見せる、完全に見せない、のどれか

カメラ位置、視線対象、表示面が同時に成立しない場合は、情報を見せることを諦めるか、構図または小道具を変える。たとえば、画面内容を見せたいのに端末の背面しかカメラに見えない構図では、画面内容を描かせない。必要なら肩越し構図、外部モニター、タブレット、紙資料などへ置き換える。

### 2. 画像生成プロンプトを作る

`$imagegen`の手順で画像を生成する。参照画像がある場合は事前に確認し、必要な画像だけを渡す。

プロンプトには次を具体的に含める。

- Web掲載用の人物メッセージ動画に使う静止画であること
- カメラ固定で動画化しやすい単一ショットであること
- 人物ID、服装、表情、持ち物、手の形
- 背景、照明、画角、比率
- カメラ位置、人物の向き、視線対象、操作対象、表示面、非表示面
- 画像内テキスト、字幕、ロゴ、UI、余計なオブジェクトを禁止すること
- 手、指、顔、持ち物の破綻を避けること

画面、紙面、商品ラベルなどの表示面がある場合は、次のような物理整合性指定をプロンプトへ入れる。

```text
The subject's eyes must land on the same object they are interacting with.
Define which surface is visible to the camera and which surface is hidden.
Only the true visible display/paper surface may contain blurred content.
Non-display surfaces must remain plain material surfaces.
If the display/paper surface cannot be physically visible from this camera angle, do not show its content.
Hands, gaze, object orientation, and camera position must describe one coherent action.
```

禁止指定は抽象的な「不自然にしない」だけで済ませず、破綻しやすい面を具体的に書く。

```text
No content, reflection, interface, document, portrait, glow, or label on surfaces that are not displays or paper.
No impossible screen geometry.
No eyeline mismatch.
No hand-object mismatch.
```

実写風では次の質感を優先する。

```text
Natural frame from a casual smartphone video, modest indoor lighting, slightly compressed but clean image, realistic skin and fabric texture, no studio stock-photo polish, no over-retouched AI gloss.
```

### 3. 目視確認する

生成画像を開き、次を確認する。

- 1人の人物として一貫している
- 顔、手、指、持ち物が破綻していない
- 動画で必要な小さな動作が成立するポーズになっている
- 人物の目線が、指定した視線対象へ自然に向いている
- 顔、胴体、手、対象物の向きが、同じ行為として成立している
- 画面、紙面、商品ラベルなどの情報が、実際に表示される面だけに出ている
- 表示面でない面に、画面、反射、UI、文字、人物、資料が貼り付いていない
- カメラ位置から見えるはずのないものを無理に見せていない
- テロップ、字幕、ロゴ、UI、不要な文字が入っていない
- 構図と比率が掲載枠に合っている
- 下部テロップやCTA付近の配置を邪魔しない余白がある
- i2vで固定カメラを維持しやすい単純な背景になっている

問題があれば修正生成する。特に手、指、持ち物、顔、視線、表示面、接触関係の違和感は動画化で悪化しやすいため、軽微でも採用しない。物理関係が破綻した場合は同じプロンプトを少し直して再試行するのではなく、カメラ位置、表示面、小道具のどれかを単純化して再生成する。

### 4. 採用画像を引き渡す

採用画像、候補画像、メタデータをimagegen-coreの出力契約に従って整理する。完了時はimagegen-coreの報告形式に従い、キャラクター静止画固有の主要オプションとして比率と想定する小さな動作を含める。

続けて動画化する場合は、採用画像を [generate-i2v-character-message](../generate-i2v-character-message/SKILL.md) の入力画像として使う。Kamui投入前のメタデータ除去やJPEG化は動画化スキル側の `prepare_source.py` に任せる。
