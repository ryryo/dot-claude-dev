---
name: dev:video-ref
description: 動画ファイルからアプリの画面遷移リファレンスドキュメントを生成する。video-analyzerスキルのキーフレーム抽出スクリプトでフレームを抽出し、Haikuサブエージェントで並列分析、遷移シーン画像と構造化マークダウン（README.md）を指定ディレクトリに出力する。使用タイミング：動画からアプリのUIフロー・ユーザーストーリーをステップごとにまとめたリファレンスを作成したい場合。
---

# dev:video-ref

動画 → キーフレーム抽出（video-analyzer）→ Haiku並列分析 → スクリーンショット + README.md 生成。

## 入力確認

ユーザーから以下を確認する（不明な場合のみ質問）：

- `VIDEO_PATH` — 動画ファイルの絶対パス（必須）
- `OUTPUT_DIR` — 出力先（デフォルト: `docs/REFERENCE/inspire/{動画名}/`）
- `APP_NAME` — ドキュメントのタイトル用アプリ名（動画ファイル名から推定可）

## Step 1: 依存関係＆キーフレーム抽出

**Bash call 1 — venv セットアップ（初回のみ）**
```bash
test -d /tmp/video-env || uv venv /tmp/video-env
source /tmp/video-env/bin/activate && uv pip install opencv-python numpy Pillow
```

**Bash call 2 — キーフレーム抽出**（video-analyzerスキルのスクリプトを使用）
```bash
source /tmp/video-env/bin/activate && python3 ~/.claude/skills/video-analyzer/scripts/extract_keyframes.py \
  {VIDEO_PATH} \
  --output /tmp/keyframes/{slug}/ \
  --threshold 0.80 \
  --quality 80 \
  --scale 0.5
```

`{slug}` は OUTPUT_DIR の末尾ディレクトリ名。抽出後にフレーム総数を確認:
```bash
find /tmp/keyframes/{slug}/ -name "*.jpg" | sort | wc -l
```

## Step 2: Haiku 並列分析

### バッチ分割

| フレーム総数 | バッチ構成 |
|------------|----------|
| ～20枚 | 1バッチ |
| 21～40枚 | 2バッチ（前半/後半） |
| 41枚以上 | 20枚ずつ分割 |

**単一メッセージで全バッチを並列 Task 呼び出しする（model: haiku）。**

Haiku サブエージェントへのプロンプト:

```
{APP_NAME} アプリのキーフレームを分析してください。

以下のファイルパスを Read ツールで直接読み込む（ディレクトリ列挙は不要）:
- /tmp/keyframes/{slug}/frame_XXX.jpg
...（バッチ内の全パスを列挙）

各フレームを分析し、以下の JSON で返す:
{
  "batch": "{バッチ番号}",
  "frames": [
    {
      "frame": "frame_XXX.jpg",
      "screen_type": "画面タイプ",
      "ui_elements": ["要素1", "要素2"],
      "user_action": "推定操作",
      "description": "画面の説明（日本語2-3文）",
      "change_from_previous": "前フレームからの変化（最初はnull）",
      "is_transition_point": true または false
    }
  ]
}
```

**注意**: Haiku は `ls` でディレクトリを列挙できないことがある。プロンプトに全ファイルパスを明示的に列挙すること。

## Step 3: 出力ディレクトリ準備＆画像コピー

```bash
mkdir -p {OUTPUT_DIR}/screenshots
```

`is_transition_point: true` のフレーム + `frame_001.jpg`（開始画面）を screenshots/ にコピー。

## Step 4: README.md 生成

`{OUTPUT_DIR}/README.md` を以下の構造で作成:

```markdown
# {APP_NAME} アプリ画面分析

概要（動画長・分析日・抽出フレーム数）

---

## ユーザーフロー全体像

（テキストのフロー図）

---

## Step N: {画面タイプ名}

**画面タイプ**: ...

- UI要素・操作の説明

[![Step N](./screenshots/frame_XXX.jpg)](./screenshots/frame_XXX.jpg)

---
```

末尾に **UIデザイン特性まとめ**（テーブル）と **参照画像一覧**（テーブル）を追加。  
画像リンクは `[![...](./screenshots/frame_XXX.jpg)](./screenshots/frame_XXX.jpg)` 形式（クリックで拡大）。

## 完了チェック

- `{OUTPUT_DIR}/README.md` が存在する
- `{OUTPUT_DIR}/screenshots/` に画像が1枚以上ある
- README.md 内の全画像リンクが screenshots/ の実ファイルを指している
