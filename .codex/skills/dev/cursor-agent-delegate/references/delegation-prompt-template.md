# Worker prompt

1つのpromptには1つのbounded taskだけを書く。実装と補助workstreamを同じpromptへ混在させない。

## Cursor実装

Cursor promptは先頭に一意な`Task Summary:`を置き、`Task ID:`を含める。

```text
Task Summary:
<task id、担当領域、成果物が分かる180文字以内の文>

Worker: cursor-cli-agent
Model: composer-2.5-fast
Reasoning effort: fixed
Routing policy: <policy_id>
Work kind: implementation
Difficulty: <low | medium>
Execution route: cursor
Route reason: <満たしたcursor_required_conditions>
Workspace: <absolute path>
Task ID: <unique id>

Goal:
<具体的な成果1件>

Read first:
- <absolute path>

Write scope:
- Allowed: <separated paths>
- Forbidden: allowed scope外、planning / progress、commit、branch、remote、未許可のlockfile / generated file

Fixed contract / reference:
- <main Codexが固定した決定、既存pattern、sample>

Constraints:
- 既存の未コミット変更や担当外の変更を戻さない。
- 設計やshared contractを変更せず、必要になった場合は停止して報告する。
- <task固有の制約>

Verification:
- Run: <specific command>
- 実行できない場合は理由と代替確認を報告する。

Final report:
- TASK_ID / MODEL
- 変更ファイルと要約
- 検証結果
- main Codexに残した判断・作業
```

### UI blockの追記

taskが`UI: surface`の場合だけ、上のpromptへ次の3blockを追記する。`<>`部分はplanの`## UI foundation`から**具体値を転記する**。「UI foundationに従う」とだけ書かない。workerはplanを読まない前提で書く。

```text
UI components (これ以外を新規に作らない):
- <UI要素>: <import path>
- <UI要素>: <import path>

UI tokens:
- 使用してよい: <token list>
- 使用禁止: <legacy token / 生palette色 / hardcoded hex,rgb,oklch>

UI labels / i18n:
- 表示文字列は <namespace> へ追加し、<locale list> をすべて埋める。文字列を直書きしない。
- 利用者向けlabelへ内部ID、enum識別子、schema field名、例外message原文を出さない。
- testを書く場合、表示文言でassertせず data-testid か role + 安定key で参照する。

UI layout:
- 新規surfaceの配置: <panel内 / dialog / overlay / banner>
- 次の共通surfaceは自分で作らず <path> をimportする: <primary/secondary/destructive action, error, success, loading, empty, disabled, 承認surface のうち該当するもの>

UI forbidden (追加):
- 上のUI componentsに対応がある要素を、素の<button> <select> <input> <textarea>や独自実装で新規に作ること
- 上のUI tokensのallowlist外の色指定
- 上のUI layoutで他taskが所有すると書かれた共通surfaceの再実装
- 上の配置方針から外れるsurfaceの新設

UI verification (追加):
- Run: <S1 command>
- Run: <S2 command>
- Run: <S3 command>
- Run: <S4 command>
- Run: <S5 command>
- いずれかが0件でない場合は修正するか、停止して該当箇所と理由を報告する。

UI final report (追加):
- 使用したcomponentとtokenの一覧
- S1〜S5の結果
- UI componentsやtokensで表現できず独自実装した箇所と、その理由
```

`UI / UX contract: not_applicable`のplan、または`UI: -`のtaskではこのblockを付けない。付ける場合は`not_applicable`と1行書いて済ませず、blockごと省く。

## Codex subagentの補助workstream

subagent promptには実装を含めず、source writeを禁止する。modelとreasoning effortはplanと起動引数で一致させ、利用できない場合はfallbackせずmainへ返す。

```text
Worker: codex-subagent
Model: <gpt-5.6-sol | gpt-5.5>
Reasoning effort: high
Routing policy: <policy_id>
Work kind: support
Difficulty: <high | medium>
Execution route: <support_subagent_high | support_subagent_medium>
Route reason: <allowed work type and concrete parallel/context-isolation benefit>
Workspace: <absolute path>
Task ID: <unique id>

Question:
<mainの進行中の推論と独立して答えられるbounded question>

Read scope:
- <absolute paths / logs / sources>

Write scope:
- Allowed: none
- Forbidden: source、plan、progress、commit、branch、remote、external stateの変更

Evaluation criteria:
- <比較軸、正確性基準、確認すべき反例>

Constraints:
- mainの結論を推測せず、source evidenceから独立に評価する。
- raw logをそのまま返さず、根拠をpathや観測結果と対応付ける。
- 実装案は提案に留め、ファイルを編集しない。

Final report:
- TASK_ID / MODEL / REASONING_EFFORT
- Evidence
- Conclusion
- Uncertainty / counterexamples
- Recommendation to main Codex
```

main Codexはsubagentの報告をそのまま採用せず、根拠を確認してDecision logまたはtask contractへ反映する。
