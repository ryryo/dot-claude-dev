# Repository Discovery Task

対象リポジトリの Codex App Worktree 環境を設計するため、読み取り専用で事実を
調査する。ファイルを編集しない。秘密ファイルの内容を読まず、存在と用途だけを
報告する。

## Input

依頼promptから次を受け取る。

- repository absolute path
- target base branch（未指定なら候補を列挙する）
- user constraints
- known stack

## Required inspection

### Repository and branch

- `git status --short --branch`
- `git worktree list --porcelain`
- current branch、default/main branch、target base branch
- primary checkout、detached/unborn checkout、保護対象main/master/trunk
- current checkoutとbase branchで `.codex`、runtime pin、package manifest、
  platform/container configが異なるか
- target成果物がbase branchにtrackedか

dirty checkoutのファイルだけを根拠にbase branchの構成を推測しない。
必要に応じて `git show <branch>:<path>`、`git ls-tree` を使う。

### Existing Codex artifacts

- `.codex/environments/environment.toml`
- `.codex/local-environment/`
- `.codex/scripts/`
- `.codex/skills/project/`
- `.codex/config.toml`、hooks、shared symlink
- 同じ親directoryに先行セットアップ済みprojectがあれば、そのmanifest/setup形式
- 各必要fileがtracked/ignored/generated/symlinkのどれか。absolute symlinkなら
  他machine/cloneでのportability risk

先行例がなければ「なし」と明記し、canonical
`.codex/environments/environment.toml` patternを採用候補にする。

### Runtime and package manager

- Node/Ruby/Python/Goなどのversion pin
- package manifestの`packageManager`、lockfile、workspace宣言
- CIが使うinstall command
- interactive shell依存のruntime manager（mise/asdf/nodenv/nvm/rbenvなど）
- Codex Appの最小PATHでもruntimeを解決するために必要な実体

### Commands and services

- dev、test、lint、typecheck、build、preview
- appごとのportとstrict/fallback動作
- DB、Redis、queue、search、object storage、browser storage
- Docker Composeのproject/port/volume
- platform固有CLI/emulator/configが存在する場合、そのversion、config root、
  local/remote切替、永続state
- deploy、remote migration、uploadなどsetup/Actionsへ入れてはいけない外部変更

### Local files

- Worktreeで必要になるgitignored file/symlinkの厳密なwhitelist候補
- target branchの `.gitignore` が各候補を除外するか
- コピー禁止のcache、dependency、build output、database、credential

## Report format

次の見出しで返す。

1. `Detected facts` — path/commandを根拠として列挙
2. `Branch differences` — current checkoutとtarget base branchの差
3. `Isolation matrix` — resource、shared/isolated、namespace/port、claim方法、cleanup可否
4. `Runtime bootstrap` — pin、manager、minimal-shell対策
5. `Manifest and Actions` — environment.toml/setup/action候補と根拠
6. `Whitelist` — copy対象、ignore状態、copy禁止対象
7. `Risks` — deploy、remote data、destructive cleanup
8. `Acceptance checks` — 実Worktreeで行う具体的なsetup/action検証
9. `Inferences` — 事実と分離した推測・未確認事項

秘密値、credential本文、`.env`本文は出力しない。
