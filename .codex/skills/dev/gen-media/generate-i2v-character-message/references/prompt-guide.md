# プロンプトガイド

## 目次

- 固定カメラ人物用テンプレート
- 動き指定例
- 避ける指定
- テロップ方針

## 固定カメラ人物用テンプレート

角括弧内だけを案件ごとに置き換える。

```text
Create a short image-to-video shot using this exact source image.
Keep the camera completely locked in its original position. Preserve the original composition, framing, perspective, background, colors, lighting direction, subject identity, object count, and spatial relationships.

The subject is [SUBJECT]. The subject performs one clear, natural action: [ACTION]. Keep the motion readable, controlled, modest, and contained within the existing frame. [ENVIRONMENT MOTION].

Use a single continuous shot. No camera movement, no zoom, no pan, no tilt, no shake, no reframing, no crop, no perspective change, no scene cut, no transition, no new objects, no disappearing objects, no text, no captions, no logos, no UI, no morphing, no hand deformation, no extra fingers, no face distortion, and no exaggerated motion.
```

## 動き指定例

財布や資料を見せる人物:

```text
[SUBJECT]: a professional Japanese woman around 35 years old, wearing a light gray blouse and dark pants, holding a burgundy wallet
[ACTION]: she gives a small friendly nod, blinks once naturally, keeps a cheerful smile, and makes a very subtle thumbs-up emphasis while continuing to hold the wallet in the same position
[ENVIRONMENT MOTION]: Add only tiny natural movement in hair tips and clothing edges as if captured in a casual smartphone video frame
```

悩み共感の人物:

```text
[ACTION]: the subject looks at the document, exhales softly, then gives a small relieved nod without moving from the original pose
```

解決後の人物:

```text
[ACTION]: the subject smiles slightly, blinks once, and raises the product or document by only a few centimeters
```

## 避ける指定

- walking, turning around, dancingなどの大きな動作
- camera movementやhandheld camera
- speakingやlip sync
- dramatic expression change
- new text、subtitle、caption
- new product、new logo

## テロップ方針

日本語テロップをi2vモデルに生成させない。文字化け、揺れ、綴り変化、フレーム間変形が起きやすい。必要な場合は生成後にHTML/CSSで重ねるか、`burn_telop.py`で焼き込む。
