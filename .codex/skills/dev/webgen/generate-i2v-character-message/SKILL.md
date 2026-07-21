---
name: generate-i2v-character-message
description: 生成済みの人物メッセージ静止画を、Web掲載用の固定カメラ短尺image-to-videoメッセージ動画としてKamui MCPで生成し、MCP設定、入力画像準備、逐次モデル実行、無音化、品質検査、比較HTML、任意の日本語テロップ焼き込みまで行う。人物が商品や資料を見せる動画、うなずき、まばたき、サムズアップ、CTA付近の短尺人物動画、SeedanceやKlingなど複数i2vモデル比較、Kamui MCP未設定プロジェクトへのローカルMCP設定が必要なときに使用する。動画化する元画像がない場合はgenerate-t2i-web-character-messageを先に使用する。
---

# 人物メッセージi2v動画生成

## 原則

- 元画像の人物ID、構図、手、持ち物、背景、比率を優先して維持する。
- カメラは完全固定にする。ズーム、パン、リフレーミング、クロップは不採用。
- 動きは1メッセージに対応する小さな動作だけに絞る。
- MCPジョブは必ず1件ずつ実行し、完了・保存後に次を送信する。
- 最終動画から音声ストリームを除去する。
- 生成モデルに日本語テロップを描かせない。テロップは任意の後処理で焼き込む。
- ユーザーがモデルを指定しない場合は、`../kamui-i2v-core/references/models.json`で有効なモデルのうち推定単価が最も安い最低解像度のモデルを1件だけ選ぶ。
- 高価なモデルや複数モデルを、ユーザーの指定なしに追加実行しない。
- 出力動画は `output/<task>/<model>.mp4` に保存する。
- 複数モデルを生成した場合は `output/<task>/index.html` も作成する。

Kamui MCPのモデル選択、MCP設定、逐次生成、再開、音声除去、検査、比較HTMLは [kamui-i2v-core](../kamui-i2v-core/SKILL.md) を読む。モデル名、MCP URL、ツール名、価格、解像度は [models.json](../kamui-i2v-core/references/models.json) だけで管理する。モデル更新時にこのスキルのスクリプトへ値を直接追加しない。

## 実行手順

### 1. 入力画像を確認する

動画化したい採用済みの人物1枚絵を確認する。キャラクターシート、参考画像、要件テキストだけをこのスキルへ直接渡さない。

- 採用済み1枚絵がある場合: その画像をi2v入力にする。
- 元画像がない場合: 先に [generate-t2i-web-character-message](../generate-t2i-web-character-message/SKILL.md) を読み、動画化用の人物静止画を作る。
- キャラクターシートや参考画像だけがある場合: 先に [source-image-guide.md](../generate-t2i-web-character-message/references/source-image-guide.md) に従い、動画化する1枚絵へ変換する。

このスキルは人物静止画の新規生成・選定を担当しない。画像作成後、採用画像パスをこのスキルへ引き渡す。

### 2. 入力画像をWeb動画用に準備する

生成済み画像にC2PAなど大きなメタデータが入っていると、Kamui側のログやモデル検証が扱いにくくなる。課金ジョブ前にメタデータを剥がした作業用画像を作る。

```bash
python3 <skill>/scripts/prepare_source.py INPUT_IMAGE \
  --task TASK_NAME \
  --project PROJECT_ROOT
```

出力された `output/TASK_NAME/_assets/source-image-prepared.jpg` をi2v入力に使う。元画像は上書きしない。

### 3. モデルを決める

ユーザー指定がなければモデルを指定せず実行する。既定では共通カタログ上の最安モデルが選ばれる。`<skill>/scripts/generate.py`は互換ラッパーで、内部では `../kamui-i2v-core/scripts/generate.py --mode message` を実行する。

```bash
python3 <skill>/scripts/generate.py output/TASK_NAME/_assets/source-image-prepared.jpg \
  --project PROJECT_ROOT \
  --task TASK_NAME \
  --prompt-file PROMPT_FILE \
  --comparison
```

モデル指定時は`--model`を繰り返す。

```bash
python3 <skill>/scripts/generate.py SOURCE_IMAGE \
  --project PROJECT_ROOT \
  --task TASK_NAME \
  --model seedance-2.0-fast \
  --model kling-v3-standard \
  --prompt-file PROMPT_FILE \
  --comparison
```

利用可能モデルは次で確認する。

```bash
python3 <skill>/scripts/generate.py --list-models
```

