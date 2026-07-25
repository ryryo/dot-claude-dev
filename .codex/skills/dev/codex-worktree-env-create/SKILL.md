---
name: dev:codex-worktree-env-create
description: |
  Codex App の Worktree モード用に、対象リポジトリを調査して tracked
  `.codex/environments/environment.toml`、setup script、Actions、
  project-specific setup/status/cleanup skill を作成・修復・検証する。
  Codex Worktree環境作成、local environment作成、setup scriptやActions作成、
  「環境が見つからない」、Worktree setup失敗、runtime/port/DB/Docker分離の
  改善を依頼されたときに使用する。
---

# codex-worktree-env-create

対象プロジェクト固有の Codex App Local Environment を、実際の Worktree で
再現可能な状態まで作る。setup helper だけで完了扱いにせず、Codex App が認識する
manifest、ベースブランチ上の可用性、Actions の実動まで検証する。

## 必須成果物

対象に既存の別形式がない限り、次を tracked file として作る。

- `.codex/environments/environment.toml`
- `.codex/local-environment/setup.sh` または `.codex/scripts/<helper>.sh`
- `.codex/skills/project/worktree-env/SKILL.md`

`environment.toml` は `version = 1`、project `name`、`[setup]`、根拠のある
`[[actions]]` を含める。setup helper や skill だけを作って
「App 側で手動登録が必要」として終了しない。

## 実行規約

- 1つのサブエージェントへ
  [`agents/repository-discovery.md`](agents/repository-discovery.md) を渡し、
  読み取り専用調査を任せる。利用不能または禁止時はメインが同じTaskを実行する。
- メインは調査結果を査読し、生成方針、編集、検証を担う。
- 対象リポジトリの規約、package manager、runtime pin、既存 scripts、
  container/platform CLI/env管理を優先する。
- 秘密情報の内容を読んだり生成したりしない。コピーは明示whitelistだけにする。
- setup は冪等・非破壊にし、deploy、remote migration、volume削除、
  長時間サービス起動を含めない。
- cleanup は detached/unborn、primary checkout、main/master/trunkなどの保護branchで停止し、
  完全に検証したWorktree namespaceだけを扱う。
- Actionsはlocal-onlyを既定にする。Deploy、remote migration、remote resource変更は
  ユーザーが明示した別workflowに分離する。
- ユーザーが指定しない限りcommit、push、base branchへの統合は行わない。

## Step 1: 実体とベースブランチを調査する

調査Taskに対象絶対パス、ユーザー制約、既知stack、編集禁止、秘密値非表示を渡す。
返却レポートを次の観点で査読する。

1. current checkout の事実と target base branch の事実が分離されている
2. manifest、setup、Actionsの既存形式と先行例が確認されている
3. runtime/package manager/dev/test/lint/typecheck/build が根拠付きである
4. DB、Redis、queue、search、storage、browser storage、port、volumeの分離要否がある
5. Web server、CLI、library、batch、container、複数appなど実在する構成が判別されている
6. whitelist候補と、それらに必要な `.gitignore` 規則が整理されている
7. 危険操作とcleanup対象が具体的に分離されている
8. 必要fileがtracked/ignored/generated/symlinkのどれか分類されている

現在のdirty branchだけを見て判断しない。新規Worktreeに指定するbase branchで
各成果物がtrackedかを `git show <base>:<path>` などで確認する。

## Step 2: 成果物を設計する

必ず [`references/artifact-patterns.md`](references/artifact-patterns.md) を読み、
対象に必要なpatternだけを採用する。

特に次を明示的に決める。

- `environment.toml` のsetupとActions
- setupをsourceしてexportを親shellへ残すか、全Actionをruntime-aware wrapper経由にするか
- Worktree固有値の保存先、port割当、既存Worktreeとの衝突検査
- ignored local fileのcopy whitelistと対応する `.gitignore`
- DB/container/local emulator/browser originなど、実在するresourceのnamespace
- statusで表示する値とcleanupで削除できる厳密な対象
- source checkoutの解決方法。`CODEX_SOURCE_TREE_PATH`を優先し、fallbackでは
  common git dirとprimary checkoutを照合して「最初のworktree」に依存しない
- secretを含む`.env`やlocal DBを自動copy/migrateするか。既定はopt-inにする

## Step 3: runtimeを非ログインshell対応にする

Codex App setup shellがユーザーのinteractive shellと同じPATHを持つと仮定しない。

