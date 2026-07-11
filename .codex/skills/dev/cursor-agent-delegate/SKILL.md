---
name: cursor-agent-delegate
description: |
  main Codex が実装・調査・レビュー作業の worker と model を選定する。Codex subagent は `gpt-5.6-sol`、`gpt-5.6-terra`、`gpt-5.5` から作業特性に合わせて選び、範囲限定の局所実装やテストは headless Cursor CLI worker に委任できる。統合と最終判断は main Codex が担う。worker 選定、subagent model 選定、作業分割、Cursor CLI 委任、並列 worker、差分検収を行うときに使う。
---

# cursor-agent-delegate

main Codex を orchestrator・reviewer・integrator とし、タスクごとに `main-codex`、`codex-subagent`、`cursor-cli-agent` のいずれかを選ぶ。委任は手段であり、分割によって待ち時間または認知負荷が実際に減る場合だけ行う。

## 参照先

- worker の判断が自明でない場合: [references/worker-selection.md](references/worker-selection.md)
- Codex subagent を候補にした場合: [references/model-selection.md](references/model-selection.md)
- worker prompt を作る場合: [references/delegation-prompt-template.md](references/delegation-prompt-template.md)
- Cursor CLI worker を投入・監視する場合: [references/operations.md](references/operations.md)
- Cursor CLI の submit / monitor が失敗した場合: [references/troubleshooting.md](references/troubleshooting.md)
- worker の成果を受け入れる場合: [references/review-checklist.md](references/review-checklist.md)

## 絶対ルール

- worker 選定を先に行う。基本的な実装は、Cursor が担当する。Cursorが苦手な領域のみをCodex がカバーする。
- Codex subagent を選ぶ場合は model も同時に選ぶ。分割表や委任メモに worker だけを書いて model を省略しない。
- model は task の難易度、中心作業、失敗時の影響、並列数から選ぶ。すべてを最大 model に寄せず、安さだけで品質要件を下げない。
- ユーザーが model を明示した場合は、その model が現在の起動 schema で利用可能なら選定ルールより優先する。
- worker には独立した 1 タスクだけを渡す。goal、read scope、write scope、禁止事項、検証方法を明示できない作業は委任しない。
- 複雑な domain logic、設計比較、深い調査、難しい review は `codex-subagent` を優先する。
- 既存パターンに沿う局所実装、pure function、adapter、validator、unit test は `cursor-cli-agent` の候補にする。
- 低リスクで範囲限定できる repository 内の実装、調査、定型確認は、Codex subagent model を選ぶ前に `cursor-cli-agent` を優先する。
- shared contract、横断的な state / routing / auth / migration、最終統合は `main-codex` が扱う。
- 複数 worker の write scope を重ねない。少しでも重なる場合は直列化するか main Codex が扱う。
- worker に planning / progress 更新、完了判定、commit、push、merge、PR、branch 切替を任せない。
- worker の報告だけで受け入れない。main Codex が diff、実ファイル、検証結果を確認する。
- 既存の未コミット変更やユーザーの作業を元に戻さない。
- Cursor IDE、Agent Window、CDP、AppleScript、deeplink を操作経路として使わない。

## 実行ステップ

### 1. 作業境界を定義する

ユーザーの goal と repository context を確認し、委任候補ごとに次を定義する。

- 具体的な成果 1 件
- 最初に読むファイル
- 編集してよいファイル
- 触ってはいけないファイルと操作
- worker と main Codex が行う検証

定義できない場合は分割せず main Codex が扱う。

### 2. worker と model を選定する

[references/worker-selection.md](references/worker-selection.md) の判断表に従い、各タスクを `main-codex`、`codex-subagent`、`cursor-cli-agent` のいずれかに割り当てる。まず Cursor CLI で安全に閉じる task かを判定し、該当しない `codex-subagent` task だけ [references/model-selection.md](references/model-selection.md) に従って model と reasoning effort を決める。worker 起動と回収のコストが直接実装より大きい小作業は main Codex が扱う。

分割内容は最低限この形式で書く。

```text
Task ID | Worker | Model | Reasoning | Mode | Goal | Write scope | Verification
T10     | codex-subagent | gpt-5.6-terra | medium | read-only | ... | none | ...
T20     | cursor-cli-agent | composer-2.5-fast | fixed | edit | ... | src/... | ...
```

### 3. 委任内容を作る

[references/delegation-prompt-template.md](references/delegation-prompt-template.md) を使い、1 prompt に 1 タスクだけを書く。Codex subagent prompt には選定した `Model:` と `Reasoning effort:` を書く。Cursor CLI prompt には一意な `Task Summary:` と `Task ID:` を含める。

### 4. 実行・回収する

`cursor-cli-agent` を選んだ場合は [references/operations.md](references/operations.md) に従い、同梱 script で submit / monitor する。通常フローに preflight を追加しない。CLI 疎通に失敗した場合だけ [references/troubleshooting.md](references/troubleshooting.md) の例外処理を使う。

`codex-subagent` を選んだ場合は、起動直前に現在の subagent schema で model が利用可能か確認し、選定した `model` と `reasoning_effort` を明示して起動する。prompt に書いた値と起動引数を一致させる。read-only の調査・review を優先し、編集を許可する場合は write scope を明示する。

### 5. 検収・統合する

worker 完了後に [references/review-checklist.md](references/review-checklist.md) を読み、scope、diff、報告、検証結果を main Codex が確認する。範囲外変更や不十分な成果はそのまま採用せず、main Codex が修正、再委任、棄却を判断する。

### 6. 報告する

worker type、実際に使った model と reasoning effort、変更ファイル、検証結果、採用または棄却の判断、残課題を簡潔に報告する。model を変更または fallback した場合は理由も報告する。最終的な完了判断は main Codex が行う。
