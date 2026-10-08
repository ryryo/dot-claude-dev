# プロンプトガイド

## ループ用テンプレート

角括弧内だけを入力画像に合わせて変更する。

```text
Create a perfectly seamless, subtle [DURATION]-second loop from this exact website image.
Keep the camera completely locked. Preserve the original composition, aspect ratio, framing, background, typography, logos, spacing, object positions, proportions, colors, outlines, and every graphic detail exactly as provided.

Animate only [MOVING ELEMENTS]. The motion is limited to [MOTION DESCRIPTION]. Keep all movement small, smooth, cyclical, and visually subordinate to the website content. Keep [FIXED ELEMENTS] completely fixed.

The first and last frames must match the supplied image exactly. All motion must ease in, ease out, reverse naturally, and settle completely back to the original state before the final frame.

No new objects, no removed objects, no camera movement, no zoom, no pan, no tilt, no shake, no parallax, no perspective change, no crop, no reframing, no layout change, no text animation, no text deformation, no logo deformation, no flicker, no morphing, no scene cut, and no audio.
```

## 固定カメラ・1メッセージ用テンプレート

ループ不要の場合に使う。テロップは生成後にHTML/CSSで重ねる。

```text
Create a short image-to-video shot using this exact source image.
Keep the camera completely locked in its original position. Preserve the original composition, framing, perspective, background, colors, lighting direction, subject identity, object count, and spatial relationships.

The subject is [SUBJECT]. The subject performs one clear, natural action: [ACTION]. Keep the motion readable, controlled, and contained within the existing frame. [ENVIRONMENT MOTION].

Use a single continuous shot. No camera movement, no zoom, no pan, no tilt, no shake, no reframing, no crop, no perspective change, no scene cut, no transition, no new objects, no disappearing objects, no text, no captions, no logos, no UI, no morphing, and no exaggerated motion.
```

## Negative prompt

比較実験ではモデル間の条件を揃えるため原則使用しない。単一モデルを詰める段階で、対応モデルにだけ使う。

```text
camera movement, zoom, pan, tilt, dolly, orbit, shake, handheld camera, reframing, crop, perspective change, scene cut, transition, multiple shots, new objects, disappearing objects, duplicated objects, text, subtitles, captions, letters, logos, UI, watermark, morphing, flicker, distorted face, deformed hands, extra fingers, color shift, background change
```

## 動き指定例

図解:

```text
[MOVING ELEMENTS]: the existing indicator lights, signal lines, and machine mechanisms
[MOTION DESCRIPTION]: one soft signal pulse and one barely perceptible operating cycle that return to their exact original state
[FIXED ELEMENTS]: the headline, labels, background, people, object positions, and all layout elements
```

人物:

```text
[MOVING ELEMENTS]: the subject's eyes, breathing, hair tips, and clothing edges
[MOTION DESCRIPTION]: one natural blink, barely perceptible breathing, and a gentle sway that returns to the exact starting pose
[FIXED ELEMENTS]: the face identity, hands, product, background, typography, and framing
```
