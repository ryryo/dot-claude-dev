---
name: cursor-agent-delegate
description: |
  事前設計が必要な中〜大規模作業について、repositoryを調査し、依存関係・設計境界・worker/model・統合順・完了条件を持つsingle-md実行計画を `docs/PLAN/{YYMMDD}_{slug}.md` に作成してから実行する。局所実装はheadless Cursor CLI、複雑な実装・調査・レビューはmodelを明示したCodex subagent、共有境界・統合・最終判断はmain Codexが担う。短期作業は対象外。Trigger: cursor-agent-delegate、Cursorで計画、worker委任計画、依存関係を設計して実装
---

# cursor-agent-delegate

main Codex が、永続的な実行計画の作成、worker選定、進捗管理、統合、最終検収を一貫して担う。

## 適用範囲

複数module・stage・worker、shared contract、migration、production barrierなど、実装前に依存関係と統合順を固定する必要がある作業に使う。現在のworking tree内で完了できる短期作業には使わず、`cursor-agent-sprint-cli`へ切り替える。

## 参照先

- 計画の土台: [templates/plan.md](templates/plan.md)
- workerとmodelの選定: [references/selection.md](references/selection.md)
- 委任prompt: [references/delegation-prompt-template.md](references/delegation-prompt-template.md)
- Cursor CLIの実行: [references/operations.md](references/operations.md)
- 成果の検収: [references/review-checklist.md](references/review-checklist.md)

## 原則

- task graphとstatus boardを実行順・進捗のsource of truthにする。
- taskにはgoal、dependencies、owner/model、read/write scope、acceptance、worker/main verificationを持たせる。
- write scopeが重なるworkerを並列実行しない。shared contractとintegration batchはmain Codexが扱う。
- workerにplan更新、完了判定、commit、push、merge、PR、branch切替を任せない。
- Cursor CLI preflightをplan taskにしない。CLI疎通失敗時だけ例外処理として実行する。
- 既存の未コミット変更を戻さず、worker reportではなくdiffと検証結果で採否を決める。

## 実行フロー

### 1. 設計対象を調査する

ユーザーの依頼とrepositoryを読み、目的、対象外、現状、設計判断、shared contract、検証方法を確定する。未解決の判断がtask graphを変える場合は、plan作成前に調査またはユーザー確認を行う。

### 2. planを初期化する

日付と短いslugを決め、同名planがないことを確認してtemplateをコピーする。

```bash
WORKSPACE="$(pwd)"
SKILL_DIR="$WORKSPACE/.codex/skills/dev/cursor-agent-delegate"
"$SKILL_DIR/scripts/init_plan.sh" --workspace "$WORKSPACE" --slug <slug>
```

### 3. planを設計する

生成したsingle-md planを編集する。[selection.md](references/selection.md)に従ってtaskごとのworker、model、reasoning effortを決め、task graph、write-scope conflict、integration batch、acceptanceを整合させる。Ready/Blocked queueは別管理せず、statusとdependenciesから判断する。

### 4. 実行前レビューを行う

最初のworkerを起動する前に、依存関係の循環、未確定contract、write scope重複、検証不能なacceptance、owner/model未設定がないことを確認する。問題があればplanを直してから実行する。

### 5. task単位で実行する

dependenciesが完了したtaskだけを実行する。promptは[delegation-prompt-template.md](references/delegation-prompt-template.md)、Cursor CLIは[operations.md](references/operations.md)を使う。Codex subagentはplanに記録した`model`と`reasoning_effort`を起動引数へ設定する。

### 6. 検収・更新・統合する

[review-checklist.md](references/review-checklist.md)で検収し、main Codexだけがstatus、decision log、検証結果をplanへ反映する。worker完了順ではなくintegration batch順に統合する。

### 7. 完了を判定する

required task、integration batch、completion criteria、最終検証が揃った場合だけ完了とする。残課題はriskまたはdeferred taskとしてplanへ残し、使用worker/model、変更、検証結果とともに報告する。
