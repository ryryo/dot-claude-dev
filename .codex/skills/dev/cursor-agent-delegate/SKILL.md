---
name: cursor-agent-delegate
description: |
  事前設計が必要な中〜大規模作業についてrepositoryを調査し、依存関係・設計境界・実装難度・実行主体・UI/UX契約・統合順・完了条件を持つsingle-md計画を `docs/PLAN/{YYMMDD}_{slug}.md` に作成して実行する。高難度・共有境界・統合はmain Codexが所有し、contractを固定できる低〜中難度の局所実装だけをheadless Cursor CLIへ委任する。Codex subagentは独立した調査・比較・監査・障害分析・レビューに限定する。Trigger: cursor-agent-delegate、Cursorで計画、worker委任計画、依存関係やUI受け入れを設計して実装
---

# cursor-agent-delegate

main Codexが計画、設計判断、worker選定、進捗管理、統合、最終検収を一貫して担う。

## 適用範囲

複数moduleやstageが絡み、実装前に依存関係、shared contract、統合順を固定する必要がある作業に使う。短期の局所作業には`cursor-agent-sprint-cli`、owner/modelやtask graphまで不要な永続チェックリストには`simple-plan`を使う。

## 参照先

- 計画template: [templates/plan.md](templates/plan.md)
- 実行主体・難度・modelのsource of truth: [references/task-routing.json](references/task-routing.json)
- worker prompt: [references/delegation-prompt-template.md](references/delegation-prompt-template.md)
- Cursor CLI操作: [references/operations.md](references/operations.md)
- 検収: [references/review-checklist.md](references/review-checklist.md)

## 所有と委任

難度と実行主体を別々に判定する。Codex subagentを高・中難度実装の一般的な委任先にしない。

1. **main Codex所有**
   高難度実装、設計判断、shared contract、public schema、migration、複数moduleの統合、共有state、外部変更、最終検収を扱う。
2. **Cursor実装**
   低〜中難度で、設計とcontractが固定され、write scopeを分離でき、既存patternや参照実装に従い、局所的に検証・棄却できる実装だけを扱う。条件を満たさないtaskはmainへ戻す。
3. **Codex subagentによる補助workstream**
   独立したコード調査、複数案・仮説の比較、read-only audit、test/log/障害原因分析、独立レビューだけを扱う。sourceを編集させず、mainが結果を要約・採否判断する。小さな調査や、前後の判断と密結合な分析はmainが直接行う。

subagentは実装taskのfallbackではない。Cursorが利用できない場合も、実装をsubagentへ自動的に振り替えない。

## UI / UX契約

UI変更を含むplanでは、次をtask contractへ簡潔に記録する。

- 影響surfaceと利用者の目的、主要flow
- 既存design system、component、interaction pattern
- loading、empty、error、disabled、success、recoveryなど必要な状態とfeedback
- keyboard、focus、pointer、semantics、accessibility
- riskに応じたbehavior test、browser操作、visual確認

product flow、複数surfaceのstate、重要なinteraction判断はmainが所有する。Cursorへ委任できるのは、既存patternとcontractが固定された局所UI実装だけである。subagentはUI調査、比較、audit、独立レビューに限る。参照UIがある場合はsourceと意図的な差分だけを記録し、viewport、theme、evidence形式はrepository固有の要件を優先する。

## 実行フロー

### 1. repositoryを調査する

目的、対象外、現状、設計境界、shared contract、UI影響、検証方法を確認する。task graphを左右する未解決事項は、追加調査またはユーザー確認で解消する。

### 2. planを初期化する

```bash
WORKSPACE="$(pwd)"
SKILL_DIR="$WORKSPACE/.codex/skills/dev/cursor-agent-delegate"
"$SKILL_DIR/scripts/init_plan.sh" --workspace "$WORKSPACE" --slug <slug>
```

### 3. task graphと契約を設計する

[task-routing.json](references/task-routing.json)を読み、次の順で各taskを解決する。

1. main ownership boundary
2. implementation difficulty
3. Cursor eligibility
4. 必要な場合だけsupport workstream eligibility
5. execution surface availability

planへ`policy_id`、work kind、difficulty、execution route、理由、owner、model/reasoning、read/write scope、acceptance、worker/main verificationを記録する。subagent taskには、並列化またはcontext隔離の具体的な利益と、mainが受け取る成果物を記録する。

### 4. 実行前レビューを行う

最初のworkerを起動する前に次を確認し、問題があればplanを修正する。

- 依存関係の循環、未確定contract、write scopeの重複
- 検証不能なacceptance、未設定のowner/model
- 高難度・共有境界・統合taskがworkerへ流れていないこと
- Cursor taskが必要条件をすべて満たすこと
- subagent taskが許可用途に該当し、source writeを持たないこと
- UI taskにuser flow、主要state、interaction/accessibility、verificationがあること

### 5. task単位で実行する

dependenciesを満たしたtaskだけを実行する。Cursor promptとsubagent promptは[delegation-prompt-template.md](references/delegation-prompt-template.md)に従う。Cursor CLIは[operations.md](references/operations.md)で実行する。

Codex subagentを起動する場合は、planに記録したmodelとreasoning effortを起動引数へ設定する。subagentにはtask-localなsourceと契約だけを渡し、mainの結論を先に教えない。

### 6. 検収・統合する

[review-checklist.md](references/review-checklist.md)でdiff、検証結果、worker reportを照合する。mainだけがplanのstatus、decision log、統合結果を更新できる。subagentの報告は根拠であり、設計判断や完了判定そのものではない。

### 7. 完了を判定する

required taskの完了または理由付きdeferred、integration batchのacceptance、最終検証がすべてそろったときだけ完了とする。残存課題はriskまたはdeferred taskとして記録する。

## 共通禁止事項

- workerにplan更新、完了判定、commit、push、merge、PR、branch切替を任せない。
- write scopeが重なるworkerを並列実行しない。
- worker reportだけで採否を決めず、既存の未コミット変更を戻さない。
- Cursor CLI preflightを通常taskにしない。CLI-level errorが起きた場合だけ実行する。
