# 計数方式、根拠、出典

## 日本語を優先する

既定 `--profile japanese` は日本語筆順のKanjiVGを優先する。これは日本語としての筆画を検討するための基準であり、姓名判断の旧字換算やサイトの独自辞書の再現ではない。

優先順は次のとおり。

1. 明示的なユーザー指定 `--override`。
2. 空白等の除外方針と、明示的な記号除外オプション。
3. 日本語の漢字・かなに対するKanjiVGの基底Unicodeファイル。
4. KanjiVG未収録文字のサイト実測・差分値、ユーザー提供単字結果。日本語文字のこの参照は `observed_site_fallback` として注意を出す。
5. 利用者が `--han-fallback unihan` を明示した場合だけ、Unihanの日本向けJ指定値、なければkTotalStrokes。
6. 明示したかな・英字・記号の補完表。
7. 句読記号・書式文字の除外方針。その他は未知として値をnullにする。

`--profile site-inspired` は3と4を逆にし、サイト実測値を優先する。単字実測45ルール（提供単字・差分を含む）と日本語データによる補完を用いる。サイト完全互換と称さない。特に実フォームの+・#・複数&に関する送信時変形は再現せず、文字を文字として計数する。

「は」はKanjiVG3画、サイト4画。「ぱ」はKanjiVG4画、サイト5画。内訳の `site_reference` と `differs_from_site_observation` で比較できる。`髙` は今回のKanjiVG基底ファイルにないため、サイト11画を参考採用し日本語の確定値としない。

## データ出典とライセンス

### KanjiVG（既定）

- 一次資料: https://kanjivg.tagaini.net/
- 元リポジトリ: https://github.com/KanjiVG/kanjivg
- 固定コミット: `70a0b7ae0c18ceb5cb358274b029cce0234a43bc`
- アーカイブSHA-256: `d6a17d77902b863d7524e24d11c44ae628c5d5ba4f09cb3af90c1190bf78bcca`
- 著作者: Ulrich Apel and contributors（元ファイルの著作権表示もCOPYINGに保持）。
- ライセンス: **CC BY-SA 3.0**。[原ライセンス全文](KANJIVG-COPYING.txt)。
- 派生ファイル: `assets/kanjivg_strokes.json`。基底Unicode名のSVG内の筆画pathの個数を抽出した6,984字。派生データもCC BY-SA 3.0で提供する。変種接尾辞付きSVGは除外した。
- 漢字・かなに使う。英字の筆画は字体や筆記法によるため、KanjiVG英字の値をサイト実測値と同一視しない。
- 基底ファイルの字体を数えるため、同じUnicode字のあらゆる印字体・異体字の正解を保証するものではない。

### Unicode Unihan（明示的な補完のみ）

- 公式データ: https://www.unicode.org/Public/17.0.0/ucd/Unihan.zip
- 仕様: https://www.unicode.org/reports/tr38/tr38-40.html
- 版は17.0.0に固定。最新追従を意図したものではない。
- アーカイブSHA-256: `f7a48b2b545acfaa77b2d607ae28747404ce02baefee16396c5d2d7a8ef34b5e`
- 著作権: Unicode, Inc.（元データは2025年版、ライセンス取得日は2026-10-16）。
- ライセンス: **Unicode License V3**。[同梱全文](UNICODE-LICENSE.txt)。
- 派生ファイル: `assets/unihan_strokes.json`。kTotalStrokesがある102,998字と、日本向けJ指定がある102字を抽出。データはUnicodeの条件に従う。
- kTotalStrokesはIRGの計数慣例による参考情報。日本語字体と一致する保証はない。kAlternateTotalStrokesのJ指定は一部に限られる。
- 複数候補があるときは `alternatives` も出力する。日本語向け主データの代用品として自動採用しない。

### サイト実測とユーザー原文

- 実測CSVはMac Chromeで行った98件の完了観測と1件の中断。サイトの文字辞書・公開コードを丸ごとコピーしたものではない。
- 原文JSONはユーザーのローカル資料で、リポジトリに同梱しない。保全確認用SHA-256は `6b004c1e0c96d55563ff62a4923551fd95fd1b3ea905ce384fa783ed776c8ed9`。
- 提供元の収集記録と、この担当のMacブラウザ実測を区別する。こちらが全120件をブラウザ確認したとはしない。
- 1〜120が各1件、本文欠落なし。follow空欄60件は◎/○と対応。主本文の数字置換後テンプレート60種だが、番号との単純循環ではない。必ず各番号の元エントリを参照する。
- 25種類の総画数について、ブラウザの本文指紋と、提供JSONのcontent+follow（改行を除去）を照合し全一致。星マークとの対応も照合済み。
- 原文は未校正。校正候補は原文と同じローカル保存先の別CSVで、CLIから自動適用しない。原文・校正資料・原文を含む加工ファイルはGit管理外とする。
- この提供原文に公開再配布ライセンスがあるとは扱わない。公開スキルには本文と校正CSVを含めない。
- 公開可能な版・ライセンス情報は `assets/sources.json` に保存。Library等の私的な参照情報はローカルの `source-provenance.json` にのみ保持。