- `.node-version`、`.tool-versions`、mise/asdf/nodenv、Ruby/Python pinを読む。
- setup時に必要なruntimeを明示的に解決する。
- setupのexportをActionsで必要とする場合は、manifestからhelperをsourceする。
- より堅牢にするなら、dev/test/lint/typecheck Actionsを同じruntime-aware wrapperへ通す。
- `FORCE_COLOR` でANSIが混ざる可能性があるため、数値出力を算術式へ直接渡さない。
- runtime pin自体がbase branchにtrackedであることを確認する。

## Step 4: project variantに合わせて実装する

存在しないサービスやコマンドを作らない。

- repository内のmanifest、config、scripts、CIからapplication typeと
  local development commandを決める。
- platform固有CLIやemulatorがある場合だけ、その公式docsとinstalled CLIの
  `--help`を確認する。特定vendorやhosting方式を前提にしない。
- containerを使う場合は固有project nameとhost portを使う。重いbuild/upは
  明示Actionに分ける。
- browser IndexedDB/localStorageは固有originで分離し、cleanupで削除しない。
- lint/testなど既存コードの失敗は、環境起動失敗と判定上も分離する。

## Step 5: 静的検証する

最低限、次を実行する。

```bash
git status --short
bash -n <setup-or-helper>
git diff --check
```

さらに以下を確認する。

- `environment.toml` がTOMLとしてparseでき、`version/name/setup/actions`を持つ
- setupとActionが参照するtracked file/package script/binstub/Compose configが存在する
- runtime pinとignored whitelistがbase branchにも存在する
- port範囲、namespace、state path、cleanup guardが整合する
- setup再実行で割当値とtracked状態が変わらない
- 最小PATHの非ログインshellでも正しいruntimeへ切り替わる
- JSON/TOMLがparseでき、実行対象scriptにexecute bitがあり、symlink targetが存在する
- cleanupがdetached/primary/protected branchと不正namespaceを確実に拒否する

## Step 6: 実WorktreeでE2E検証する

完了前にtarget base branchから一時Worktreeを作る。未commit成果物ならその正確な
diffと新規fileだけを一時Worktreeへ適用して、Codex App相当のsetupを実行する。
検証のためにcommitやbase統合を行わず、既存のユーザーWorktreeも破壊的に再利用しない。

1. manifestとhelperがWorktree内に存在する
2. setupが成功し、依存関係と固有stateが作られる
3. setupを再実行して冪等性を確認する
4. 登録Actionをrepository typeに応じて実行する
5. stateがWorktree配下または固有namespaceにだけ作られる
6. 起動したprocessがあれば正確に停止し、listenerを使う場合は残らない
7. test/lint/typecheck等があれば実行し、環境不良と既存コード不良を区別する
8. 検証前後で意図しないtracked差分がない
9. resource分離が必要なprojectだけ、複数Worktreeと競合時の挙動を検証する

Web/APIなどlistenerを持つActionでは割当portへのrequestを確認する。CLI/library/batchでは
代表commandのexit statusと出力artifact/stateの分離を確認する。

一時Worktreeは検証後に安全にremoveする。candidate E2Eとbase branch上の可用性は
分けて報告し、baseへ未統合なら「統合後に新規Worktreeで利用可能」と明示する。

## 判定と報告

単一の「総合PASS/FAIL」にrepository品質を混ぜない。最低限、次の2判定を出す。

- `Worktree Environment`: manifest認識、setup、runtime、依存関係、分離、Action配線、
  state containment、cleanupを判定する
- `Repository Checks`: test/lint/typecheck/buildのコード品質結果を判定する

Actionが正しいcommandを正しいruntimeで起動し、コード診断を返した場合、Action配線は
PASS、該当Repository CheckはFAILとする。コード診断だけを理由に
`Worktree Environment: FAIL`へしない。環境判定をFAILにするのは、setup不能、runtime
不一致、依存不足、resource衝突、誤command、起動不能、state漏洩、cleanup失敗など、
Worktree環境自身に原因がある場合だけとする。

最終報告では次の形式を使い、必要なら失敗したrepository commandと最小修正案を続ける。

```text
Worktree Environment: PASS
Repository Checks: FAIL (lint: existing code diagnostics)
```

## 完了条件

- [ ] repository discoveryをメインが査読した
- [ ] `.codex/environments/environment.toml` がtrackedでApp認識形式になっている
- [ ] setup/helperとproject skillがbase branch上に存在する
- [ ] runtime、package manager、ignored whitelistが非ログインshellで機能する
- [ ] 対象に実在するport/DB/container/emulator/storageの必要な分離が反映されている
- [ ] cleanupにbranchとnamespace guardがある
- [ ] setupの冪等性とActionsを実Worktreeで検証した
- [ ] Worktree EnvironmentとRepository Checksを別々に判定した

## Resources

- [Repository discovery task](agents/repository-discovery.md)
- [Artifact patterns](references/artifact-patterns.md)
