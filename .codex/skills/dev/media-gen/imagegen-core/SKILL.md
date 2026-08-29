---
name: imagegen-core
description: Image Genツールを使う画像生成スキルの共通実行規約。生成前のtaskとmodel決定、output配下への採用画像保存、候補画像、prompt/request/reviewメタデータ、目視確認、採用画像の扱いを統一する。generate-t2i系スキルやその他Image Gen前提のスキルが共通出力契約を必要とするときに使用する。
---

# Image Gen Core

## Overview

Image Genそのものの共通契約だけを扱う。用途固有の構図、配色、漫画コマ割り、人物ポーズ、プロンプトテンプレート、品質基準は呼び出し側スキルに残す。

## Responsibilities

- 生成前に`<task>`と`<model>`を決める。
- 採用画像を `output/<task>/<model>.<ext>` に保存する。
- 候補画像、修正生成、メタデータを同じ`<task>`配下に整理する。
- 採用画像とレビュー候補を混同しない。
- 目視確認の結果をメタデータへ残す。
- Image Genの実行前後で、参照画像と生成結果を必要に応じて目視確認する。

## Naming

- `<task>`: 今回の目的を表す小文字英数字とハイフンの名前。80文字以内を目安にする。
- `<model>`: 実際に使う画像生成モデルの安定したfilesystem-safeなID。生成前に決め、`unknown`や`imagegen`で代用しない。
- `<ext>`: 実際の画像形式。PNGで保存できる場合はPNGを優先する。

## Output Contract

```text
output/<task>/
├── <model>.<ext>
├── <model>-candidate-1.<ext>
├── <model>-candidate-2.<ext>
└── _metadata/
    └── <model>/
        ├── prompt.txt
        ├── request.json
        └── review.json
```

採用画像だけを `output/<task>/<model>.<ext>` に置く。候補画像や修正生成は `<model>-candidate-N.<ext>` として同じディレクトリに保存する。複数モデルを比較した場合は、モデルごとに同じ規約で保存する。

## Metadata

`prompt.txt`には最終生成プロンプトを保存する。

`request.json`には少なくとも次を保存する。

```json
{
  "task": "task-name",
  "model": "model-slug",
  "aspect_ratio": "4:3",
  "text_mode": "none",
  "referenced_images": [],
  "output": "output/task-name/model-slug.png"
}
```

`review.json`には採用判断に使った目視確認結果を保存する。用途固有スキルのQA項目を、`checks`配列またはオブジェクトとして残す。

## Reuse From Other Skills

Image Gen前提の用途スキルは、この`SKILL.md`を読んでから用途固有の手順へ進む。出力規約、候補命名、メタデータ名を用途スキル側に再定義しない。

呼び出し側スキルでは次だけを追加で決める。

- 画像の目的と掲載場所
- プロンプト作成規則
- 参照画像の扱い
- 用途固有の目視確認項目
- 生成失敗時や修正生成時の判断

## Reporting

完了時は、採用画像パス、`<task>`、`<model>`、主要オプション、残っている制約だけを簡潔に報告する。