人物写真風の入力ではSeedance系が肖像・私的情報検証で拒否される場合がある。拒否された場合は同じ入力で再送を繰り返さず、[model-selection.md](references/model-selection.md) に従いKling O3 StandardまたはKling V3 Standardを試す。

### 4. プロンプトを作る

[prompt-guide.md](references/prompt-guide.md) の固定カメラ・人物用テンプレートを基準に、英語で具体化する。

- カメラ完全固定を明記する。
- 人物ID、服装、持ち物、表情を維持する。
- 動作は1つにする。例: 小さくうなずく、1回まばたき、親指を少し強調する。
- 手と顔の変形、指の増加、持ち物の消失を禁止する。
- 日本語テロップ、ロゴ、UI、字幕を生成させない。

モデル比較では全モデルに同じpositive promptを渡す。

### 5. MCPを設定して逐次生成する

`generate.py`は実行対象モデルをプロジェクトの`.mcp.json`へ自動的にマージする。この処理は `../kamui-i2v-core/scripts/setup_mcp.py` が担当する。

- 既存の`.mcp.json`内の他サーバーを削除しない。
- ヘッダーには`${KAMUI_CODE_PASS_KEY}`だけを保存する。
- キー本体は環境変数またはGit管理外の`.env.local`から読む。
- キーがない場合は空の`KAMUI_CODE_PASS_KEY=`を作成して停止し、ユーザーに設定を依頼する。

詳細は [mcp-setup.md](../kamui-i2v-core/references/mcp-setup.md) を読む。

中断後は同じコマンドを再実行する。保存済みMP4はスキップし、送信済み`request_id`があるジョブは再課金せずポーリングから再開する。意図的に再生成する場合だけ`--overwrite`を使う。

課金前の計画確認には`--dry-run`を使う。

### 6. 検査する

生成後、`generate.py`が`inspection.json`と`_inspection/`内のコンタクトシートを作成する。必要に応じて再検査する。

```bash
python3 <skill>/scripts/inspect_videos.py output/TASK_NAME
```

人物動画では特に次を確認する。

- 音声ストリームが0件
- カメラ移動、ズーム、クロップがない
- 顔が別人化していない
- 手、指、財布、資料などの持ち物が破綻していない
- 背景に文字、ロゴ、UIが新規出現していない
- 1メッセージに必要な動きだけが入っている

詳細は [quality-guide.md](references/quality-guide.md) を読む。

### 7. 比較ページを作る

複数モデル時は自動作成する。単一モデルでも必要なら実行する。

```bash
python3 <skill>/scripts/build_comparison.py output/TASK_NAME
```

HTMLは [comparison-template.html](../kamui-i2v-core/assets/comparison-template.html) を使い、全動画に`autoplay muted loop playsinline`を設定する。

### 8. 任意でテロップを焼き込む

WebサイトではHTML/CSSのテロップを原則にする。動画単体として確認・配布する場合だけ、`burn_telop.py`で焼き込む。

```bash
python3 <skill>/scripts/burn_telop.py output/TASK_NAME/MODEL.mp4 \
  --line1 "サブスクで明朗会計" \
  --line2 "勧誘一切無し"
```

既定値は今回の検証で使った黄色帯、太い黒文字、白縁、下部2段のスタイルにしている。細かな調整は [telop-guide.md](references/telop-guide.md) を読む。

## 出力

```text
output/<task>/
├── <model-a>.mp4
├── <model-b>.mp4
├── index.html
├── manifest.json
├── inspection.json
├── _assets/
│   ├── source-image-original.<ext>
│   └── source-image-prepared.jpg
├── _inspection/
│   ├── <model-a>-contact-sheet.jpg
│   └── <model-b>-contact-sheet.jpg
├── _telop/
│   ├── <model>-telop.mp4
│   ├── <model>-telop-contact-sheet.jpg
│   └── <model>-telop-request.json
└── _metadata/
    ├── <model-a>/
    │   ├── request.json
    │   ├── submit-response.json
    │   └── result.json
    └── <model-b>/
```

ユーザーへは動画、比較HTML、主要な検査結果、Seedanceなどの拒否理由、未解決の品質問題を報告する。生成料金の概算と実課金が一致するとは断定しない。

## 必要環境

- Python 3.9以上。外部Pythonパッケージは不要。
- Kamui Code Pass Key。
- `ffmpeg`と`ffprobe`。画像準備、無音化、検査、テロップ焼き込みに使う。
- インターネット接続。

依存コマンドがない場合は課金ジョブ開始前に停止する。
