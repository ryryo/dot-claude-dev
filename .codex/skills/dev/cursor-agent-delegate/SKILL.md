---
name: cursor-agent-delegate
description: |
  事前設計が必要な中〜大規模作業を対象に、repositoryを調査したうえで、依存関係・設計境界・task難度・worker/model・UI/UX契約・統合順・完了条件を盛り込んだsingle-md実行計画を `docs/PLAN/{YYMMDD}_{slug}.md` に作成し、それに沿って実行する。局所的な実装はheadless Cursor CLIに、高・中難度のtaskはrouting policyでmodelを明示したCodex subagentに委任し、共有境界・統合・最終判断はmain Codexが担う。短期作業は対象外。Trigger: cursor-agent-delegate、Cursorで計画、worker委任計画、依存関係やUI受け入れを設計して実装
---

# cursor-agent-delegate

main Codex が、永続的な実行計画の作成、worker選定、進捗管理、統合、最終検収を一貫して担う。

## 適用範囲

複数のmodule・stage・workerが絡み、shared contract、migration、本番反映の障壁などが伴う作業のように、実装前に依存関係と統合順を固定しておく必要がある場合に使う。次のようなケースでは別のskillに切り替える。

- working tree内で完結し、永続planを必要としない短期作業 → `cursor-agent-sprint-cli`
- 永続的なチェックリストは必要だが、owner/model・task graph・write scopeの重複・integration batchまでの事前設計は不要な作業 → `simple-plan`

## 参照先

- 計画の土台: [templates/plan.md](templates/plan.md)
- task種別・難度・modelのsource of truth: [references/task-routing.json](references/task-routing.json)
- 委任prompt: [references/delegation-prompt-template.md](references/delegation-prompt-template.md)
- Cursor CLIの実行: [references/operations.md](references/operations.md)
- 成果の検収: [references/review-checklist.md](references/review-checklist.md)

## 原則

- task graphとstatus boardを実行順・進捗のsource of truthにする。
- taskにはgoal、dependencies、routing classと理由、owner/model、read/write scope、acceptance、worker/main verificationを持たせる。
- 共有境界・統合・外部変更・最終判断は難度に関係なくmain Codexへ置き、残るtaskだけをrouting policyで高・中・低へ分類する。
- write scopeが重なるworkerを並列実行しない。shared contractとintegration batchはmain Codexが扱う。
- UIを変更するplanでは、影響surface、利用者の目的と主要flow、既存design system/pattern、必要な状態とfeedback、interaction/accessibility、リスクに応じたvisual verificationをtask contractとして明文化する。参照UIが実在する場合はsourceと意図的な差分だけを記録し、viewport・theme・evidence形式はrepositoryやproductの要件を優先する。
- workerにplan更新、完了判定、commit、push、merge、PR、branch切替を任せない。
- Cursor CLI preflightをplan taskにしない。CLI疎通失敗時だけ例外処理として実行する。
- 既存の未コミット変更を戻さず、worker reportではなくdiffと検証結果で採否を決める。

## 実行フロー

### 1. 設計対象を調査する

ユーザーの依頼とrepositoryを読み込み、目的、対象外、現状、設計判断、shared contract、検証方法、UI影響と参照sourceを確定する。未解決の判断がtask graphに影響する場合は、planを作成する前に追加調査を行うか、ユーザーに確認する。

### 2. planを初期化する

日付と短いslugを決め、同名planがないことを確認してtemplateをコピーする。

```bash
WORKSPACE="$(pwd)"
SKILL_DIR="$WORKSPACE/.codex/skills/dev/cursor-agent-delegate"
"$SKILL_DIR/scripts/init_plan.sh" --workspace "$WORKSPACE" --slug <slug>
```

### 3. planを設計する

生成したsingle-md planを編集する。

- [task-routing.json](references/task-routing.json)の`policy_id`をplanへ記録する。
- routingは`main ownership boundary → task_type_defaults → high_escalation_signals`の順に判定する。`low`は`low_route_required_conditions`をすべて満たす場合だけ選び、それ以外のbounded taskは`medium`にする。
- 解決したrouting class、理由、worker、model、reasoning effortをplanへ記録する。
- UI影響がある場合は、影響surface、user flow、既存pattern、状態、interaction/accessibility、visual verificationをtask contractへ対応付ける。
- task graph、write-scope conflict、integration batch、acceptanceの内容に矛盾がないよう整合させる。Ready/Blocked queueは別管理せず、statusとdependenciesから判断する。

### 4. 実行前レビューを行う

最初のworkerを起動する前に、次の問題がないことを確認する。問題があればplanを修正してから実行する。

- 依存関係の循環
- 未確定のcontract
- write scopeの重複
- 検証不能なacceptance
- routing class・owner・model未設定
- UI taskにおけるuser flow・主要state・verificationの欠落

### 5. task単位で実行する

dependenciesが完了したtaskだけを実行する。promptの作成には[delegation-prompt-template.md](references/delegation-prompt-template.md)、Cursor CLIの実行には[operations.md](references/operations.md)を使う。Codex subagentを起動する際は、planに記録した`model`と`reasoning_effort`を起動引数に設定する。

### 6. 検収・更新・統合する

[review-checklist.md](references/review-checklist.md)で検収する。status、decision log、検証結果をplanへ反映できるのはmain Codexだけである。統合はworkerの完了順ではなく、integration batch順に行う。

### 7. 完了を判定する

planのcompletion criteriaに沿って、required taskの完了（理由付きのdeferredを含む）、integration batchのacceptance、最終検証という3点がすべてそろって初めて完了とする。残った課題はriskまたはdeferred taskとしてplanに記録し、報告時にはどのworker/modelを使ったか、何を変更したか、どう検証したかを明記する。
