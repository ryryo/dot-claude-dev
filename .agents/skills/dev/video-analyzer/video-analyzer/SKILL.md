---
name: video-analyzer
description: 動画ファイルからキーフレームを抽出し、Haikuサブエージェントで低コスト分析を実行します。UIバグ検出、画面遷移分析、動画内容の理解などに使用します。通常450円かかる動画分析を約1円まで削減可能です。
---

# Video Analyzer

動画ファイルからキーフレームを効率的に抽出し、Haikuサブエージェントで一括分析することで大幅なコスト削減を実現するスキル。

## コスト比較

| 方式 | 5秒動画のコスト | 削減率 |
|------|----------------|--------|
| 通常（全フレーム、Opus） | 約450円 | - |
| キーフレーム抽出（Opus） | 約24円 | 95% |
| **キーフレーム + Haiku** | **約1円** | **99.8%** |

## 依存関係のインストール

```bash
pip install -r skills/video-analyzer/requirements.txt
```

または個別にインストール:
```bash
pip install opencv-python numpy Pillow
```

## ワークフロー

### Step 1: キーフレーム抽出

Bashツールでスクリプトを実行:

```bash
python skills/video-analyzer/scripts/extract_keyframes.py \
  /path/to/video.mp4 \
  --output /tmp/keyframes/analysis_001/ \
  --threshold 0.85 \
  --quality 30 \
  --scale 0.3
```

**パラメータ:**
| パラメータ | デフォルト | 説明 |
|-----------|-----------|------|
| `--threshold`, `-t` | 0.85 | 類似度閾値（低いほど多くのフレームを抽出） |
| `--quality`, `-q` | 30 | JPEG品質（低いほどファイルサイズ小） |
| `--scale`, `-s` | 0.3 | 出力サイズの倍率（元の30%） |
| `--max-frames`, `-m` | 無制限 | 最大抽出フレーム数 |

**出力例:**
```
Processing video: /path/to/video.mp4
  Duration: 5.00s (150 frames @ 30.00 FPS)
  Original size: 1920x1080
  Output size: 576x324

============================================================
Extraction Summary
============================================================
Keyframes extracted: 52
Total size: 0.54MB
Estimated tokens: ~10,400
Estimated cost (Haiku): $0.0026 (~0.4円)
============================================================
```

### Step 2: Haikuサブエージェントで分析

Taskツールを使用してHaikuモデルのサブエージェントを呼び出す。

**基本的な呼び出し:**
```
Task tool:
  subagent_type: general-purpose
  model: haiku
  description: "Analyze video keyframes"
  prompt: (下記参照)
```

## 分析プロンプト例

### 汎用分析

```
動画から抽出されたキーフレームを分析してください。

キーフレーム出力ディレクトリ: /tmp/keyframes/analysis_001/

以下の手順で実行：
1. Readツールで上記ディレクトリ内の全JPEG画像を読み込む
2. 各フレームの内容を時系列順に分析する
3. 以下の形式でJSON結果を返す:

{
  "total_frames": 数値,
  "analysis": [
    {
      "frame": "frame_001.jpg",
      "timestamp_approx": "0.0s",
      "description": "画面の説明",
      "change_from_previous": "前フレームからの変化点"
    }
  ],
  "summary": {
    "main_flow": "操作フローの概要",
    "key_observations": ["重要な観察点"]
  }
}
```

### UIバグ検出

```
UIバグ検出分析を実行してください。

キーフレームディレクトリ: /tmp/keyframes/bug_report/

以下の観点で各フレームを分析：
1. レイアウト崩れ（要素の重なり、はみ出し）
2. 表示異常（文字化け、画像欠け）
3. 状態不整合（ボタンのdisabled状態、ローディング表示）
4. エラーメッセージの表示

出力形式:
{
  "bugs_found": [
    {
      "frame": "frame_xxx.jpg",
      "bug_type": "layout_break",
      "description": "詳細説明",
      "severity": "high/medium/low"
    }
  ],
  "clean_frames": ["問題なしのフレーム一覧"]
}
```

### 画面遷移フロー分析

```
画面遷移フロー分析を実行してください。

キーフレームディレクトリ: /tmp/keyframes/user_flow/

以下の手順で実行：
1. 全フレームを時系列順に読み込む
2. 各画面のタイプを識別（ログイン、一覧、詳細、モーダル等）
3. 遷移パターンを特定

出力形式:
{
  "screens": [
    {"frame": "xxx", "screen_type": "login", "key_elements": [...]}
  ],
  "transitions": [
    {"from": "login", "to": "dashboard", "trigger": "ログインボタンクリック"}
  ],
  "flow_diagram": "A -> B -> C -> D"
}
```

## 並列実行（大量フレームの場合）

50枚以上のキーフレームがある場合、複数のHaikuサブエージェントで並列分析:

```
# 単一メッセージで複数のTaskツールを同時呼び出し

Task tool 1:
  subagent_type: general-purpose
  model: haiku
  description: "Analyze keyframes batch 1 (001-020)"
  prompt: "フレーム分析 バッチ1
    対象: /tmp/keyframes/video_xxx/frame_001.jpg 〜 frame_020.jpg
    ..."

Task tool 2:
  subagent_type: general-purpose
  model: haiku
  description: "Analyze keyframes batch 2 (021-040)"
  prompt: "フレーム分析 バッチ2
    対象: /tmp/keyframes/video_xxx/frame_021.jpg 〜 frame_040.jpg
    ..."
```

## バックグラウンド実行

長時間かかる分析の場合:

```
Task tool:
  subagent_type: general-purpose
  model: haiku
  run_in_background: true
  description: "Background analysis of video keyframes"
  prompt: "..."
```

## Step 3: 結果の統合

サブエージェントから返された分析結果を元に、レポートを作成する。
複数バッチで並列実行した場合は、結果をマージして時系列順に整理。

## モデル選択ガイド

| モデル | 入力コスト | 推奨用途 |
|--------|-----------|---------|
| **haiku** | $0.25/1M | 画像分析、定型作業（推奨） |
| sonnet | $3/1M | 中程度の複雑さの分析 |
| opus | $15/1M | 複雑な設計、重要な判断 |

**Haiku推奨の理由:**
- 画像認識・分析タスクでは十分な精度
- キーフレーム分析は定型的なパターン認識が主
- コスト効率が最も高い

## ディレクトリ構造

```
skills/video-analyzer/
├── SKILL.md                      # このファイル
├── requirements.txt              # Python依存関係
└── scripts/
    └── extract_keyframes.py      # キーフレーム抽出スクリプト
```

## トラブルシューティング

### 依存関係エラー

```
ModuleNotFoundError: No module named 'cv2'
```

解決: `pip install opencv-python numpy Pillow`

### 動画形式エラー

対応形式: mp4, mov, avi, mkv, webm など一般的な形式
エラーが出る場合は、ffmpegで変換を試す

### メモリ不足

長時間動画の場合、`--max-frames` オプションで抽出数を制限
