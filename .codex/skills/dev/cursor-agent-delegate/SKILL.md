---
name: cursor-agent-delegate
description: |
  事前設計が必要な中〜大規模作業について、repositoryを調査し、依存関係・設計境界・task難度・worker/model・UI/UX契約・統合順・完了条件を持つsingle-md実行計画を `docs/PLAN/{YYMMDD}_{slug}.md` に作成してから実行する。局所実装はheadless Cursor CLI、高・中難度taskはrouting policyでmodelを明示したCodex subagent、共有境界・統合・最終判断はmain Codexが担う。短期作業は対象外。Trigger: cursor-agent-delegate、Cursorで計画、worker委任計画、依存関係やUI受け入れを設計して実装
---

# cursor-agent-delegate

main Codex が、永続的な実行計画の作成、worker選定、進捗管理、統合、最終検収を一貫して担う。

## 適用範囲

複数module・stage・worker、shared contract、migration、production barrierなど、実装前に依存関係と統合順を固定する必要がある作業に使う。現在のworking tree内で完了でき、永続planが不要な短期作業は`cursor-agent-sprint-cli`へ切り替える。永続的なチェックリストは必要だが、owner/model、task graph、write conflict、integration batchの事前設計までは不要な作業は`simple-plan`へ切り替える。

## 参照先

- 計画の土台: [templates/plan.md](templates/plan.md)
- task種別・難度・modelのsource of truth: [references/task-routing.json](references/task-routing.json)
- 委任prompt: [references/delegation-prompt-template.md](references/delegation-prompt-template.md)
- Cursor CLIの実行: [references/operations.md](references/operations.md)
- 成果の検収: [references/review-checklist.md](references/review-checklist.md)

## 原則

- task graphとstatus boardを実行順・進捗のsource of truthにする。
- taskにはgoal、dependencies、routing classと理由、owner/model、read/write scope、acceptance、worker/main verificationを持たせる。
- shared boundary・integration・production・最終判断は難度に関係なくmain Codexへ置き、残るtaskだけをrouting policyで高・中・低へ分類する。
- write scopeが重なるworkerを並列実行しない。shared contractとintegration batchはmain Codexが扱う。
- UIを変更するplanは、影響surface、利用者の目的と主要flow、既存design system/pattern、必要な状態とfeedback、interaction/accessibility、リスクに応じたvisual verificationを契約化する。参照UIが実在する場合だけsourceと意図的な差を記録し、viewport、theme、evidence形式はrepositoryやproductの要件を優先する。
- workerにplan更新、完了判定、commit、push、merge、PR、branch切替を任せない。
- Cursor CLI preflightをplan taskにしない。CLI疎通失敗時だけ例外処理として実行する。
- 既存の未コミット変更を戻さず、worker reportではなくdiffと検証結果で採否を決める。

## 実行フロー

### 1. 設計対象を調査する

ユーザーの依頼とrepositoryを読み、目的、対象外、現状、設計判断、shared contract、検証方法、UI影響と参照sourceを確定する。未解決の判断がtask graphを変える場合は、plan作成前に調査またはユーザー確認を行う。

### 2. planを初期化する

日付と短いslugを決め、同名planがないことを確認してtemplateをコピーする。

```bash
WORKSPACE="$(pwd)"
SKILL_DIR="$WORKSPACE/.codex/skills/dev/cursor-agent-delegate"
"$SKILL_DIR/scripts/init_plan.sh" --workspace "$WORKSPACE" --slug <slug>
```

### 3. planを設計する

生成したsingle-md planを編集する。[task-routing.json](references/task-routing.json)の`policy_id`をplanへ記録する。routingは`main ownership boundary → task_type_defaults → high_escalation_signals`の順に判定し、`low`は`low_route_required_conditions`をすべて満たす場合だけ選び、それ以外のbounded taskは`medium`にする。解決したrouting class、理由、worker、model、reasoning effortをplanへ記録する。UI影響がある場合は、影響surface、user flow、既存pattern、状態、interaction/accessibility、visual verificationをtask contractへ対応付ける。task graph、write-scope conflict、integration batch、acceptanceを整合させ、Ready/Blocked queueは別管理せずstatusとdependenciesから判断する。

### 4. 実行前レビューを行う

最初のworkerを起動する前に、依存関係の循環、未確定contract、write scope重複、検証不能なacceptance、routing class・owner・model未設定、UI taskのuser flow・主要state・verification欠落がないことを確認する。問題があればplanを直してから実行する。

### 5. task単位で実行する

dependenciesが完了したtaskだけを実行する。promptは[delegation-prompt-template.md](references/delegation-prompt-template.md)、Cursor CLIは[operations.md](references/operations.md)を使う。Codex subagentはplanに記録した`model`と`reasoning_effort`を起動引数へ設定する。

### 6. 検収・更新・統合する

[review-checklist.md](references/review-checklist.md)で検収し、main Codexだけがstatus、decision log、検証結果をplanへ反映する。worker完了順ではなくintegration batch順に統合する。

### 7. 完了を判定する

required task、integration batch、completion criteria、最終検証が揃った場合だけ完了とする。残課題はriskまたはdeferred taskとしてplanへ残し、使用worker/model、変更、検証結果とともに報告する。
