---
name: cursor-agent-sprint-cli
description: "独立した作業をheadless Cursor CLIへ委任し、一時Sprintで実行・監視・検収する。永続PLANが必要な場合はcursor-agent-delegateを使う。"
---

# Cursor Agent Sprint CLI（CLI 版軽量 Sprint）

boundedな worker sprint を Cursor CLI で実行する。sprint の状態は `.codex/tmp/{YYMMDD}_{slug}/` に閉じ込め、main Codex が作業を進めながら、独立して検証・棄却できる部分を Cursor CLI worker に渡す。

## Cursor能力の前提

Composer 2.5の適用範囲には、long-horizon task、multi-file change、数百tool call、testをoracleにしたfeature deletion/reimplementationを含める。Fast variantは発表上Standardと同じintelligenceとして扱う。[Composer 2.5](https://cursor.com/blog/composer-2-5)と[Composer model page](https://cursor.com/composer)を根拠とする。

Cursor実装には、固定contract、negative test、scope制限、mainによるdiff検収を必須とする。公称benchmarkの未達成caseと公式記事が報告するreward hackingを、この検収要件へ反映する。

## 委任判定

実行主体を次の全条件で決める。

1. **判断の確定度**: expected behavior、contract、invariant、禁止境界が固定済み、または選択肢とtie-break ruleがboundedである。
2. **実装の独立性**: task-localなsourceとpromptだけで完結し、mainや他workerとの反復判断を要しない。前後にmain Gateを置けば独立するtaskも含む。
3. **write scopeの隔離**: allowed pathを排他的に書け、投入中のmain、user、他workerと同じ変更単位を触らない。
4. **検証oracle**: focused test、fixture、typecheck、build、snapshot、dry-runなどで期待動作を再現可能に判定できる。partialならmainが確認する残りを限定できる。
5. **副作用と可逆性**: 未commitの局所diffとして棄却・補正できる。共有artifactならexclusive ownershipとrollbackを明記できる。
6. **参照可能性**: 既存pattern、参照実装、sample、fixture、testのいずれかを直接使える。

complexityは`low`、`medium`、`high`を許容し、prompt量、timeout、verification強度へ反映する。execution routeは上の6条件から決める。

未解決のarchitecture/product/security/data ownership判断、他taskと結合したwrite、弱く再現不能なoracle、production・外部設定・実data・課金・権限などローカルdiffで戻せない変更、最終acceptanceはmain Codexが扱う。

auth、secret、crypto、crash/retry/lease、外部providerなどのrisk modifierには、mainが固定するinvariant、negative case、禁止副作用、real secretやproduction stateを使わないoracle、局所rollbackを必須controlとして設定する。controlを満たす実装はCursor、満たせない実装はmainが所有する。

未解決判断または結合実装を含むtaskは、`main: contract/invariant/oracle固定 → Cursor: 参照駆動の実装shard → main: risk検証/統合`へ分割する。分割で同じsourceの往復編集が増える、またはcontext再構築と検収costが実装costを上回る場合はmainが一貫して所有する。

## 適用条件

Cursor CLIへの委任を依頼された場合、または呼び出し元がこの実行経路を選んだ場合に使う。通常の実装・調査依頼だけでは起動しない。上の条件を満たす独立taskがなければ Cursor CLI を起動せず、main Codex が直接作業する。複数日にまたがる作業や再開可能な計画管理が必要な場合は、適切な永続計画を使う。

複数の停止点を`docs/PLAN`のチェックリストで管理・再開したいが、詳細なtask graphまでは不要な場合はプロジェクトの既存計画形式を使う。shared contract、migration、複数worker/model、非自明な統合順の事前設計が必要な場合は`cursor-agent-delegate`を使う。

## 絶対ルール

- worker にversion control／remote操作、progress file 更新、最終完了判断を任せない。
- 実行主体は常に main Codex から考え始め、委任条件を満たす task だけ `cursor-cli-agent` に切り替える。
- 2 つ以上の worker の write scope を重ねない。
- ユーザーが明示しない限り、既存の未コミット変更を戻さない。
- Cursor CLI worker は `--yolo` で動く。final report は参考情報として扱い、diff と検証を main Codex が確認してから受け入れる。
- Cursor CLI model は `composer-2.5-fast` 固定。

## 実行と監視

委譲候補がある場合だけ[実行手順](references/execution.md)を読む。Sprint初期化、task契約、必須ラベル、prompt、submit、monitor、CLI障害時のpreflightはこの資料を正本とする。main-onlyならSprintを作らず通常の作業を続ける。

- モデルは`composer-2.5-fast`、実装は排他的scopeで実行する。
- `done: true`はworker実行の完了であり、採用は下のmain検収後に決める。
- 送信済みtaskはregistryから監視する。状態不明のまま同じtaskを重複投入しない。

## 検収と完了

### 受け入れ前に検収する

worker 完了後、main Codex は必ず確認する。

```bash
git status --short
git diff --name-only
git diff --stat
git diff -- <allowed paths>
```

確認項目:

- 変更ファイルが allowed write scope に収まっている。
- 複数 worker の write scope が重なっていない。
- 既存のユーザー変更または先行 agent 変更が戻されていない。
- final report と実際の diff が一致している。
- ユーザー視点で必要な振る舞いが完了している。
- worker verification が成功している。失敗または未実行なら、理由が具体的で受け入れ可能である。
- workerが未解決判断を追加しておらず、記録したdecision state、independence、side-effect scope、oracleと実diffが一致する。
- risk modifierがある場合、main固定のinvariantとnegative caseをmainが再実行している。

範囲外変更が見えた場合は、diff を見てから判断する。worker 由来で安全に直せると明確な場合だけ main Codex が修正してよい。ユーザーの変更かもしれない場合は触る前に確認する。

### 統合と検証

worker の完了順ではなく依存順に統合する。main Codex は共有 contract を解決し、リスクに見合う最小検証を実行する。

- 振る舞い変更: focused unit / integration test
- TypeScript / API surface 変更: `npm run typecheck`
- 影響範囲が広い変更: `npm test`
- app-level / routing 変更: `npm run build`
- UI 変更: 可能なら browser check

結果は `review.md` に記録する。diff、scope、report、検証が揃ってから task を accepted にする。

### 報告

最終報告には必要なものだけを書く。

- sprint directory path
- 使った worker type
- 変更ファイル
- 実行した検証と結果
- 棄却または修正した worker output
- 残リスクや follow-up

ユーザーに求められていない限り、内部 plan を長く説明しない。

## Optional: 大きな計画を sprint-cli 実行単位へ分割する

大きな実装計画や調査計画を実行する前に、ユーザーが`cursor-agent-sprint-cli でどう分けるか考えて`、`フェーズごとに sprint-cli したい`、`大きい計画を CLI worker に分割したい` などを求めた場合だけ使う。

この option は**実装ではなく分割設計**を行う。計画の source of truth を先に特定し、main Codex が sprint boundary を決める。ユーザー作業や外部設定が必要な場合は、sprint group、barrier、次 sprint group のように stage を分ける。

Cursor CLI preflight は sprint stage や task として事前配置しない。submit / monitor で CLI 疎通問題が出たときだけ、その場の復旧処理として差し込む。

詳細手順は `references/large-plan-sprint-division.md` を読む。