### ローカル鑑定ファイルの設定

参照先の優先順は `--data FILE`、環境変数 `NAME_STROKES_DATA`、既定ファイル。既定は `$XDG_DATA_HOME/name-strokes/shamei_uranai_1-120.json`。XDG未設定時は `~/.local/share/name-strokes/shamei_uranai_1-120.json`。校正候補は同じフォルダーの `校正候補.csv` を別途読む。

ファイルがなくても公開cloneで文字計数は可能。鑑定欄は `data_not_configured`。壊れたデータは `data_error`、部分データで番号が存在しなければ `result_not_available` とし、本文を捏造しない。原文監査はローカルファイルに対して `audit_corpus.py --data FILE` を実行する。

JSONの最小形は次のような架空データ。これはスキーマ説明用で実際の鑑定ではない。

```json
{"source_kind":"synthetic_example","results":[{"target_strokes":1,"result":{"result_num":1,"result_mark":"○","result_content":"SYNTHETIC EXAMPLE ONLY","result_follow":""}}]}
```

`.gitignore` は `local/`、`private/`、原文JSON名、校正候補CSV名、私的出典ファイル名を除外する。原文を含む出力を別名でリポジトリへ保存して公開しない。公開テストは一時ディレクトリに作る架空の最小fixtureだけを用い、実原文の有無に依存しない。

## 表記の扱い

- 幅・半角カナの濁点・合成濁点をNFKC/NFCで統一。独立濁点をかなに付けた表記も合成する。
- CJK互換漢字はNFKCで基底字に潰さない。国/國、高/髙等の新旧・異体を一律置換しない。
- IVSは基底字として補完し、変換履歴に警告を残す。選択字形の筆画は確定しない。
- Latinのアクセントは基底英字へ補完する。éとe+結合アクセントは同じ計数になる。綴りは元入力も保持。
- 小書きかなで公開データがない場合は通常字の表を参照し、推定属性を残す。
- 法人格は含めるのが既定。`--strip-corporate` は先頭・末尾の株式会社、有限会社、合同会社、合資会社、合名会社を明示的に除く。
- 空白・書式文字・未定義句読点の除外は0画方針として明示し、物理的な画数が実測0だったとはしない。

## 補完値の性質

英字はA3/a2だけを単字実測。その他は手書き慣例を基にしたv1の**推定表**。大文字26字の総和59、小文字26字54に合うが、2本の総和条件だけで52字の個別値は一意に決まらない。これをサイトの単字辞書と称さない。正確なサイト単字値が必要なら追加の許可済み個別実測で更新する。

記号はサイトで対応する&2、ハイフン1、ピリオド1、中点1、長音符1、々3を文脈差分として優先する。その他は一つの実用的な記入規則。

| 記号 | 補完値 |
|---|---:|
| +、= | 2 |
| #、% | 4 |
| _、/、\\、括弧各片 | 1 |
| @ | 2 |
| :、;、!、? | 2 |
| *、$、€、£ | 3 |
| カンマ、和文読点・句点 | 1 |

唯一の標準や実測値ではなく、`basis=heuristic` と `source=symbol-policy-v1` を出す。絵文字等を無根拠に0画とはしない。未知があれば `total=null` と既知部分小計、警告、文字位置を返す。ユーザーが指定した値は `basis=user_override` とする。

## 原文参照

合計1〜120のうちローカルJSONに存在する番号の原文を取り出す。原文ファイルは公開対象に含めない。計数に公開データ・推定・正規化・除外が含まれる場合は `conditional_reference` とする。鑑定文の品質や数字の正しさを保証するラベルではない。データ未設定・番号なし・0・120超・未確定合計には原文鑑定なし。無断の循環・原文の生成・修正をしない。

## 再検証・更新

実行時はPython標準ライブラリだけで動き、ネットアクセスしない。

```bash
python3 <skill-dir>/scripts/audit_corpus.py
python3 -m unittest discover -s <skill-dir>/scripts -p 'test_*.py' -v
```

公開データを更新する場合は公式ソースを取得し、版・コミット・SHA-256・ライセンスを確認してから、同梱のオフライン抽出器を使う。

```bash
python3 <skill-dir>/scripts/build_kanjivg.py <archive.zip> <source-metadata.json> <skill-dir>/assets/kanjivg_strokes.json <skill-dir>/references/KANJIVG-COPYING.txt
python3 <skill-dir>/scripts/build_unihan.py <Unihan-17.0.0.zip> <skill-dir>/assets/unihan_strokes.json
```

KanjiVG用source-metadataにはcommit、url、archive_sha256、license、bytesを記載する。更新後はsources.jsonと検収を更新する。推定表の変更をサイト観測へ昇格させない。原文JSON更新は別の明示的な提供原文を受け取り、差分とハッシュを検収してから行う。
