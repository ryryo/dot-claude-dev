# pstack-thermos

`$pstack-thermos` から開発・レビュー・初回設定を呼び出す。開発はpstack、コード変更のレビューはthermosの手順を使う。内部手順は必要になった時点で読む。

## 呼び出し例

- `$pstack-thermos この不具合を調査し、修正・レビュー・検証まで進めて`
- `$pstack-thermos このPRを正しさと保守性の両方からレビューして`
- `$pstack-thermos このリポジトリで未設定の担当をセットアップして`

レビューだけの依頼では編集しない。自律開発でも、委譲や外部操作は利用者とリポジトリの指示に従う。

## 初回設定

Python 3.11以上で [セットアップ補助](references/setup.md)の診断を行う。`<skill-root>` はこの配布物、`<project>` は対象リポジトリの絶対パスに置き換える。

```sh
python3 <skill-root>/scripts/setup.py check --project <project>
python3 <skill-root>/scripts/setup.py install --project <project>
```

補助は既存の共有入口を再利用し、7担当を配置する。入口がない場合だけリンクを追加する。共有リンクと共有先のファイルは変更しない。配置の検査と、Codexによるスキル・担当の検出および起動は別に確認する。

## 内容の場所

| 場所 | 用途 |
| --- | --- |
| [SKILL.md](SKILL.md) | 一つの入口と手順選択 |
| [references/pstack/](references/pstack/index.md) | 開発の内部手順、23作業手順、必要時に読む資料 |
| [references/thermos/](references/thermos/guide.md) | 二方向レビューと統合した報告 |
| [references/review.md](references/review.md) | レビューの開始・修正・再確認 |
| [references/setup.md](references/setup.md) | 初回配置、更新、取り外し、旧配置の移行 |
| `assets/agents/` | 初回補助がコピーする7担当の設定 |
| `scripts/pstack/` | 計画・記録・作業状態・PR監視などの実行補助 |

付属の実行補助で使うBun、GitHub CLIなどは、その手順を使うときに確認する。常駐する指示や外部スキルの一括読み込みは追加しない。

## 出典と保守

著者・利用条件・固定した版は [NOTICE.md](NOTICE.md)、ファイルの対応は [provenance.json](provenance.json)、検査方法は [SYNC.md](SYNC.md)。現在の検証範囲は [validation/integration.md](validation/integration.md)に記録する。
