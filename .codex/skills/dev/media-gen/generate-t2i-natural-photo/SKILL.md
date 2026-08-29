---
name: generate-t2i-natural-photo
description: 参照画像または要件テキストから、SNSやUGCに実在しそうな自然な実写写真をImage Genで生成・選定・目視確認する。人物の顔・髪・体型、肌、光、撮影特性、参照資料の役割を分離し、広告写真やCGのようなAI光沢を避ける。現在画像を保った人物再現、制御された人物資料、局所修正、画質再構築では、同梱referenceから適切な専門工程へルーティングする。
---

# 自然なSNS実写生成

## ゴール

美しさ、清潔感、上品さ、親しみやすさを残しながら、完璧に均された広告モデル写真ではなく、現実の人物と場所を日常の撮影機器で写したような一枚を作る。自然さは画質を機械的に劣化させて作らず、人物固有の形、場面に説明できる光、控えめな画像処理、生活上の小さな不均一さから成立させる。

## 対象と境界

このスキルを使う:

- SNS投稿、UGC、日常スナップ、友人撮影、スマートフォン写真風の新規実写生成
- 顔、人物シート、衣装、背景、構図など複数の参照を担当別に統合する完成画像生成
- 参照画像なしで、文章から実在しそうな人物写真や日常写真を作る場合
- 既存画像を入力にしても、利用者が「元資料から新しく作り直す」と指定した再生成
- 現在画像の場面、衣装、表情、撮影特性を保ちながら、顔や体型を基準資料へ合わせ直す人物再現

このスキルを総合入口として使い、次は専門工程へルーティングする:

- 顔や体型の比較資料、キャラクターシート、三面図: [制御撮影と適用先](references/controlled-reference-and-routing.md)を読み、同梱の[配置テンプレート](assets/character-sheet-layout-template.png)と`character-sheet-imagegen`を使う
- ガビガビ、二重輪郭、編集残りなどの画質再構築: [局所修正とクリーン再構築](references/refinement-and-clean-remake.md)を読み、`ai-clean-remake`を使う
- 構図ラフ、漫画、アイソメ図、イラスト、動画生成
- 既存画像の局所だけを直す注釈編集: [局所修正とクリーン再構築](references/refinement-and-clean-remake.md)の局所修正契約を使う

## 共通実行契約

実生成前に`$imagegen`の指示と [imagegen-core](../imagegen-core/SKILL.md) を読む。保存先、候補名、`prompt.txt`、`request.json`、`review.json`はimagegen-coreへ従う。プロンプト作成だけを依頼された場合はImage Genを実行しない。

国籍、年齢、性別、カメラ機種、縦横比は固定しない。利用者の指定、人物設定、参照資料を正本とする。SNS／UGCの指定だけがある場合は、日常のスマートフォン撮影を既定にしてよい。

現在画像の場面を維持した人物の顔・体型補正や、別人物を同じ場面へ再現する依頼では、生成前に必ず[現在画像を土台にした人物再現](references/reference-led-subject-reshoot.md)を読む。通常の新規生成では読まない。

## 参照画像の役割を先に固定する

生成前に、各画像の担当を次から一つ以上割り当てる。

- `identity`: 顔骨格、目鼻口、輪郭、年齢感、固有特徴
- `hair`: 色、hairline、分け目、前髪、顔周り、長さ、カット、毛量、質感、スタイリング、外形
- `body`: 頭と肩のスケール、肩幅と傾斜、胸郭、バスト、胴の奥行きと長さ、ウエスト、骨盤、ヒップと臀部、太腿、膝、ふくらはぎ、脚長、胴脚比率、正面幅・側面奥行き・背面体積
- `outfit`: 形、丈、色柄、素材、装飾、重なり、靴
- `environment`: 場所、面、奥行き、物の配置、その場にある光源
- `composition`: カメラ位置、画角、crop、ポーズ、人物と物の配置
- `capture`: 露出、色、コントラスト、被写界深度、処理感などの撮影特性
- `plate`: 人物再現時の現在画像。場面、カメラ、crop、ポーズ、表情動作、髪型の外形、衣装、手、小物、背景、光、撮影特性だけを担当し、選択された顔や体型の解剖学的基準にはしない

一つの参照から担当外の要素を移さない。人物シートの白Tシャツ、デニム、白背景、ラベル、ガイド、シート配置は、明示的に衣装や構図へ指定されない限り完成画像へ移さない。構図ラフの線や注釈も描画しない。

複数の顔写真は平均顔へ混ぜず、一人の固定された顔を説明する相補的な観察として使う。人物シートは正面幅、側面奥行き、背面体積を一つの身体として読む。髪の正本を顔写真と人物シートのどちらに置くかも明記し、担当外の髪型を移さない。参照にない衣装、背景、構図は文章と用途から自然に補完する。

## プロンプトの組み立て順

抽象的な「変えない」「自然にする」を反復せず、次の工程を具体的に書く。

