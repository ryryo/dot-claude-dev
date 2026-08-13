# Repository Discovery Task

対象repositoryのCodex App Worktree環境を設計するため、読み取り専用で事実を調査する。
fileを編集せず、secret、credential、`.env`の本文を読んだり出力したりしない。

## Input

- repository absolute path
- target base branch（未指定なら候補）
- user constraints
- known stack

## Required inspection

### Repository and Worktree lifecycle

- `git status --short --branch`
- `git worktree list --porcelain`
- current／default／target base branch
- primary、Codex-managed detached、Permanent Worktree、unborn、保護branch
- current checkoutとtarget baseにある`.codex`、runtime pin、manifest、platform configの差
- target成果物がbaseでtrackedか
- WorktreeがCleanupなしで削除された場合にshared namespace／claimが残るか

dirty checkoutだけでbaseを推測しない。必要なら`git show <base>:<path>`、`git ls-tree`を使う。

### Existing Codex and shared tooling

- `.codex/environments/environment.toml`
- `.codex/local-environment/`、`.codex/scripts/`、`.codex/skills/project/`
- `.worktreeinclude`、`.gitignore`
- `.codex/config.toml`、hooks、skills、Claude等のproject-local tooling
- tracked／ignored regular／ignored symlink／generated／absolute symlinkの分類
- tracked configからignored hook／skillへの参照
- symlink target rootの実在性と別machineでのportability risk

Codex-managed Worktreeでは`.worktreeinclude`がignored通常fileだけをcopyし、source symlinkを
skipする前提で、setupによるsymlink復元要否を報告する。

### Runtime and dependencies

- Node／Ruby／Python／Go等のversion pin
- package manager、lockfile、workspace、CI install command
- mise／asdf／nodenv／nvm／rbenv等のinteractive shell依存
- minimal PATHでruntimeを解決するための実体
- dependency directoryと共有可能なcontent-addressable store／download cache
- frozen／locked install commandとinstall済みmarker

### Commands, services, and startup mutations

- dev、test、lint、typecheck、build、preview
- appごとのport、strict／fallback動作、proxy、browser origin
- Web、API、worker、DB、Redis、queue、search、object storage、container、emulator
- startup／shutdown／reload／mode切替時のmigration、job復旧、backfill、poster生成、
  cache生成、metadata更新、expired state削除
- process内lockだけで共有dataの複数process書込みを調停できるか
- deploy、remote migration、upload等の外部変更

### Local resources and filesystem

各resourceを次へ分類する。

- tracked
- ignored regular file
- ignored symlink
- shared concurrent-safe cache
- read-heavy seed
- mutable local state
- external mutable resource
- shared read-only resource

さらに確認する。

- normal／fixture／test等のmode境界
- media、generated artifact、tmp、scratch、logs、local DBの容量と書込み性
- OS、filesystem、source／destination device、COW／reflink可否
- primaryからseed中にsourceが変化する可能性と整合性保証
- Worktreeで必要なignored whitelistとignore provenance
- copy／symlink／共有を禁止すべきcache、build output、browser profile、credential

secret本文は読まず、存在、file種別、ignore状態、参照元だけを報告する。

### State, claims, and cleanup

- Worktree ID、state path、port／namespace claimの保存先
- atomic claim、operation lock、`pending -> ready`、crash recovery
- claimに必要なowner path、Worktree ID、schema、port情報
- owner Worktree消失後のstale判定に使えるGit／listener事実
- cleanup対象と削除順
- primary、detached、保護branch、別owner、symlink target、稼働中listenerのguard
- browser storage、remote resource、共有auth／cache等の削除禁止対象

## Report format

1. `Detected facts` — file／commandを根拠に列挙
2. `Branch and lifecycle differences` — current、base、managed detached、Permanentの差
3. `Resource classification` — 全resourceの種別、容量、書込み性
4. `Isolation matrix` — shared／COW／isolated／external namespace、claim、cleanup可否
5. `Startup mutations` — 起動だけで変化するresourceとprocess間競合
6. `Runtime and dependencies` — pin、minimal shell、Worktree展開先、共有store
7. `Ignored files and symlinks` — include候補、link復元、ignore状態、依存元
8. `Manifest and Actions` — setup／Action候補と根拠
9. `Lifecycle and recovery` — transaction、lock、stale claim、detached cleanup
10. `Risks` — remote mutation、source整合性、destructive cleanup、portability
11. `Acceptance checks` — static、再setup、2 Worktree、negative、cleanupの具体検証
12. `Inferences` — 事実と分離した推測・未確認事項

## Acceptance check selection

- Dev／listenerがある: 2 Worktree同時起動、HTTP、proxy、固有originを確認する
- startup mutation／mutable stateがある: 一方だけの安全な書込みが他方とprimaryへ出ないことを確認する
- ignored regular fileが必要: Codex-managed相当の`.worktreeinclude`copyを確認する
- ignored symlinkが必要: source target、復元、冪等性、競合fail-closedを確認する
- bulk seedがある: COW／reflink能力、anchor、再setup不変、Cleanup分離を確認する
- shared claimがある: concurrent allocationとstale owner回収を確認する
- repository checksがある: environment判定とcode診断を分ける

秘密値、credential本文、`.env`本文は出力しない。
