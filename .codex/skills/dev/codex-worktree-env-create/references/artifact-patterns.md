# Artifact Patterns

Codex Worktree 用の local environment、Actions、project-specific skill を作るときの設計パターン。
対象プロジェクトの既存規約を優先し、ここにある内容は候補として適用する。

## Local Environment Setup Script

setup script は Worktree 作成直後に自動実行されるため、軽量・冪等・非破壊にする。

入れてよい処理:

- gitignored ファイルの whitelist コピー
- package manager の存在確認
- 依存関係が未インストールの場合だけの軽量 install
- 初回に必要な軽い build/codegen
- `.envrc` の Worktree 専用マーカー付きブロック更新
- direnv/mise/asdf などの有効化に必要な非破壊コマンド

避ける処理:

- DB volume 削除
- migration/seed の自動実行
- 長時間の Docker build / compose up
- 秘密情報ファイルの生成
- 全 gitignored ファイルの一括コピー
- ユーザーのローカル設定を上書きする処理

whitelist コピーの対象例:

```text
.envrc
.env.local
.env.development.local
.tool-versions
.mise.local.toml
```

`node_modules`、`vendor/bundle`、`.next`、`tmp`、cache 類は、プロジェクトのサイズと package manager の性質を見て判断する。
コピーする場合も whitelist に明示し、全 `.gitignore` 対象を広くコピーしない。

## Worktree 固有 env

Worktree 固有値は、手書き設定と共存できるようマーカー付きブロックで管理する。

```sh
# codex-worktree-env start
export COMPOSE_PROJECT_NAME=...
export APP_PORT=...
export DB_NAME=...
# codex-worktree-env end
```

port は次のいずれかで決める。

- 既存プロジェクトの規約に従う
- ブランチ名または Worktree path から hash で決める
- 空き port を検出して `.envrc` に固定する

hash 方式は再現性が高いが衝突がありうる。
空き port 検出方式は衝突に強いが、Worktree を作り直すと値が変わりうる。

## Docker Compose と DB

Docker Compose を使うプロジェクトでは、`COMPOSE_PROJECT_NAME` を Worktree ごとに分けることを標準候補にする。
Compose project name を分けると、container、network、volume の namespace を分離しやすい。

DB がある場合に検討する値:

- `COMPOSE_PROJECT_NAME`
- host port
- app DB name
- test DB name
- Redis DB number または key prefix
- queue prefix
- search index prefix
- local storage bucket / path prefix

DB がない場合は、DB 関連の env や cleanup を作らない。
依存関係、env ファイル、dev server port、build cache の扱いに絞る。

## Actions

Actions は人間と Codex が繰り返し使うコマンドだけにする。
既存の package scripts、Makefile、binstubs、Compose file に根拠があるものを登録する。

基本候補:

- `dev`
- `test`
- `lint`

必要に応じた候補:

- `typecheck`
- `build`
- `db:migrate`
- `db:seed`
- `compose up`
- `compose down`
- `compose logs`

長時間の初期化や破壊的 cleanup は Actions より project-specific skill 側に置き、確認手順とガードを明記する。

## Project-specific Worktree Skill

既存分類がなければ、スキル名は `project:worktree-env`、生成先は `.codex/skills/project/worktree-env/SKILL.md` 相当を推奨する。

含める手順:

- setup: Worktree 固有 env、direnv/mise/asdf、DB 作成、migration など
- status: branch、port、Compose project、DB、container、volume の確認
- cleanup: container/volume/cache/branch などの片付け

setup は繰り返し実行できるようにし、`.envrc` などはマーカー付きブロックで更新する。
cleanup は main/master 上で停止し、削除対象 namespace が特定できない場合は自動削除しない。

## Cleanup Guards

cleanup には最低限以下の確認を入れる。

```sh
branch="$(git rev-parse --abbrev-ref HEAD)"
case "$branch" in
  main|master)
    echo "Cannot run cleanup on $branch" >&2
    exit 1
    ;;
esac
```

Docker volume や DB を削除する場合は、対象が Worktree 固有の `COMPOSE_PROJECT_NAME` または prefix に属していることを確認する。
確認できない資源は一覧表示までに留め、削除はユーザーに任せる。

## Validation

生成後は、対象に応じて以下を確認する。

```bash
bash -n <script>
ruby -e 'require "yaml"; YAML.load_file(ARGV.fetch(0))' <yaml-file>
rg 'codex-worktree-env start|codex-worktree-env end' <env-or-script>
```

Actions や skill が参照するコマンドは、実行前に package scripts、Makefile、binstubs、Compose file などで存在確認する。
