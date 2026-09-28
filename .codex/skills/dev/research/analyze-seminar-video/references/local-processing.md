# ローカル処理の手順

以下のパスは例。`SKILL_DIR` は読んだSKILL.mdのディレクトリ、入力は利用者指定の絶対パス、出力はそのタスクの新規ディレクトリに置き換える。シェルへ値を渡すときは引用する。

## MLX Whisper

Apple Silicon、FFmpeg/ffprobe、Python、mlx-whisperが必要。既存の環境とモデルキャッシュを優先する。以下はmlx-whisper 0.4.3を使う例で、モデルは引数で変更可能。

```bash
uv run --offline --python 3.11 --with mlx-whisper==0.4.3 python \
  "$SKILL_DIR/scripts/transcribe.py" "/absolute/seminar.mp4" \
  --out "/absolute/report/transcription" --language ja
```

初回に依存やモデルがなければ、不足を説明し、ネットワーク取得が許される環境で `uv` の `--offline` を外し、スクリプトへ `--allow-download` を追加する。音声認識の実行はローカルで、動画や音声を外部認識APIへアップロードしない。オフライン指定がある場合は取得せず、不足モデルを報告する。

スクリプトは動画の尺を検出し、既定480秒単位の16kHzモノラル音声を一時生成する。`--chunk-seconds` で変更可能。完了済みの分割を保存して再開できる。再開時に動画のhash・設定が違えば停止するため、新しい出力ディレクトリを使う。同じ出力先への同時実行はしない。

- `manifest.json`: 元動画hash、尺、認識条件、処理状態。
- `part-*.json`: 生ASR、元動画へのoffset、分割尺。
- `transcript.json`: 生ASRを元動画時刻へ変換した有効範囲のsegments。分割範囲外の時刻は除外またはclampし、変更件数を保存。厳密な発話境界ではない。
- `transcript.txt`: 時刻付き、`full-transcript.txt`: 時刻なしの自動文字起こし。未校正。

分割境界付近で発言が途切れた場合は、その前後を含むWAVを別途切り出して再認識し、元区間のoffsetと補足として保存する。生ASRを無言で上書きしない。

## FFmpegで画像・クリップを抽出

まず `ffprobe -v error -show_format -show_streams -of json INPUT` でメタデータを読む。以下はFFmpegの引数例。秒は元動画基準、durationは終了秒−開始秒。既存ファイルを守るため `-n` を使う。

```bash
# 画像。指定秒にseekして1フレーム保存する。
ffmpeg -v error -nostdin -n -ss 123.4 -i INPUT -frames:v 1 frame.png

# スライド領域の例。cropは幅:高さ:x:y。実画像に合わせて決める。
ffmpeg -v error -nostdin -n -ss 123.4 -i INPUT \
  -vf 'crop=1280:720:100:80' -frames:v 1 slide.png

# 全体の概観。2分間隔は長尺セミナーの出発点で、網羅性を保証しない。
ffmpeg -v error -nostdin -n -i INPUT \
  -vf 'fps=1/120,scale=960:-2' overview-%04d.jpg

# 20秒の動画クリップ。H.264/AAC、偶数寸法、ブラウザー向け。
ffmpeg -v error -nostdin -n -ss 300 -i INPUT -t 20 \
  -map 0:v:0 -map '0:a:0?' -vf 'scale=trunc(iw/2)*2:trunc(ih/2)*2' \
  -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p \
  -c:a aac -b:a 160k -movflags +faststart clip.mp4
```

フレーム番号から時刻を推定する場合、VFR・開始時刻・fpsフィルターの丸めに注意する。概観画像の番号だけで精密な境界を確定せず、該当区間を指定時刻で再抽出する。フレーム単位の精度が必要なら元PTSを検査する。

動画をcropするときはscaleの前にcropを加える。スライドの比率を変形させない。複数cropの結合では表示領域の縦横比を保って同一キャンバスに配置し、音声は同じ元区間から保持する。編集で失われた部分を明記する。作品の元ファイルと、録画内上映の切り抜きを区別する。

## 記録とHTML

`source.json` には元動画のパス、hash、尺、解像度、対象範囲を記録する。共有する資料の本文へローカル絶対パスを露出させず、必要なら共有版からsourceパスだけ省く。

`evidence.json` の一例:

```json
{
  "assets": [{
    "id": "demo-01", "source_id": "V01", "file": "media/demo-01.mp4",
    "start_seconds": 300, "end_seconds": 320, "crop_xywh": null,
    "section": "実演の操作手順", "reason": "入力から結果までの操作を確認できる"
  }],
  "claims": [{"section": "実演の操作手順", "source_id": "V01", "asr_seconds": [295, 325], "assets": ["demo-01"]}]
}
```

HTMLでは `<video controls preload="metadata" poster="media/demo-01.jpg"><source src="media/demo-01.mp4" type="video/mp4"></video>` とMP4への通常リンクを付ける。画像・動画は `max-width:100%;height:auto`。生の発話をHTMLに埋める際はエスケープする。長い表や固有名詞でもスマートフォンでページ全体が横にはみ出さないようにする。
