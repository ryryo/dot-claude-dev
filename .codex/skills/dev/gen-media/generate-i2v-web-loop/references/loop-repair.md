# ループ修復ガイド

## 目次

- 修復前の判断
- 修復順序
- trim
- crossfade
- ping-pong
- 再生成

## 修復前の判断

`inspection.json`のSSIMだけで決めず、`index.html`を5回以上連続再生する。次を分けて考える。

- 見た目の差: 最終フレームと先頭フレームの形や色が違う。
- 動きの差: 見た目は近いが、速度や方向が境界で跳ねる。
- 構図の破綻: カメラ、文字、オブジェクトが途中で変化する。

構図の破綻は後処理で隠さず再生成する。

## 修復順序

1. 動かす要素と動きの量を減らして再生成する。
2. プロンプトへ`all motion settles completely before the final frame`を追加する。
3. 末尾の不安定区間だけをtrimする。
4. 小さな差だけならcrossfadeを試す。
5. 往復可能な動きだけping-pongを試す。
6. どれも不自然なら別モデルで再生成する。

後処理は元動画を上書きせず、`_delivery/`へ出力する。

## trim

末尾だけが崩れる場合に使う。

```bash
python3 <skill>/scripts/postprocess.py output/TASK_NAME \
  --model MODEL_SLUG \
  --repair trim \
  --trim-end 0.25
```

トリミング後の最終フレームと先頭フレームを再検査する。単に短くするだけで境界が悪化する場合もある。

## crossfade

背景の明るさや輪郭がわずかに違う場合に使う。

```bash
python3 <skill>/scripts/postprocess.py output/TASK_NAME \
  --model MODEL_SLUG \
  --repair crossfade \
  --crossfade-duration 0.3
```

末尾から先頭へ短くブレンドする。文字、ロゴ、細線に二重像が出る場合は使わない。0.2〜0.4秒を目安にし、長いcrossfadeで破綻を隠さない。

## ping-pong

光、呼吸、布の揺れなど、逆再生しても意味が変わらない動きに使う。

```bash
python3 <skill>/scripts/postprocess.py output/TASK_NAME \
  --model MODEL_SLUG \
  --repair pingpong
```

歩行、搬送、液体、煙、読み書き、物体の出現・消失には使わない。再生時間は概ね2倍になる。

## 再生成

次の場合は後処理より再生成を優先する。

- 文字やロゴが中間フレームで変形する。
- カメラが移動する。
- 人物の顔、手、指が破綻する。
- オブジェクトの数や位置が変わる。
- 色や背景が動画全体で変化する。

再生成では一度に1条件だけ変更し、原因を追跡できるようにする。
