# 出典と利用条件

pstackはLauren Tan（poteto）のスキル集を基にしたHashem KhalifaのCodex移植版、thermosはCursorのレビュー手順を基にしたDimabytesのCodex移植版を参照した。原作者、Cursor、OpenAIによる公認版ではない。

| 参照元 | 固定したcommit |
| --- | --- |
| [HashemKhalifa/pstack-codex](https://github.com/HashemKhalifa/pstack-codex) | `5d74be1bfcf8294735ed0a825357b6fe84cd238f` |
| [Dimabytes/codex-thermos](https://github.com/Dimabytes/codex-thermos) | `2fa74e6a9e00b9fe24c59cf86336d0f71762f8c7` |
| [Cursorのthermos](https://github.com/cursor/plugins/tree/main/thermos) | `9d76bcab133aefcccb16121d7be874e6aa823729` |

pstackの追加反証レビューは [poteto/noodle](https://github.com/poteto/noodle)に由来する。原作者と移植の著者は [CONTRIBUTORS.md](CONTRIBUTORS.md)、元のpstackの分類は [UPSTREAM.json](UPSTREAM.json)に保持する。

MITの著作権表示と本文を、[pstack](LICENSE)、[追加レビュー](references/pstack/adversarial-review/LICENSE)、[thermos](references/thermos/LICENSE)で保持する。

## 整理した内容

人とエージェントが読む指示を日本語で整理した。入口を一つにし、pstackの53手順と追加の反証レビューを参照資料へ移した。thermosの二方向レビューをコード変更の確認へ接続し、計画・設計の反証と実動作検証を区別した。

識別子、設定キー、実行補助、ライセンス、試験の固定値は意味を保って扱う。計画検査の日本語語彙、移動後のパス、7担当の設定と初回配置補助は適用先に合わせた。ファイル対応、省いた配布設定、補助コードの変更理由は [provenance.json](provenance.json)に記録する。

以前のプラグイン定義、個別スキルのUI設定、旧構造だけを検査する補助は単一スキルの入口と現行検査へ統合した。53手順、23作業手順、追加レビューの観点は維持し、実行依存を増やしていない。

## 制作に使用した補助スキル

- [yomiyasu](https://github.com/nanaism/yomiyasu)：意味、条件、断定の強さ、主体と時制を保つ推敲。
- [natural-japanese](https://github.com/coji/natural-japanese)：読者と目的に沿った執筆、機械検査と文脈による判断。
- [ponytail](https://github.com/DietrichGebert/ponytail)：呼び出し元・設定・検証まで含め、必要な範囲を最小の変更で終える。

制作時の補助として使用し、スキルの実行依存や常駐指示には加えない。固定した版はprovenance.jsonに記録する。

technical-writingの参照元にはDiátaxis、Google developer style、ASD-STE100 Issue 9、John R. KohlのGlobal English Style Guideがある。言語の構文をそのまま移さず、意味・主体・条件・操作順を読む規則へ反映している。

## 過去の検証と現在の検証

[上流の記録](provenance/pstack/validation/)と [以前の移行記録](provenance/pstack/ja-migration.md)は過去の証拠として保存する。現在の端末や構成の合格証拠には使わない。今回の検証は [validation/integration.md](validation/integration.md)に記録する。
