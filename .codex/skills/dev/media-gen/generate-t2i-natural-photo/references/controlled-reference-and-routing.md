# 制御撮影と適用先

日常のSNS写真と、比較可能な人物資料では同じ自然さを使わない。生成物の目的を先に選ぶ。

## 適用表

| 生成物 | 契約 |
|---|---|
| 顔候補、顔ポートフォリオ | `human-appearance-realism-v1` + `social-capture-realism-v1` |
| 初回投稿完成画像、日常SNS、UGC | `human-appearance-realism-v1` + `social-capture-realism-v1` |
| ベーシック人物、人物シート、人物付き衣装シート | `human-appearance-realism-v1` + `controlled-reference-realism-v1` |
| 顔・体型の人物再現 | 人物再構築後、現在画像の`capture`を再適用 |
| 注釈による局所修正 | 修正領域を現在画像周辺の肌、髪、素材、光、撮影特性へ合わせる |
| クリーン再構築 | 自然な肌、髪、素材を再構築し、ノイズ、手ブレ、低解像度を追加しない |
| マネキン、共通衣装、衣装単体、背景資料、構図ラフ | 人物実在感契約を適用しない |

国籍、年齢、性別は各人物設定または依頼を正本とし、どの契約にも固定しない。

## controlled-reference-realism-v1

人物比較資料、キャラクターシート、三面図では`character-sheet-imagegen`を使い、次を撮影契約へ統合する。

```text
Use a controlled reference-sheet presentation: neutral white background, stable even light, consistent scale, and clear comparable detail.

Do not introduce everyday scenery, smartphone degradation, camera shake, added noise, or casual depth effects. Preserve living human skin, natural hair grouping, and real fabric response within the controlled setup.
```

日常写真らしさを出すための背景、手ブレ、スマホノイズを人物資料へ持ち込まない。一方で、制御撮影を理由に肌を無孔のCG面、髪を均一な線、衣服を合成樹脂のような表面へ変えない。

## 同梱配置テンプレート

利用者が別のレイアウトを指定していない場合は、[character-sheet-layout-template.png](../assets/character-sheet-layout-template.png)を`template-layout`として使う。

- 寸法: 1448×1086（4:3）
- SHA-256: `2e8983961454d8d2b0f4bd4a6ca575e8a6c3c31840145d344a000abd04c90134`
- 構造: 左に同寸の3枠、右に正面・真横・背面と共通水平ガイド
- 表示文字: `表情`、`正面`、`側面`、`背面`だけ

この画像は配置だけの基準であり、顔、髪、身体、衣装、肌、光、人物identityの根拠にしない。人物シートでは左3枠を表情へ使い、マネキン、体型、衣装資料では個別契約に従って空欄にできる。テンプレートの水平ガイドは三方向の頭頂、肩、腰、足元を比較可能に揃えるために使い、身長数値や追加ラベルを発明しない。

## 人物資料の参照分離

- 顔: 骨格、目鼻口、輪郭、年齢感、固有特徴。
- 髪: hairline、色、分け目、前髪、顔周り、長さ、カット、毛量、質感、全方向の外形。
- 身体: 正面幅、真横の奥行き、背面体積を一体として固定する。
- 衣装: 同一の衣装仕様を全ビューへ適用し、身体をpadding、compression、reshapingしない。
- layout: 枠、ラベル、余白、配置だけに使い、人物や衣装の基準にしない。

全ビューで顔、髪、身体、年齢、衣装、光を揃える。人物資料はSNS完成画像ではないため、自然な表情差を設けても撮影条件や人物仕様は変えない。
