---
name: generate-i2v-web-loop
description: 生成済み静止画からWeb掲載用のimage-to-video動画を生成し、固定カメラ、レイアウト維持、ループ、無音化、品質検査、複数モデル比較HTMLまで一貫して処理する。既定ではKamui MCPを使う。ユーザーがMagnific、Kling 3.0 Omni、このサイトで動画生成、Magnific画面での実行を明示した場合はmagnific-i2v-coreを併用してブラウザUIで実行する。Webサイト用のループ動画、静止画への微細な動き付け、固定構図の短尺動画、複数i2vモデル比較に使用する。動画化する元画像がない場合はgenerate-t2i-web-isometricなど目的に合う画像作成スキルを先に使用する。
---

# Web向けi2vループ動画生成

## 原則

- 元画像の構図、比率、文字、ロゴ、UI、余白、色を優先して維持する。
- ループ用途では同じ画像を開始・終了フレームへ指定する。
- 生成ジョブは必ず1件ずつ実行し、完了・保存後に次を送信する。
- 最終動画から音声ストリームを除去する。
- Web素材では4Kを使用せず、実表示サイズに必要な最低限の解像度を選ぶ。
- 生成providerは、ユーザー指定がなければKamui MCPにする。ユーザーがMagnific利用を明示した場合だけMagnificへ切り替える。
- Kamuiでユーザーがモデルを指定しない場合は、カタログ上で有効なモデルのうち、最低解像度で推定単価が最も安いモデルを1件だけ選ぶ。

Kamui MCPのモデル選択、MCP設定、逐次生成、再開、音声除去、検査、比較HTML、基本出力契約は [kamui-i2v-core](../kamui-i2v-core/SKILL.md) を読む。モデル名、MCP URL、ツール名、価格、解像度は [models.json](../kamui-i2v-core/references/models.json) だけで管理する。モデル更新時にこのスキルのスクリプトへ値を直接追加しない。

Magnificを使う場合は [magnific-i2v-core](../magnific-i2v-core/SKILL.md) を読み、Browser skillでMagnificの動画生成UIを操作する。MagnificはブラウザUI依存なので、`scripts/generate.py`へ無理に渡さない。

## 実行手順

### 1. 入力を確認する

入力画像を表示し、寸法と比率を確認する。元画像がない場合は、先に目的に合う画像作成スキルで静止画を作る。LP、記事LP、企業サイト、サービスサイト向けのアイソメ画像なら [generate-t2i-web-isometric](../generate-t2i-web-isometric/SKILL.md) を読む。

- `<task>`: 今回の目的を表す小文字英数字とハイフンの名前
- 動かす既存要素: 1〜3種類
- 動かさない要素: 文字、ロゴ、UI、主要な輪郭
- 長さ: ループは原則4秒
- 比率: 入力画像と同じ比率

詳細は [quality-guide.md](references/quality-guide.md) を読む。Web上の表示幅から必要解像度を決める場合は [web-delivery.md](references/web-delivery.md) も参照する。

### 2. モデルを決める

まずproviderを決める。

- 指定なし: Kamui MCP。
- `Magnific`、`Kling 3.0 Omni`、`このサイトで動画生成`などの指定あり: Magnific。

Kamuiの場合、ユーザー指定がなければ、モデルを指定せず実行する。現在の既定値はSeedance 2.0 Miniの最低解像度だが、必ず共通JSONカタログから動的に選択させる。`<skill>/scripts/generate.py`はKamui互換ラッパーで、内部では `../kamui-i2v-core/scripts/generate.py --mode loop` を実行する。

```bash
python3 <skill>/scripts/generate.py INPUT_IMAGE \
  --task TASK_NAME \
  --mode loop \
  --prompt-file PROMPT_FILE
```

モデル指定時は`--model`を繰り返す。

```bash
python3 <skill>/scripts/generate.py INPUT_IMAGE \
  --task TASK_NAME \
  --mode loop \
  --model kling-o3-standard \
  --model seedance-2.0-fast \
  --prompt-file PROMPT_FILE
```

利用可能モデルは次で確認する。

```bash
python3 <skill>/scripts/generate.py --list-models
```

Magnificの場合は、`../magnific-i2v-core/references/models.json`と実際のUI表示を見てモデル、解像度、秒数、比率、消費表示を確認する。ユーザー指定がない限り、UIで確認できる最安・最低解像度を選ぶ。入力画像や終了画像の設定で比率がUI側に固定される場合は、実際の比率を記録して報告する。

### 3. プロンプトを作る

[prompt-guide.md](references/prompt-guide.md) のテンプレートを基準に、入力画像の内容へ合わせて英語で具体化する。

- カメラ完全固定を明記する。
- 動かす既存要素だけを列挙する。
- 文字を生成・再描画・変形しないよう明記する。
- 開始と終了で元画像へ完全に戻すよう明記する。
- 大きな移動、場面転換、追加物を禁止する。

モデル比較では全モデルに同じpositive promptを渡す。モデル固有のnegative promptは、比較条件を変えるため既定では追加しない。