1. 画像ごとの担当と、移してはいけない付随要素を宣言する。
2. 顔参照があれば、一人の安定した顔骨格とパーツ関係を復元する。
3. 髪参照があれば、髪型の外形と内部の毛束仕様を分けて復元する。
4. 体型参照があれば、正面幅、側面奥行き、背面体積から一つの身体を復元する。
5. 構図のカメラ、crop、関節位置、視線、接触関係を解く。
6. 復元した人物をそのポーズへ投影し、衣装を身体へ自然に着せ、環境へ配置する。
7. 人物実在感契約と、用途に合う撮影実在感契約を適用する。
8. 顔、髪、体型、衣装、物理関係、光、撮影感を担当資料ごとに照合してから出力する。

## 人物実在感契約

人物が写る場合は、必要な要素だけをプロンプトへ統合する。

```text
Reconstruct one coherent adult person from the identity evidence instead of averaging toward a generic beauty template. Keep realistic facial structure and harmonious feature placement, including reference-supported contour, bone structure, eye spacing, brows, nose, lips, age cues, and small stable asymmetries.

Keep plausible eye size, visible sclera, eyelid thickness, and subtle left-right differences. Render living skin with restrained pores, fine facial hair, faint redness, tonal variation, and natural shadow transitions. Render hair as varied locks with modest flyaways, loose strands, and irregular grouping.

Preserve the subject's attractive, clean, refined, and approachable presentation, but do not obtain beauty by perfect symmetry, enlarged eyes, cosmetic averaging, beauty-filter smoothing, plastic gloss, waxy skin, uniform highlights, or perfectly separated hair strands.
```

「一般人らしさ」は人物を地味にしたり欠点を追加したりする意味ではない。撮られ方、表情、光、画像処理を広告撮影から日常側へ戻す。参照にないほくろ、左右差、肌荒れなどを自然さの記号として発明しない。

## 撮影実在感契約

SNS／UGC用途では次を基礎にする。

```text
Finish the scene as a plausible everyday social-media photograph rather than a studio advertising image. Use a smartphone-like casual capture unless another camera is specified. Let the light come from windows, sky, or fixtures that exist in the scene, with restrained exposure, white balance, local contrast, and processing.

Let the expression arise from the depicted moment: small natural movement around the eyes and mouth, not a mechanically perfected smile. Preserve beautiful presentation while prioritizing lived-in plausibility and natural, scene-supported imperfection.

Avoid CG-like materials, synthetic edge gloss, excessive micro-contrast, over-retouched skin, stock-photo staging, and other generated-image polish. Retain modest sensor texture, small focus variation, or slight motion evidence only when the scene supports it; do not force blur, noise, camera shake, or low resolution onto a clean image.
```

高性能カメラ、スタジオ照明、意図的な広告写真を利用者が指定した場合は、その指定を優先する。その場合も肌、髪、素材をCG化せず、現実の撮影として成立させる。

## 物理整合性

人物、スマートフォン、小物、鏡、画面、紙面がある場合は、カメラ位置、人物の向き、視線対象、手の接触、見える面を一つの行為として説明する。見えない画面内容を無理に描かせない。鏡像、手指、小物の重なり、接地、影、窓光の方向を生成前に確認する。

## 生成と再試行

- 既定は一枚を生成し、原寸で確認する。比較を求められた場合だけ、構図や撮影方針が明確に異なる候補を作る。
- 失敗時は、同じ否定表現を増やさない。`identity`、`hair`、`body`、`outfit`、`geometry`、`lighting`、`capture`のどこが外れたかを特定し、その工程を具体化して再生成する。
- 「元資料から作り直す」場合は、失敗画像や直前の生成画像を入力に含めない。
- 参照役割を変えず、別候補の画像を次候補の参照にしない。
- 利用者が編集を指定していない限り、生成済み画像の局所編集へ切り替えない。

## 目視確認

生成前に参照画像、生成後に結果を実際に開く。次を目視し、promptの語句やhashだけを品質根拠にしない。

- 顔が参照人物または人物設定と同じ一人に見える
- 髪色、hairline、分け目、前髪、長さ、外形が髪の担当資料に合う
- 頭と肩、肩、胸郭、バスト、胴、ウエスト、骨盤、ヒップ、臀部、太腿、膝、ふくらはぎ、脚長の比率と奥行きが体型資料に合う
- 衣装の形、丈、素材、重なり、靴が衣装資料に合う
- 目、肌、髪、歯、手指、素材境界にCG光沢や生成破綻がない
- 表情が場面から生じ、笑顔や左右対称が作り込まれすぎていない
- 光源、影、反射、露出、色温度が同じ空間として説明できる
- カメラ位置、crop、ポーズ、視線、手、小物、接触関係が成立する
- スマホ感を作るための過剰なノイズ、ぼけ、低解像度化がない
- 不要な文字、ロゴ、透かし、比較枠、参照シートの要素が混入していない

`request.json`には通常項目に加えて、使用した参照画像と役割、生成モード、`human-appearance-realism-v1`、SNS／UGCなら`social-capture-realism-v1`、制御撮影なら`controlled-reference-realism-v1`を記録する。`review.json`には実際に観察した合否と、残る差だけを記録する。

## 完了報告

採用画像を表示し、保存先、使用した参照役割、比率、撮影方針、残る制約を短く報告する。候補がある場合は採用品を明示し、候補を採用品として報告しない。
