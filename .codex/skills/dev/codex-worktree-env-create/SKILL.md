---
name: dev:codex-worktree-env-create
description: |
  Codex AppのWorktreeモード用にrepositoryを調査し、tracked
  `.codex/environments/environment.toml`、setup／Actions、project skillを
  作成・修復・実Worktree検証する。Worktree setup、local environment、並行Dev、
  runtime／port／DB／storage分離、`.worktreeinclude`、shared symlink、依存導入、
  stale claim、Cleanup安全性の改善を依頼されたときに使用する。
---

# codex-worktree-env-create

対象project固有のCodex App Local Environmentを、複数Worktreeで安全かつ再現可能な
状態まで作る。manifestやhelperの存在だけで完了扱いにせず、base上の可用性、並行実行、
状態分離、異常終了後の復旧、Actionsの実動まで検証する。

## 必須成果物

対象に同等の既存形式がない限り、次をtracked fileとして作る。

- `.codex/environments/environment.toml`
- `.codex/local-environment/setup.sh`または`.codex/scripts/<helper>.sh`
- `.codex/skills/project/worktree-env/SKILL.md`
- ignored通常fileの継承が必要な場合はrepository rootの`.worktreeinclude`

`environment.toml`は`version = 1`、project `name`、`[setup]`、根拠のある
`[[actions]]`を含める。helperだけを作ってApp側の手動登録へ委ねない。

## 実行規約

- 可能なら1つのsubagentへ[`agents/repository-discovery.md`](agents/repository-discovery.md)
  を渡して読み取り専用調査を任せ、mainが結果を査読する。利用不能ならmainが同じ調査を行う。
- repository規約、runtime pin、package manager、既存scripts、platform CLIを優先する。
- secret本文を読んだり生成したりしない。ignored fileとsymlinkは明示whitelistだけを扱う。
- setupは冪等・非破壊にし、deploy、remote migration、production upload、長時間serviceを含めない。
- Devまたはmutable local resourceがあるprojectは、parallel-safeを既定の設計目標にする。
- cleanupはprimary、unborn、保護branch、不正owner／namespaceで停止する。detachedでは破壊的
  Cleanupを既定拒否し、Codex-managed Worktree削除後のshared claimは安全なstale回収で扱う。
- Actionsはlocal-onlyを既定にする。remote mutationは確認付きの別workflowへ分離する。
- ユーザーが指定しない限りcommit、push、base統合を行わない。

## Step 1: repositoryと実行時副作用を調査する

調査Taskへrepository絶対path、target base、ユーザー制約、既知stack、編集禁止、secret
非表示を渡す。次を査読する。

1. current checkout、target base、primary、Codex-managed detached、Permanent Worktreeが区別されている
2. manifest、setup、Actions、runtime pin、package commandが実在fileを根拠にしている
3. tracked／ignored通常file／ignored symlink／dependency／cache／bulk seed／mutable state／external resourceが分類されている
4. server startup時のmigration、job復旧、backfill、cache生成、metadata更新が確認されている
5. Web、API、worker、DB、queue、storage、browser origin、containerの分離要否がある
6. `.worktreeinclude`候補とshared symlinkの依存先が秘密本文を読まずに整理されている
7. filesystemとOSにCOW／reflink能力があるか、非対応時のfallbackが明記されている
8. cleanup対象、残存し得るshared claim、remote／browser／authなど削除禁止対象が分かれている

dirty checkoutだけでbaseを推測しない。`git show <base>:<path>`、`git ls-tree`などで
成果物とpinがtarget baseに存在するか確認する。

## Step 2: isolation matrixとlifecycleを確定する

必ず[`references/artifact-patterns.md`](references/artifact-patterns.md)を読み、対象に必要な
patternだけを採用する。少なくとも次を明示する。

- resourceごとの`tracked | include | recreate symlink | shared cache | COW seed | isolated mutable | external namespaced`
- setupをsourceするか、全Actionをruntime-aware wrapperへ通すか
- Worktree固有state、port pair、container／DB namespace、browser origin
- stateのversion、`pending -> ready`、atomic write、operation lock、crash recovery
- shared claimのowner情報と、Worktreeが消えた後のstale回収条件
- source checkoutを`CODEX_SOURCE_TREE_PATH`優先で解決し、common Git directoryとprimaryを照合する方法
- `.env`、local DB、大容量mediaを継承／seedする根拠と残るrisk

不明なmutable resourceを共有扱いにしない。共有する場合はread-onlyまたはprocess間安全である
根拠を記録する。

## Step 3: runtimeとdependenciesを非ログインshell対応にする

