# Diagram Selector

Mermaid は計画規模ではなく、仕様に含まれる構造で選ぶ。必要な図だけを書く。図を増やすこと自体を目的にしない。

## Selection Rules

| 構造 | Mermaid | 使う条件 |
| --- | --- | --- |
| 画面、ユーザー導線、操作入口 | `flowchart TD` / `flowchart LR` | UI や画面遷移が実装判断に関わる |
| API、非同期処理、外部サービス、保存処理の時系列 | `sequenceDiagram` | 呼び出し順、責務境界、失敗点を理解する必要がある |
| DB、永続化モデル、エンティティ関係 | `erDiagram` | schema、migration、保存設計が中核 |
| 状態遷移 | `stateDiagram-v2` | draft/published、capture lifecycle、job status など状態が仕様の中心 |
| Gate、work package、依存関係 | `flowchart TD` / `flowchart LR` | 実行順、並列可能性、review-fix の流れを見せる |
| 期限、段階リリース、長期計画 | `gantt` | 日付・フェーズが意思決定に必要な場合のみ |

## Defaults

- 依存関係図は generated 領域で Gate から自動生成する。
- authored の「アーキテクチャ詳細」では、タスク理解に効く図だけを選ぶ。
- 小さいタスクでも DB が中核なら `erDiagram` を使う。
- 大きいタスクでも DB に触らないなら `erDiagram` は使わない。
- `gantt` は通常不要。期限や外部マイルストーンが実装順に影響するときだけ使う。

## Quality Bar

- 図はコードレベル詳細ではなく、責務、境界、流れ、状態を示す。
- 図のノード名は人間が読むラベルにし、実装ファイル名だけの羅列にしない。
- 図と Gate 契約が矛盾してはいけない。
- 図で説明した重要な境界は Gate の `constraints` または `acceptanceCriteria` にも反映する。
