# Artifact Patterns

対象projectの既存規約を優先し、必要なpatternだけを使う。

## 目次

- Codex App manifest
- Setup lifecycle
- Runtime and dependencies
- Resource classification
- Ignored files and shared symlinks
- State, ports, and stale claims
- Large local data
- DB, containers, and external resources
- Cleanup and detached worktrees
- Actions and validation

## Codex App manifest

tracked entrypointは`.codex/environments/environment.toml`とする。

```toml
version = 1
name = "project-name"

[setup]
script = ".codex/scripts/worktree-env.sh setup"

[[actions]]
name = "Dev"
icon = "play"
command = ".codex/scripts/worktree-env.sh dev"

[[actions]]
name = "Status"
icon = "info"
command = ".codex/scripts/worktree-env.sh status"
```

setupでexportを親shellへ残す必要がある場合だけhelperをsourceする。副作用を避けるなら全Actionを
runtime-aware wrapperへ通す。helperやproject skillだけを作ってApp登録を省略しない。

## Setup lifecycle

setupを次に分類する。

- safe default: runtime解決、whitelist継承、symlink復元、固有state／port作成
- conditional default: lockfile固定dependency install、COW seed
- explicit opt-in: local DB migration、container起動、重いcodegen
- prohibited: deploy、remote migration／seed、production upload、secret生成

setupはversion付きstateを持ち、複数resourceを作る場合は`pending -> ready`で管理する。
stagingへ書き、検証後にatomic renameする。operation lockはprocess終了で解放される
`lockf`／`flock`等を優先し、staleになるmkdir lockだけへ依存しない。

再setupは既存ready stateを再利用する。pending stateでは完成済みmarkerをadoptするか、厳密に
限定したstagingだけを除去して再試行する。ready stateのresource欠損は暗黙再生成せずfail-closedにする。

source checkoutは`CODEX_SOURCE_TREE_PATH`を優先する。fallbackはcommon Git directoryからprimary
候補を解決し、repository root、common directory、primary checkoutであることを照合する。
`git worktree list`の先頭を無条件にsourceとみなさない。

## Runtime and dependencies

Codex setupを非ログインshellとして扱う。

1. `.node-version`、`.tool-versions`、mise／asdf／nodenv等のpinを読む。
2. managerの既知install pathまたはproject-local toolchainから実体を解決する。
3. runtime `bin`をPATH先頭へ加え、versionをexact matchで検証する。
4. Actionsも同じwrapperを使う。

dependency directoryはWorktreeごとに作る。`node_modules`、virtualenv、bundle install先などを
primaryからcopy／symlinkしない。pnpm store、npm cache、Bundler cache、pip cache等、toolが
concurrent-safeに管理するcontent-addressable store／download cacheだけを共有する。

- lockfile固定installを使う
- dependency markerがあれば再installしない
- 同時setupでstore corruptionやlock競合がないことを確認する
- download数、reuse、所要時間を記録できる場合は報告する

`FORCE_COLOR`でANSIが入る出力を算術式へ直接渡さない。

## Resource classification

各resourceを次のいずれかへ分類する。

| 種別 | strategy | 例 |
|---|---|---|
| tracked | Git checkout | source、manifest、runtime pin |
| ignored regular | `.worktreeinclude` | `.env.local`、local config |
| ignored symlink | setupで再作成 | shared hooks、skills |
| shared cache | tool管理cacheのみ共有 | pnpm store |
| read-heavy seed | COW／reflink | media library、fixture |
| mutable local | Worktree固有root | JSON、SQLite、jobs、tmp |
| external mutable | 固有namespace | DB schema、queue prefix、bucket prefix |
| shared read-only | 明示根拠付き共有 | immutable SDK／model cache |

分類不能なmutable resourceは共有しない。source codeだけでなくserver startup、shutdown、reload、
mode切替が書き込むresourceも含める。

## Ignored files and shared symlinks

Codex-managed Worktreeで必要なignored通常fileはtracked `.worktreeinclude`へ明示する。

```text
.env.local
.dev.vars
.codex/config.toml
.codex/hooks.json
```

- sourceが存在しGit ignore対象であることを確認する
- secret本文を読んだりlogへ出したりしない
- tracked fileを列挙しない
- credentialがremote mutationを可能にする場合は、file継承とremote namespaceを別々に判断する
- manual `git worktree add`には適用されないため、E2EではCodex-managed相当のcopyを明示的に再現する

Codexは`.worktreeinclude`に一致するsource symlinkをskipする。ignored symlinkはsetupで再作成する。

1. repositoryごとの明示whitelistを持つ
2. primaryのsourceがsymlinkでtargetが実在することを検証する
3. absolute targetは同一machine限定と記録し、必要なら共有root envを優先する
4. 全source targetと全destination競合をpreflightする
5. destinationが同じsymlinkなら維持する
6. 異なるsymlink、broken link、通常file／directoryなら上書きせず停止する
7. preflight成功後に不足分だけ作る

tracked configがignored hook／skillを参照する場合、そのlinkを依存関係として必須扱いにする。
Statusはsecret本文を出さず、通常fileとsymlinkの`available | unavailable`だけを表示する。

## State, ports, and stale claims

Worktree固有値はignored stateへ固定し、shared Git directoryのclaimと対応付ける。

