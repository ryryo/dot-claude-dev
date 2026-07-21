---
name: kamui-i2v-core
description: Kamui MCPの画像から動画生成に使う共通実行基盤。Kamui CodeパスキーでMCP設定をマージし、models.jsonからi2vモデルを選択し、submit/status/resultを逐次実行し、動画ダウンロード、音声除去、再開、検査、比較HTML作成を行う。Webループ動画、人物メッセージ動画、その他Kamui MCP i2vスキルが共通処理を必要とするときに使用する。
---

# Kamui i2v共通基盤

## 概要

Kamui MCPによるi2v生成の共通部分だけを扱う。用途固有の入力画像作成、プロンプト設計、ループ補修、テロップ焼き込み、品質判断は呼び出し側スキルに残す。

## 役割

- `references/models.json`を唯一のモデルカタログにする。
- プロジェクトに`.mcp.json`がない場合はカレントワークスペースまたはスキルの親プロジェクトにある`.mcp.json`を初期配置元にし、必要なKamui MCPサーバーを安全にマージする。
- `KAMUI_CODE_PASS_KEY`を環境変数または`.env.local`から読み、キー本体を`.mcp.json`へ保存しない。
- i2vジョブをモデルごとに直列実行する。
- 送信済み`request_id`がある場合は再課金せずポーリングから再開する。
- ダウンロードした動画から音声ストリームを除去する。
- `inspection.json`、コンタクトシート、比較HTMLを作成する。

## 直接実行

モデル一覧を表示する:

```bash
python3 <core-skill>/scripts/generate.py --list-models
```

ループ用i2vジョブを実行する:

```bash
python3 <core-skill>/scripts/generate.py INPUT_IMAGE \
  --project PROJECT_ROOT \
  --task TASK_NAME \
  --mode loop \
  --prompt-file PROMPT_FILE \
  --comparison
```

リポジトリが`output/<generation_type>/<model_name>/`を要求する場合は、そのモデルディレクトリ配下を明示的な出力先として渡す:

```bash
python3 <core-skill>/scripts/generate.py INPUT_IMAGE \
  --project PROJECT_ROOT \
  --task TASK_NAME \
  --output-root PROJECT_ROOT/output/i2v/MODEL_SLUG \
  --model MODEL_SLUG
```

`--output-dir`を使うと、タスク名ディレクトリを含む完全な出力先を直接指定できる。

人物メッセージ用i2vジョブを実行する:

```bash
python3 <core-skill>/scripts/generate.py INPUT_IMAGE \
  --project PROJECT_ROOT \
  --task TASK_NAME \
  --mode message \
  --prompt-file PROMPT_FILE \
  --comparison
```

明示的にモデル比較する場合は`--model`を複数回渡す。`--model`がない場合、スクリプトは`references/models.json`から有効な最安モデルを1つ選ぶ。`--mode loop`では`supports_loop`も必須条件にする。

課金される生成前にモデル、秒数、解像度、概算費用を確認したい場合は`--dry-run`を使う。

## MCP設定

`generate.py`は`--no-setup-mcp`が指定されていない限り`setup_mcp.py`を自動実行する。設定だけ行う場合:

```bash
python3 <core-skill>/scripts/setup_mcp.py \
  --project PROJECT_ROOT \
  --model MODEL_SLUG
```

MCP設定の挙動を変更する前に[mcp-setup.md](references/mcp-setup.md)を読む。

## 出力契約

`generate.py`は既定で`PROJECT_ROOT/output/<task>/`へ次を出力する。`--output-root`を指定すると`OUTPUT_ROOT/<task>/`へ出力し、`--output-dir`を指定するとそのディレクトリをそのまま出力先にする。

```text
<task-output-dir>/
├── <model>.mp4
├── manifest.json
├── inspection.json
├── index.html
├── _assets/
│   └── source-image.<ext>
├── _inspection/
│   └── <model>-contact-sheet.jpg
└── _metadata/
    └── <model>/
        ├── request.json
        ├── submit-response.json
        └── result.json
```

`_delivery/`、`_telop/`、準備済み入力画像などの追加出力フォルダは呼び出し側スキルで作成する。

## 他スキルからの再利用

上位のi2vスキルでは、この`SKILL.md`を読んだうえで、このスキルのスクリプトを直接実行する:

```bash
python3 .codex/skills/dev/webgen/kamui-i2v-core/scripts/generate.py ...
```

後方互換のコマンドが必要な場合は、呼び出し側スキルに薄いラッパーだけを残し、`../kamui-i2v-core/scripts/<script>.py`を解決して引数を転送する。モデルカタログ、MCP設定コード、ポーリング処理、検査コード、比較テンプレートを呼び出し側スキルへコピーしない。

## 保守

- モデル名、MCP URL、ツール名、価格、秒数、解像度、パラメータフィールドは[models.json](references/models.json)だけで更新する。
- Kamui MCP全体の初期設定を更新する場合は、ツールキットルートの`.mcp.json`を正本として更新する。キー本体などの秘密情報は含めない。
- `scripts/kamui_i2v.py`には外部Python依存を追加しない。
- すべてのi2v用途に安全でない限り、用途固有のプロンプトルールをここへ追加しない。
- カタログ変更後は`python3 <core-skill>/scripts/generate.py --list-models`と`python3 <core-skill>/scripts/setup_mcp.py --list-models`を実行する。
