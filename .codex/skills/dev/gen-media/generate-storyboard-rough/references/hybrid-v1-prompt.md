# Hybrid v1 白黒ラフ絵コンテプロンプト

画像生成直前にこのファイルを最後まで読み、次のテンプレートの固定文を削らず、変数だけを直接観察した内容で置き換える。

## 変数

- `ASPECT_RATIO`: 入力画像の実寸に最も近い対応比率。
- `SOURCE_WIDTH` / `SOURCE_HEIGHT`: 入力画像の実寸。
- `OBSERVED_DESCRIPTION`: ショットサイズ、crop、人物・部位の配置、ポーズ軸、小物、背景の大きな面だけを書く。
- `FRAMING_LOCK`: 頭、手、肩など主要anchorの画面内相対位置・大きさと、身体が画面端またはoverlayで見切れる位置を書く。
- `VISIBLE_COUNTS`: `persons=N, faces=N, hands=N, other visible body parts=N`の形式で書く。
- `CLOTHING_ACCESSORY_GUARD`: 服・髪の大きな外形と存在するアクセサリーだけを書く。精密描画を命令しない。
- `MASKED_REGION_DESCRIPTIONS`: overlayをブラーした場合だけ使う。各領域で続く最も単純な身体・小物・背景面と、追加してはいけない要素を書く。

## 固定テンプレート

```text
Use case: illustration-story
Asset type: rough storyboard production note
Input image: edit target and visual layout reference. Use it only for camera framing, composition, subject placement, pose axes, visible body segments, visible object placement, and background geometry.
Primary request: Convert the input image into one black-and-white rough storyboard / rough name sketch. This is an unfinished production layout note for video planning, not a portrait, clean line drawing, or finished illustration.
Hybrid approach variant 1 — layout construction first: preserve the spatial layout visible in the input image, including the exact original framing, subject scale, crop, pose, visible object placement, background geometry, and existing crop intersections.
Hard framing lock: FRAMING_LOCK. Keep these anchors at the same normalized canvas positions and scale. Do not zoom out, zoom in, reframe, recenter, uncrop, or reveal more of the subject or scene than the input image shows.
Draw the image as an unfinished video layout rough: head oval, face cross guide, torso axis, shoulder direction, arm axis, hand placement, visible object placement, background geometry guides, and only the body segments that are actually visible up to their existing crop or occlusion boundaries.
Use the entire canvas edge to edge for the composition. This means no added border or padding; it does not permit zooming out or revealing additional scene content. The canvas edges are the shot boundary; do not draw any enclosing perimeter line, camera frame, storyboard panel border, picture frame, matte, white margin, or blank padding inside the image.
Keep loose construction strokes, search lines, overlaps, and correction strokes visible throughout the subject and background.
Face should be simple: oval, cross guide, dots or short marks for eyes and mouth, not a detailed beauty portrait.
Body and clothing should be simple block, axis, and tube construction for reading pose, not anatomy rendering or garment rendering.
Aspect ratio: ASPECT_RATIO from source SOURCE_WIDTHxSOURCE_HEIGHT.
Black ink lines on a plain white ground only. No color, gray wash, shading, shadows, fills, gradients, halftone, painted areas, or solid black hair masses.
No text, captions, subtitles, logos, numbers, typography, watermarks, arrows, attention arrows, motion arrows, decorative symbols, icons, focus lines, or finished character illustration anywhere in the image.

Layout guard only:
OBSERVED_DESCRIPTION
Visible subject count guard: VISIBLE_COUNTS. Do not add extra people, faces, hands, body parts, props, accessories, patterns, furniture, or decorations.
Accessory guard only, not a rendering instruction: CLOTHING_ACCESSORY_GUARD
```

## ブラー領域がある場合だけ追加する節

```text
Masked overlay layout guard:
MASKED_REGION_DESCRIPTIONS
Blurred pixels are occluded source information, not permission to complete hidden anatomy or reveal a wider shot. Continue only the simplest directly supported clothing or background planes needed to remove the overlay, using sparse unresolved construction lines where the source is uncertain. Preserve the source subject scale and crop. Do not render clothing detail from the blur. Do not invent or fully resolve hidden limbs, lower body, people, faces, hands, body parts, props, accessories, furniture, text, icons, or decorations.
```

## 組み立て規則

1. ブラー領域がなければ追加節を含めない。
2. 入力画像にない物語、動作の前後、人物の感情、小物、装飾を追加しない。
3. `OBSERVED_DESCRIPTION`へ服の素材、襟、袖口、しわ、髪の毛流れを詳述しない。
4. 失敗理由を大量に追記せず、この短い骨格を維持する。
5. 修正生成では問題を1つだけ明記し、固定テンプレートの禁止事項と構図保持を再指定する。