- `.node-version`、`.tool-versions`、mise／asdf／nodenv等のpinからruntime実体を解決する。
- interactive shellのPATH、alias、shimだけを前提にしない。
- Actionsも同じruntime-aware wrapperへ通す。
- `FORCE_COLOR`由来のANSIを数値判定へ混ぜない。
- dependency directoryはWorktreeごとに作り、package managerのcontent-addressable store／cache
  だけを共有する。`node_modules`等をcopy／symlinkしない。
- lockfile固定installを使い、install済みなら再実行しない。

## Step 4: project固有環境を実装する

- manifest、config、package scripts、CIから実在するDev／Test／Lint／Typecheck／Buildを選ぶ。
- ignored通常fileは`.worktreeinclude`を優先する。Codexはsource symlinkをcopyしないため、
  ignored symlinkはsetupで全targetをpreflightしてから不足分だけ再作成する。
- Web／API／workerの全portを一組でatomic claimし、起動時はstrict portを使う。
- startup mutationが触る全保存先をWorktreeごとに分離する。
- 大容量seedは同一filesystemのCOW／reflinkを優先し、staging、anchor確認、atomic renameを使う。
- DB／container／emulatorが実在するときだけ固有namespaceを導入する。
- browser storageは固有originで分離し、Cleanupでは削除しない。

## Step 5: 静的検証する

最低限、次を実行する。

```bash
git status --short
bash -n <setup-or-helper>
git diff --check
```

さらに次を確認する。

- manifestをTOML parseし、version／name／setup／Actionsを検証する
- helper、package script、runtime pin、`.worktreeinclude`がtarget baseで利用可能である
- scriptのexecute bit、最小PATH、対応が必要ならOS標準shellでも成立する
- ignored fileはGit ignore対象で、secret本文がlogやdiffへ出ていない
- shared symlinkはtargetが存在し、競合時に上書きせず停止する
- state／claim schema、port範囲、namespace、realpath／symlink guardが整合する
- setup再実行でstate、port、seed、symlinkが変化しない
- cleanupがprimary、保護branch、不正owner／namespace、稼働中listenerを拒否する

## Step 6: 実WorktreeでE2E検証する

target baseから一時Worktreeを作る。未commit成果物は正確なdiffと新規fileだけをcandidateへ
反映し、検証commitや既存ユーザーWorktreeへ依存しない。

1. manifestとhelperが存在し、Codex-managed相当のignored file継承を再現できる
2. setupが最小PATHで成功し、runtime、dependency、symlink、state、seedが揃う
3. setup再実行でchecksumと割当が不変である
4. Devがある場合はHTTP／listener／proxyを確認する
5. Test／Lint／Typecheck／Buildなど登録Actionを実行する
6. 起動processを停止し、listenerが残らないことを確認する
7. cleanup guard、symlink競合、破損state等の重要negative caseを確認する
8. tracked差分、primary data、remote resource、別Worktreeが変化していないことを確認する

Dev、listener、startup mutation、mutable stateのいずれかがある場合、2つのWorktreeを同時に
setup／起動する。固有port、固有origin、一方だけの書込み、片方のCleanup後も他方が動くことを
確認する。検証後はprocess、candidate Worktree、branch、claimを安全に片付ける。

Codex-managed Worktreeはdetachedであるため、setup／Actionsがdetachedでも動くことを確認する。
破壊的Cleanupをdetachedで拒否する設計では、owner path不存在・Git worktree未登録・listener
不在・正しいclaim schemaをすべて満たすstale claimだけを将来setupが回収できることを確認する。

## 判定と報告

最低限、次を分ける。

- `Worktree Environment`: manifest、setup、runtime、dependency、継承、分離、並行実行、Action配線、cleanup
- `Repository Checks`: Test／Lint／Typecheck／Buildのコード診断

正しいActionが既存コード診断を返した場合、環境はPASS、Repository ChecksはFAILとする。

```text
Worktree Environment: PASS
Repository Checks: FAIL (lint: existing code diagnostics)
```

## 完了条件

- [ ] repository discoveryとisolation matrixをmainが査読した
- [ ] manifest、helper、project skill、必要な`.worktreeinclude`がtarget baseで利用可能である
- [ ] runtime、dependencies、ignored file、shared symlinkが最小PATHで成立する
- [ ] startup mutationを含む全mutable resourceが必要な境界で分離されている
- [ ] state transaction、operation lock、port claim、stale回収が定義・検証されている
- [ ] setupの冪等性と登録Actionsを実Worktreeで検証した
- [ ] 必要なprojectでは2 Worktree同時実行と書込み分離を検証した
- [ ] Worktree EnvironmentとRepository Checksを別々に判定した

## Resources

- [Repository discovery task](agents/repository-discovery.md)
- [Artifact patterns](references/artifact-patterns.md)
