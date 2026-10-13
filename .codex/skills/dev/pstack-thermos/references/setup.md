# 初回セットアップの補助

対象プロジェクトの既存のスキル入口を再利用し、7担当を配置する。入口がない場合だけリンクを追加する。Python 3.11以上を使う。`<skill-root>` はこの `SKILL.md` があるディレクトリ、`<project>` は既に存在する作業リポジトリの絶対パスに置き換える。

## 診断と配置

```sh
python3 <skill-root>/scripts/setup.py check --project <project>
python3 <skill-root>/scripts/setup.py install --project <project>
```

`check` はファイルを書き換えない。`.codex/skills/dev/pstack-thermos` または管理外の `.codex/skills/pstack-thermos` が同じ配布物を参照していれば、その入口を再利用する。`skills/dev` や `skills` 自体が共有リンクでも、共有先へ書き込まない。

`install` は `.codex/agents/` に7担当、`.codex/pstack-thermos/install.json` に管理対象とハッシュを配置する。既存の入口を再利用できない場合だけ、`.codex/skills/pstack-thermos` にこの配布物へのリンクを追加する。モデルと思考量は親から継承し、レビュー担当を読み取り専用にする。

設定済みなら不足・変更を診断し、管理外の設定や利用者が変更した担当設定を保持する。競合があれば全体の適用前に停止し、具体的なパスを報告する。配置途中で失敗した場合は、変更前の管理対象へ戻す。

## 更新・旧配置の移行・取り外し

```sh
python3 <skill-root>/scripts/setup.py update --project <project>
python3 <skill-root>/scripts/setup.py uninstall --project <project>
```

`update` は管理記録と現在の内容を照合し、変更されていない管理対象だけを更新する。共有入口がある場合は、この補助が以前に配置した重複リンクも外す。利用者が作成したリンクは管理対象へ取り込まず保持する。

以前の補助が同じ配布場所の `pstack` から配置した記録があれば、その記録で所有を確認し、旧入口を外してthermosの2担当も配置する。共有入口がなければ新入口を追加する。新旧両方の記録、別の配布元、競合する管理外の設定がある場合は停止する。旧配置への `install` では移行せず、診断後の `update` を案内する。

`uninstall` はこの補助が管理し、配置後に変更されていないファイルとリンクだけを外す。再利用した入口と共有先は管理記録へ含めず、更新・取り外しでも変更しない。作業データや無関係な設定は削除しない。配布物を別の場所へ移した場合は、記録との照合が必要になるため、移動前に取り外す。

## プロジェクトでまだスキルを読めない場合

このスキルを読めるチャットからスクリプトを直接実行する。どのプロジェクトからも入口を呼べるようにする依頼がある場合だけ、ユーザー共通の配置へ進む。既定では対象プロジェクトだけを変更する。

```sh
python3 <skill-root>/scripts/setup.py install --scope user
```

共通の配置先は `CODEX_HOME`、未指定なら `~/.codex`。補助は対象プロジェクトの信頼設定を共通の `config.toml` から読み取るだけで、自動的に信頼を付与しない。

## Codexでの検出・起動を確認する

新しいチャットで `$pstack-thermos` を呼び出す。実際の担当一覧に、`poteto-agent`、`comment-sicko`、`pstack_skeptic`、`pstack_architect`、`pstack_minimalist`、`thermos_correctness`、`thermos_quality` が出るかを確認する。

委譲と試験が許可されている場合は、読み取り専用の限定試験で各担当の起動・応答・終了を確認する。未実施ならそのまま記録する。`check` の「配置済み」はファイルの確認結果であり、担当が実際に呼び出せたことを意味しない。

専用担当を使わず汎用担当へ指示を渡す経路もある。モデル・思考量・並列数の調整を依頼された場合は [setup-pstack](pstack/setup-pstack/guide.md)へ進む。設定名と値は現在の実行環境で確認する。
