# Web配信ガイド

## 目次

- 配信解像度
- 配信ファイル
- HTML
- reduced motion
- 読み込み性能
- アクセシビリティ

## 配信解像度

必要な入力幅の目安を次で求める。

```text
必要ピクセル幅 = CSS表示幅 × 想定Device Pixel Ratio
```

通常はDPR 2までを基準にし、実表示より大幅に大きな動画を配信しない。

- CSS幅320px以下: 480p級を検討する。
- CSS幅360〜640px: 720p級を基準にする。
- CSS幅640px超または大きなヒーロー: 必要な場合だけ1080p級を使う。
- 4Kはこのワークフローの対象外とする。大きなヒーローでもまず1080p級までで実表示を検証する。

モデルへ指定した`720p`などの名前と実ピクセル寸法は一致しない場合がある。必ず`inspection.json`の実寸を使う。

## 配信ファイル

採用動画へ`postprocess.py`を実行する。

```bash
python3 <skill>/scripts/postprocess.py output/TASK_NAME \
  --model MODEL_SLUG \
  --repair none
```

次を`output/TASK_NAME/_delivery/`へ作る。

- H.264 MP4: `yuv420p`、`faststart`、音声なし
- VP9 WebM: 音声なし
- WebP poster: 配信動画の先頭フレーム
- `delivery-manifest.json`: 実際の仕様と修復方式

## HTML

```html
<picture class="loop-visual__fallback">
  <img src="/assets/example-poster.webp" alt="">
</picture>

<video
  class="loop-visual__video"
  autoplay
  muted
  loop
  playsinline
  preload="metadata"
  poster="/assets/example-poster.webp"
  aria-hidden="true"
>
  <source src="/assets/example.webm" type="video/webm">
  <source src="/assets/example.mp4" type="video/mp4">
</video>
```

装飾動画では`aria-hidden="true"`を使う。動画だけが持つ意味やメッセージは、近接するHTML本文または適切な代替テキストにも含める。

## reduced motion

```css
.loop-visual__fallback {
  display: none;
}

@media (prefers-reduced-motion: reduce) {
  .loop-visual__video {
    display: none;
  }

  .loop-visual__fallback {
    display: block;
  }
}
```

JavaScriptで自動再生を開始する場合も、`prefers-reduced-motion`がreduceなら再生しない。

## 読み込み性能

- 通常は`preload="metadata"`を使う。
- 動画をLCP候補にせず、posterを先に表示する。
- ファーストビュー外の動画はIntersection Observerで表示直前に読み込む。
- MP4へ`faststart`を設定し、メタデータをファイル先頭へ移す。
- 実機回線でMP4とWebMの容量を比較し、不要な形式は配信しない。

## アクセシビリティ

- 自動再生動画は無音にする。
- 点滅や急激な明暗変化を避ける。
- 動画の上へ載せるテロップはDOMテキストにする。
- CTAや重要情報を動画内だけに置かない。
