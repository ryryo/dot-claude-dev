---
name: magnific-i2v-core
description: Magnific APIを使ってimage-to-video生成を行う共通手順。ユーザーがMagnific、Kling 3.0、Magnific APIでのi2v実行を明示したときに使用する。APIキー、開始画像アップロード、プロンプト投入、非同期ポーリング、MP4保存、技術検査までのprovider固有運用を定義する。APIが使えない場合だけMagnificブラウザUIをfallbackとして扱う。
---

# Magnific i2v共通基盤

## 概要

Magnific APIを使うi2v生成のprovider固有部分だけを扱う。用途固有の入力画像作成、プロンプト設計、成果物加工、品質判断は呼び出し側スキルに残す。

Kamui MCPを使える状況ではKamuiを既定にする。ユーザーが「Magnificで」など、Magnific利用を明示した場合だけこのスキルを使う。

## 前提

- Magnific APIキーはプロジェクトの`.env.local`または`.env`、または環境変数に`MAGNIFIC_API_KEY`として置く。サンプルはこのスキル配下の`.env.example`を見る。旧Freepik名などの互換キー名は使わない。
- APIキー、アップロードURL、生成物URLは非公開情報として扱い、最終応答にそのまま出さない。
- 生成ジョブ送信、ファイルアップロード、ダウンロードはユーザーがその目的を明示している範囲でだけ行う。
- モデルに字幕、ロゴ、UIなどの文字要素を描かせるかどうかは呼び出し側のプロンプト方針に従う。
- このスキルはMagnific API呼び出し、MP4取得、providerメタデータ記録、技術検査だけを担当する。

## モデル

モデル候補と既定値は [models.json](references/models.json) を見る。

- `models.json`の`models`には、公式Magnific API docsでcreate endpointとpoll endpointを確認できたモデルだけを入れる。ブラウザUIだけで見えたモデルを選択可能モデルとして登録しない。
- ユーザーがモデルを指定した場合: `models.json`のslugに対応するAPIモデルを使う。
- ユーザーがモデルを指定しない場合: `defaults.fallback_model`のAPIモデルを使う。
- APIで`aspect_ratio=auto`を使う場合は入力画像比率に従う。呼び出し側の指定が16:9など固定なら、その指定を渡す。

## 実行手順

### 1. 入力と出力先を決める

- 入力画像: 生成済みの採用静止画を使う。キャラクターシートだけを直接i2vに入れない。
- タスク名: `output/<task>/` に保存できる小文字英数字とハイフンの名前にする。
- 出力モデル名: `models.json`のslugを使う。例: `magnific-kling-v3-omni-std`。

出力先:

```text
PROJECT_ROOT/output/<task>/
├── <model>.mp4
├── inspection.json
├── _assets/
│   └── source-image.<ext>
├── _inspection/
│   └── <model>-contact-sheet.jpg
├── _metadata/
│   └── <model>/
│       └── request.json
```

### 2. 入力画像を準備する

呼び出し側スキルが、Magnificへ渡すローカル画像を用意する。このcoreでは画像の新規生成、人物補正、ループ用開始・終了設計、メタデータ除去方針を決めない。

入力画像は絶対パスで扱い、元画像を上書きせず`output/<task>/_assets/`へコピーする。APIアップロードはPNG、JPEG、WebP、10MB以下を前提にする。

### 3. Magnific APIで生成する

通常は `scripts/generate_api.py` を使う。

モデル一覧を表示する:

```bash
python3 .codex/skills/dev/webgen/magnific-i2v-core/scripts/generate_api.py --list-models
```

```bash
python3 .codex/skills/dev/webgen/magnific-i2v-core/scripts/generate_api.py \
  PROJECT_ROOT TASK_NAME /abs/path/to/source-image.png \
  --prompt-file /abs/path/to/prompt.txt \
  --model magnific-kling-v3-omni-std \
  --duration 5 \
  --aspect-ratio auto
```

