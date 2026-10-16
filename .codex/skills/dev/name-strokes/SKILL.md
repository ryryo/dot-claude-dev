---
name: name-strokes
description: 社名・屋号・サービス名の候補を発音、意味、用途、画数から検討する。日本語筆順データを優先する根拠付きPython計数と、ユーザー提供の1〜120画の鑑定原文参照を行う。命名案の作成、比較、表記違いの検討、画数内訳の確認に使う。
---

# 命名と画数

候補の意味・呼びやすさ・表記・用途を先に評価し、画数は選択材料の一つとして扱う。対象の事業、想定読者、希望する響きや言語、候補があれば利用する。不足情報が判断を変える場合だけ確認する。

## 候補を比較する

1. 少数の候補を、読み・意味・対象とのつながり・綴りやすさ・略称も含めて作る。既存候補の比較ならその候補を優先する。
2. このスキル内のCLIを実行して画数を計算する。モデルの暗算で未測定文字の値を確定しない。
3. 既定は日本語向け **KanjiVG** の筆画数。サイト実測値との比較が必要なら `--profile site-inspired` も実行し、違いを見せる。Unicode/Unihanの補完は既定では無効。
4. 正規化、文字別の根拠、推定・未知文字を確認する。未知文字が残る場合は合計を未確定として示し、既知部分の小計で鑑定しない。
5. 結果を「候補・読み・意味と用途・画数/方式・根拠や未確認点」の比較表にする。最終推薦は画数だけで決めない。

## CLI

`<skill-dir>` はこのSKILL.mdのある実際のフォルダーに置き換える。

```bash
python3 <skill-dir>/scripts/count_strokes.py '候補名A' '候補名B'
python3 <skill-dir>/scripts/count_strokes.py 'ｶﾞ＋Ａ' '一🧪一' --json
python3 <skill-dir>/scripts/count_strokes.py 'は' --profile site-inspired
python3 <skill-dir>/scripts/count_strokes.py '株式会社候補名' --strip-corporate
python3 <skill-dir>/scripts/count_strokes.py '一🧪一' --override '🧪=5'
python3 <skill-dir>/scripts/count_strokes.py '候補名' --data /path/outside/repository/fortune.json
```

- 日本語データ未収録の漢字まで調べるためにUnihanを使う場合だけ `--han-fallback unihan` を明示する。日本語字体と異なる可能性を表示し、根拠付きの補完として扱う。
- `--symbols count` が既定。対応記号には線・点の明示ルールを使い、`--symbols ignore` で記号除外との比較ができる。
- 法人格は既定で含める。`--strip-corporate` は先頭・末尾の日本語法人格だけを除く利用者向けの追加機能。
- `--json` は常に候補結果の配列。`--no-fortune` で鑑定文を省略。`--full-text` で人間向け出力にも提供原文を全文表示する。
- 鑑定データは同梱しない。参照先は `--data FILE`、環境変数 `NAME_STROKES_DATA`、既定ファイルの順。既定は `$XDG_DATA_HOME/name-strokes/shamei_uranai_1-120.json`、XDG未設定時は `~/.local/share/name-strokes/shamei_uranai_1-120.json`。
- データ未設定の公開cloneでも計数は動く。鑑定は `data_not_configured` と説明し、本文・印を生成しない。
- `--strict` は未知文字があっても全候補の内訳を出力し、終了コード2を返す。既定では未知文字があってもプログラム全体を落とさない。
- 日本語・英字・数字の表記差は正規化するが、漢字の新旧字体・CJK互換漢字は一律に統合しない。原表記と変換履歴を残す。

## 鑑定原文

利用権のあるローカル鑑定JSONを外部ファイルとして読む。ユーザー提供の元原文と校正資料はGit管理外で保持し、このスキルには含めない。総画数1〜120のうちローカルファイルに存在する番号だけを直接参照する。データ未設定、該当番号なし、0、120超、合計未確定では原文鑑定を返さず、循環や新しい本文を作らない。

日本語筆順を基準に得た合計に対する原文参照は、サイトでその名前を鑑定した結果とは区別する。`site-inspired` も完全互換ではない。サイトの記号送信バグは再現しない。

校正するときは利用者のローカル保存先にある `校正候補.csv` と [本文を含まない検収記録](references/data-verification.json) を読む。校正候補は未承認で、原文へ自動反映しない。原文・校正資料・原文を含む実行出力を公開対象へ追加しない。

## 根拠・精度を確認するとき

[計数方式とデータ出典](references/counting-policy.md) に、日本語優先とサイト寄りの違い、補完表、ライセンス、更新手順を記載している。サイト仕様の証拠を確認するときは [Macでの実測調査](references/社名占い_実測調査.md) と [実測CSV](references/社名占い_実測.csv) を読む。

商標・ドメイン・法人名の利用可能性はCLIでは調べない。確認を実施していない候補は「商標未確認」等と明記し、確認済みと表現しない。調べる依頼があれば別途、対象国・区分・最新の一次情報で確認する。
