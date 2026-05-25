---
name: dev:codex-worktree-env-create
description: |
  Codex App の Worktree モードを各プロジェクトで安全に運用するため、
  リポジトリ構成を調査して local environment setup script、Actions、
  project-specific worktree setup/cleanup skill を設計・生成する。

  Trigger:
  codex-worktree-env-create, Codex Worktree環境作成, local environment作成,
  Worktree用setup script作成, Worktree用Actions作成, Codex worktree env create
user-invocable: true
---

# codex-worktree-env-create

Codex App の Worktree モードをプロジェクトごとに運用できる形へ整える。
共通テンプレートを押し付けず、対象リポジトリの runtime・DB・Docker・env 管理・開発コマンドを読んで、そのプロジェクト専用の `.codex` 成果物を作る。

## ゴール

- Worktree 作成直後に必要な環境初期化を local environment setup script として用意する。
- Codex App から頻繁に実行する dev/test/lint などを Actions として設計する。
- DB・Redis・queue・search・storage・port など、Worktree 並列実行で衝突する資源を分離する。
- setup/status/cleanup を扱う project-specific worktree skill を作る。
- 生成物に秘密情報を含めず、破壊的 cleanup には明確なガードを置く。

## 基本方針

- 調査は `agents/repository-discovery.md` の Task へ切り出す。このスキルでは 1 つのサブエージェントにリポジトリ全体の調査を任せ、メインセッションは調査結果の査読、生成方針、編集を担う。
- サブエージェントが利用できない環境、またはユーザーが明示的に禁止した場合は、メインセッションが同じ Task 仕様を読み、編集せずに調査する。
- 対象プロジェクトの既存規約を優先する。`.codex`、AGENTS/CLAUDE 系ルール、package manager、Docker Compose、env 管理、既存 scripts を先に読む。
- setup script は軽量・冪等・非破壊にする。DB 起動、migration、volume 削除など時間がかかる処理や危険操作は、原則 project-specific skill または Actions に分ける。
- `.env`、API key、credential などの秘密情報は生成しない。必要な場合は、既存ファイルの存在とコピー方針だけを扱う。
- Worktree 固有値はマーカー付きブロックで管理し、手書き設定と共存させる。
- 破壊的操作は main/master 上で停止し、削除対象 namespace を特定できる場合だけ実行対象にする。

## 実行手順

### Step 1: 調査 Task を起動する

`agents/repository-discovery.md` を使って、対象リポジトリの Worktree 運用に必要な事実を調査する。

サブエージェント実行手段が利用できる場合は、この Task 仕様を 1 つの worker prompt として渡す。
利用できない場合は、メインセッションが同じ Task 仕様を読み、編集せずに調査だけを実行する。

依頼には最低限以下を含める。

- 対象リポジトリの絶対パス
- ユーザー指定の制約や優先事項
- 既に分かっている技術スタック
- ファイル編集を行わないこと
- 秘密情報の中身を読まず、存在と用途だけ報告すること

### Step 2: 調査結果を査読する

返ってきたレポートを読み、以下を確認する。

1. 検出事実と推測が分離されている
2. DB・Redis・queue・search・storage・port・volume の分離要否が明記されている
3. dev/test/lint/typecheck などの実行コマンドが根拠付きで示されている
4. Worktree に必要な gitignored ファイルが whitelist 候補として整理されている
5. 危険操作と cleanup 対象が具体的に分けられている

不足があれば、調査 Task に不足観点を指定して再調査させる。

### Step 3: 生成方針を決める

`references/artifact-patterns.md` を読み、対象プロジェクトに合わせて生成物を決める。

標準の生成対象は以下。

- local environment setup script
- Codex App Actions
- project-specific worktree skill

既存 `.codex` 設定がある場合は、その形式を優先して追記・更新する。
形式が不明な場合は、既存ファイルを壊さず、ユーザーに Codex App 側で雛形生成が必要であることを報告する。

### Step 4: 成果物を作成する

対象プロジェクトの構成に合わせて、必要なファイルだけを作る。

project-specific skill は、既存分類がなければ `project:worktree-env` として `.codex/skills/project/worktree-env/SKILL.md` 相当を推奨する。
本文には setup/status/cleanup の手順を含め、DB がないプロジェクトでは DB 関連手順を作らない。

local environment setup script には、Worktree 作成直後に自動実行して安全な処理だけを入れる。
Actions には、人間と Codex が繰り返し使う dev/test/lint などを入れる。

### Step 5: 検証する

生成後に以下を確認する。

```bash
git status --short
```

該当ファイル種別に応じて、以下も実行する。

```bash
bash -n <setup-script>
ruby -e 'require "yaml"; YAML.load_file(ARGV.fetch(0))' <yaml-file>
```

さらに、Actions や project-specific skill が参照するコマンドが package scripts、Makefile、binstubs、Compose file などに実在することを確認する。
危険操作は main/master ガード、namespace ガード、削除対象の明示があることを確認する。

## 完了条件

- [ ] `agents/repository-discovery.md` の調査結果をメインセッションが査読している
- [ ] setup script が軽量・冪等・非破壊で、秘密情報を生成しない
- [ ] Actions が既存コマンドに基づいている
- [ ] project-specific worktree skill に setup/status/cleanup の手順がある
- [ ] DB・Redis・queue・search・storage・port の分離要否が反映されている
- [ ] cleanup に main/master ガードと削除対象 namespace の確認がある
- [ ] YAML 構文、shell 構文、参照コマンド、危険操作ガードを検証している

## References

- [agents/repository-discovery.md](agents/repository-discovery.md)
- [references/artifact-patterns.md](references/artifact-patterns.md)