このスクリプトは次を行う。

- `.env.local`、`.env`、環境変数から`MAGNIFIC_API_KEY`を読む
- `POST /v1/ai/uploads/request-url`でアップロードURLを取得する
- signed URLへ画像bytesをPUTし、`asset_url`を得る
- モデルのcreate endpointへpromptと画像URLを送る
- poll endpointを完了まで確認する
- 生成MP4を`output/<task>/<model>.mp4`へ保存する
- `_metadata/<model>/request.json`へrequest、task、出力URL、ffprobe結果を記録する

`--aspect-ratio`を省略した場合は`models.json`の`default_aspect_ratio`を使う。Omniは`auto`、通常Kling 3は`16:9`を既定にする。

音声が不要なWeb用動画では`--audio`を付けない。`--audio`を付けた場合だけ`generate_audio: true`にする。

### 4. 逐次生成する

生成は1ジョブずつ行う。スクリプトは完了までpollする。失敗、認証エラー、クレジット不足、rate limitが出た場合はstderrまたは例外本文を確認し、APIキーやアカウント状態など具体的な対応をユーザーに依頼する。

`_metadata/<model>/request.json`には少なくとも次を残す。

- provider: `Magnific API`
- model
- source_image
- prompt_fileまたはprompt本文
- endpoint、duration、aspect_ratio、audio
- task_id
- output_url
- 出力パス

### 5. 検査する

MP4本体を技術検査する。共通検査スクリプトが使える場合は使ってよいが、用途固有の採否判断は呼び出し側スキルへ返す。

```bash
python3 <kamui-i2v-core>/scripts/inspect_videos.py PROJECT_ROOT/output/TASK_NAME
```

確認する項目:

- MP4本体である
- 音声ストリームが0件
- 要求秒数に近い
- 比率が意図と合う
- 生成モデルが新しい文字、ロゴ、UI、デバイスを追加していない
- 顔、手、持ち物、背景境界が安定している
- 場面変化、ズーム、クロップがない

## Browser UI fallback

APIキーがない、APIアクセスが有効化されていない、API未対応のモデルやUI固有設定が必要、またはユーザーが明示的にMagnific画面での操作を求めた場合だけBrowser skillを読む。

Browser skillに従い、既存タブがあればclaimし、なければ次を開く。

```text
https://www.magnific.com/jp/app/ai-video-generator
```

画面で確認する項目:

- ツールが動画生成ツールである
- モデルが目的のモデルである
- 解像度がユーザー指定または最小十分な値である
- 秒数が用途に合っている
- 音声が不要な場合はOFFにする
- 比率が指定通り、または入力画像固定による実比率になっている

生成中はステータスを確認し、失敗・CAPTCHA・ログイン・クレジット不足が出た場合はユーザーに具体的な対応を依頼する。完了後は生成カードを開き、詳細画面の動画本体ダウンロードを使う。カード一覧のダウンロードはサムネイル画像を落とすことがあるため、MP4拡張子と`ffprobe`で必ず確認する。

## 他スキルからの再利用

上位の`generate-i2v-*`スキルでは、ユーザー指定がなければKamui coreを使う。ユーザーがMagnific利用を明示した場合だけ、この`SKILL.md`と必要なreferenceを読んで、APIで実行する。

Browser UI fallbackはMagnificの画面状態、ログイン、クレジット、ダウンロード導線に依存するため、APIで足りる場合は使わない。

Web配信用の成果物加工、ループ補修、文字重ね、人物/商品/資料の採否判断は呼び出し側スキルで行う。

## 保守

- Magnific側のAPI endpointやモデル名が変わったら [models.json](references/models.json) を更新する。
- UI座標を手順として固定しない。必ず画面状態、DOM、詳細画面、ファイル拡張子で確認する。
- 生成費用やクレジット消費はAPIまたはDashboardで確認できる範囲だけ記録し、実課金額と一致すると断定しない。
