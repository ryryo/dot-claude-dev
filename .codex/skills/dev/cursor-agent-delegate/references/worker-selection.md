# worker の選定

作業単位ごとに、次の順で判断する。

1. main Codex が保持すべき判断か。
2. 独立した worker task として境界を固定できるか。
3. repository 内で範囲限定できる低リスク作業として Cursor CLI に渡せるか。
4. Cursor CLI に渡せない場合、深い推論や Codex 固有 context / tool が必要か。
5. Codex subagent の場合、どの model と reasoning effort が適切か。
6. 起動・回収・検収を含めても委任する価値があるか。

| Worker | 選ぶ条件 | 選ばない条件 |
| --- | --- | --- |
| `main-codex` | 要件が曖昧、shared contract、横断 state、auth、routing、migration、統合、最終判断 | 独立して並列化でき、委任効果が明確な作業 |
| `codex-subagent` | 複雑な domain logic、algorithm、設計比較、深い調査、risk analysis、難しい review、Codex 固有 context / tool が必要な分析 | Cursor CLI で安全に完結する repository 内の低リスク作業 |
| `cursor-cli-agent` | write scope が狭い局所実装、pure function、adapter、validator、unit test、機械的変更、範囲限定の repository 調査・inventory | 仕様が曖昧、複数領域を横断、設計判断が主、Codex 固有 context / tool が必要 |

## 判断ルール

- 5 分程度で main Codex が安全に終えられる単純作業は、worker 起動の固定費を考慮して main Codex を優先する。
- repository 内で完結し、scope と検証を固定できる低リスク task は `cursor-cli-agent` を優先する。同じ task を `gpt-5.6-terra` に割り当てない。
- 調査結果によって次の実装方針が変わる場合は、まず `codex-subagent` に read-only 調査を渡し、main Codex が次を決める。
- `codex-subagent` を選んだら [model-selection.md](model-selection.md) に従い、worker 名と同じ行に model と reasoning effort を書く。
- `cursor-cli-agent` には、コマンドで受け入れ条件を判定できる実装を渡す。
- 並列化は write scope が完全に分離している場合だけ行う。shared file、shared schema、同じ UI surface を触る task は同時実行しない。
- 同じ workspace を共有する前提で、他 worker とユーザーの変更を戻さないよう prompt に明記する。
- worker の出力は main Codex が review するまで未検収として扱う。

## 典型例

| 作業 | Worker | Model | Reasoning |
| --- | --- | --- | --- |
| 新しい認可境界の設計と統合 | `main-codex` | inherited | inherited |
| 既存認可実装の重大リスク調査 | `codex-subagent` | `gpt-5.5` | `high` |
| 難しい race condition の bounded fix | `codex-subagent` | `gpt-5.6-sol` | `high` |
| 複数責務が絡む module 境界の設計調査 | `codex-subagent` | `gpt-5.6-terra` | `medium` |
| 独立した 20 module の定型 inventory | `cursor-cli-agent` | `composer-2.5-fast` | fixed |
| 仕様確定済み validator と unit test | `cursor-cli-agent` | `composer-2.5-fast` | fixed |
| 複数 worker 成果の conflict 解消 | `main-codex` | inherited | inherited |
| 既存 adapter と同型の adapter 追加 | `cursor-cli-agent` | `composer-2.5-fast` | fixed |