### 4. 生成providerごとに設定する

Kamuiの場合、MCP設定は [kamui-i2v-core](../kamui-i2v-core/SKILL.md) の手順に従う。`generate.py`は`../kamui-i2v-core/scripts/setup_mcp.py`を通じて、対象プロジェクトに`.mcp.json`がなければ初期配置元からコピーし、実行対象モデルの設定をマージする。

```bash
python3 <skill>/scripts/setup_mcp.py --project PROJECT_ROOT --model MODEL_SLUG
```

設定だけ行う場合は上記を使う。`.mcp.json`の初期配置、既存設定とのマージ、`KAMUI_CODE_PASS_KEY`の扱いはこのスキル側で再定義しない。

詳細は [mcp-setup.md](../kamui-i2v-core/references/mcp-setup.md) を読む。

Magnificの場合、MCP設定は不要。Browser skillを読み、[magnific-i2v-core](../magnific-i2v-core/SKILL.md) の手順でMagnificの動画生成UIを操作する。

### 5. 逐次生成する

Kamuiの場合、`generate.py`へ複数モデルを渡しても、内部では次をモデルごとに直列実行する。

1. MCP初期化
2. `submit`
3. `status`をポーリング
4. `result`を取得
5. 動画をダウンロード
6. 音声を除去
7. 出力を検査
8. 次のモデルへ進む

中断後は同じコマンドを再実行する。保存済みMP4はスキップし、送信済み`request_id`があるジョブは再課金せずポーリングから再開する。意図的に再生成する場合だけ`--overwrite`を使う。

課金前の計画確認には`--dry-run`を使う。

Magnificの場合も1件ずつ実行する。ループ用途では開始画像と終了画像に同じ画像を入れるか、UIが終了画像を受け付けない場合はプロンプトで開始末尾の一致を強く指定する。完了後は詳細画面からMP4本体をダウンロードし、`ffprobe`で確認してから出力契約に合わせて保存する。

### 6. 検査する

Kamuiでは生成後、`generate.py`が`inspection.json`と`_inspection/`内の5点コンタクトシートを作成する。MagnificではMP4を出力契約に合わせて保存した後、同じ検査スクリプトを手動実行する。必要に応じて再検査する。

```bash
python3 <skill>/scripts/inspect_videos.py output/TASK_NAME
```

次を確認する。

- 音声ストリームが0件
- 長さが要求値に近い
- 入力と出力の比率差が1%以内
- 文字、ロゴ、UIが全フレームで安定
- カメラ移動やクロップがない
- 先頭・末尾フレームが十分近い
- 境界で動きの速度や方向が急変しない
- コンタクトシート上で文字、ロゴ、主要オブジェクトが変形していない
- 急な場面変化が検出されていない

SSIMは静止フレームの近さだけを測る補助指標であり、シームレスループを保証しない。必ず`index.html`で複数回ループ再生して目視確認する。

### 7. 比較ページを作る

複数モデル時は自動作成する。単一モデルでも必要なら実行する。

```bash
python3 <skill>/scripts/build_comparison.py output/TASK_NAME
```

HTMLは [comparison-template.html](../kamui-i2v-core/assets/comparison-template.html) を使い、全動画に`autoplay muted loop playsinline`を設定する。全体の再生、停止、先頭から再生、速度変更を提供する。

### 8. 採用動画をWeb配信用に仕上げる

比較と検査で採用動画を決めた後、元動画を上書きせず`_delivery/`へ配信用成果物を作る。

```bash
python3 <skill>/scripts/postprocess.py output/TASK_NAME \
  --model MODEL_SLUG \
  --repair none
```

既定ではループ補修を加えず、H.264 MP4、VP9 WebM、WebP posterへ変換する。目視で境界問題がある場合だけ`trim`、`crossfade`、`pingpong`を選ぶ。補修方式の判断は [loop-repair.md](references/loop-repair.md)、HTML実装と配信解像度は [web-delivery.md](references/web-delivery.md) に従う。

文字やロゴの変形、カメラ移動、構図変化は後処理で隠さず再生成する。後処理条件を変更する場合は`--overwrite`を明示する。

## 出力

基本出力はKamuiの場合 [kamui-i2v-core](../kamui-i2v-core/SKILL.md)、Magnificの場合 [magnific-i2v-core](../magnific-i2v-core/SKILL.md) の出力契約に従い、このスキル側で再定義しない。

Web配信用の後処理を行った場合だけ、タスク出力ディレクトリ内の`_delivery/`へH.264 MP4、VP9 WebM、WebP poster、`delivery-manifest.json`を追加する。

ユーザーへは動画、比較HTML、主要な検査結果、未解決の品質問題を報告する。生成料金の概算と実課金が一致するとは断定しない。

## 必要環境

- Python 3.9以上。外部Pythonパッケージは不要。
- Kamui Code Pass Key。
- `ffmpeg`と`ffprobe`。無音化と検査に使う。
- インターネット接続。

依存コマンドがない場合は課金ジョブ開始前に停止する。