```text
STATE_VERSION=2
WORKTREE_ID=project-wt-abc123
WEB_PORT=4410
API_PORT=4411
DATA_STATUS=ready
```

- path hashだけでportを決めず、claimとlistenerを確認する
- Web、API、worker、DB等の派生portを一組でatomic claimする
- `lsof`等がなければ空きと推測せず停止する
- 起動直前にもlistenerを確認し、serverはstrict portを使う
- 初回割当後は再setupで変えない
- 固有originによってbrowser storageを分離する
- claimへowner path、Worktree ID、port pair、schema versionを記録する

WorktreeがCleanupなしで削除されてもshared claimは残り得る。setup時に次をすべて満たすclaimだけを
staleとして回収する。

- owner pathが存在しない
- `git worktree list --porcelain`にownerがない
- claimの全portにlistenerがない
- claim schema、owner ID、path、namespaceが正しい
- targetがcommon Git directory内の厳密なclaim pathでsymlinkではない

一条件でも不明なら回収しない。空のoperation lock fileはclaimと区別する。

## Large local data

bulk mediaやfixtureは、初期参照と変更後の保存境界を分けて考える。

- macOS／APFS: 同一filesystemで`cp -c`
- Linux: filesystem対応を確認して`cp --reflink=always`
- 非対応: full copy、empty seed、shared read-onlyから明示選択
- hardlink: 上書きが共有されるため既定禁止

COW／reflink seedは次を満たす。

- sourceとdestinationのdevice／filesystem capabilityを確認する
- mutable metadataと必要なmedia hierarchyだけをwhitelistする
- tmp、scratch、logs、cacheは空のWorktree固有directoryにする
- stagingへcloneし、代表anchorをbyte比較する
- ownership markerにschema、Worktree ID、sourceを記録する
- atomic rename後だけreadyへする
- 再setupでprimaryから再同期しない

directory cloneはvolume snapshotと同じ一括時点保証を持たない。primaryが書込み中なら、atomic file
write、immutable blob、server停止、revision付きexport等から整合性根拠を決めて記録する。

## DB, containers, and external resources

実在するときだけ設計する。

- SQLite／local JSON: Worktree固有rootまたはCOW seed
- PostgreSQL等: database／schema名をWorktree IDで分離
- Redis／queue／search: DB番号だけでなくprefix／index／consumer groupも分離
- object storage: local bucket rootまたは明示prefixを分離
- Compose: 固有`COMPOSE_PROJECT_NAME`とhost portを使う
- remote resource: setupで作成・migration・削除しない

同じcredentialを継承しても、remote mutationの安全性が成立するとはみなさない。

## Cleanup and detached worktrees

Cleanup前にbranch、Worktree、owner、listener、targetを検証する。

- primary、main／master／trunk、unborn、不正branchでは停止する
- targetのrealpathが専用namespace内にあることを確認する
- symlink化されたparent／targetを拒否する
- 別Worktree ownerや外部listenerを変更しない
- browser storage、remote resource、共有auth／cacheを削除しない
- data、claim、stateの順など、失敗後に再Cleanupできる順序を選ぶ

Codex-managed Worktreeは通常detachedである。setupと通常Actionsはdetachedで動作させる一方、
破壊的Cleanupをdetachedで許可するかは別契約にする。既定では拒否し、Appによるcheckout削除で
Worktree-local dataを破棄し、残ったshared claimは将来setupのstale回収で処理する。
Permanent Worktree等のbranch付きsecondary checkoutでは、全guard成立時だけCleanupを許可する。

## Actions and validation

既存manifest、package scripts、Makefile等に根拠があるActionだけを登録する。

基本候補: `Dev`、`Test`、`Lint`、`Typecheck`、`Status`

必要時: `Build`、`Cleanup`、platform local dev、local migration、Compose up／down

Deploy、remote migration、bucket／database作成を通常Actionへ登録しない。

### Static

- TOML／JSON parse
- helperのOS標準shellと利用runtime shellでの構文検査
- execute bit、tracked path、ignore provenance、symlink target
- minimal PATH runtime解決
- setup再実行時のstate／port／seed／symlink checksum不変
- `git diff --check`

### Real Worktree E2E

1. ignored通常file継承とshared symlink復元
2. symlink／state／claim競合のfail-closed
3. setupと再setup
4. Devのlistener、HTTP、proxy、固有origin
5. registered repository checks
6. listener停止とCleanup guard
7. primary／別Worktree／remoteの不変
8. candidate Worktree、process、branch、claimの後片付け

Dev、listener、startup mutation、mutable stateがある場合は2 Worktreeを同時にsetup／起動する。
一方だけのsentinelまたは安全なlocal mutationが他方とprimaryへ現れないことを確認する。

### Result classification

| 観測 | Worktree Environment | Repository Checks |
|---|---|---|
| setup／runtime／resource分離失敗 | FAIL | NOT RUNまたは影響範囲のみFAIL |
| Action command／path誤り | FAIL | NOT RUN |
| 正しいActionがcode diagnosticsを返す | PASS | FAIL |
| 環境とcode checksが成功 | PASS | PASS |

最終報告は最低限次を含める。

```text
Worktree Environment: PASS
Repository Checks: FAIL (lint: existing code diagnostics)
```
