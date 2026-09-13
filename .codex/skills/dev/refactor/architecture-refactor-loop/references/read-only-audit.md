# Read-only architecture audit

監査のみの依頼に適用する。実装用の作業記録やgoalは作らない。

- repositoryと指定scopeをfreshに読み、編集、進捗file作成、テスト／build実行、Cursor CLI、Gitの状態変更、外部作用を行わない。
- 許容された既存差分を`git status --short`で確認し、baselineと現在差分の両方を監査する。
- 実行入口、データフロー、state owner、副作用／resource、public contract、module境界、依存方向、test seamをmapにする。
- 責務境界、依存方向、state ownership、副作用、contract保護、test seam、runtime riskを一件目で止めずに一巡する。
- 行数、命名、好み、到達不能な推測だけをfindingへ昇格させない。
- audit agentは採否、goal化、実装、完了判定をせず、一回のfresh reportを返して停止する。

出力には次を含める。

1. 実際に確認したscopeとpath
2. architecture map
3. 全観点のfinding sweep
4. findingごとのseverity、path／line、到達する因果経路、破られるcontractまたはarchitecture pain、最小修正境界、既存oracle
5. 既に差分で直っている問題、却下／deferした候補と理由

追加のP0／P1／P2がなければ`NO_FINDINGS`とする。read-only audit modeはここで終了する。
