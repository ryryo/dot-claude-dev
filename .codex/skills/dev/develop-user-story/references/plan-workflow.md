# PLANの作成と独立レビュー

PLANを新規作成・意味変更するとき、またはPLAN独立レビューGateを担当するときに読む。レビュー済みのストーリーを、別の実装者が開始・検証できる実装契約へ変換する。実行だけの依頼は[実装と停止条件](implementation.md)へ進む。

## 成果と実装契約を固定する

解決した台帳と同じscopeのtemplateを使う。repository直下では`docs/PLAN/_TEMPLATE.md`、project-localでは同階層の`_PLAN_TEMPLATE.md`を優先する。候補が複数または存在しない場合は、独自形式を作る前に確認する。

PLANは独立してhandoffできる成果で切る。単一成果なら一枚にし、複数成果が見込まれる場合だけ[並列PLAN設計](parallel-plan-execution.md#1-分割可否を先に判定する)で分割可否を決める。USとPLANは一対一でなくてよいが、条件ID単位の追跡を保つ。

実装前に次を固定する。

- **契約**：担当US・条件ID、Goal、制約、対象外。PLANの都合で条件を追加・弱体化しない。
- **実行**：開始条件、依存順、read／write scope、Phaseの完了状態、停止Gate、handoff成果と受け取り先。
- **検証**：条件と`例:`を判定するcommand、実画面・実サービス確認、証拠、最終状態を更新するowner。
- **作用の境界**：現在の導線から到達する外部作用、権限、費用、永続状態、共有ownerに必要な承認・失敗状態・復旧手順。一般的なrisk一覧を展開しない。

既存承認の対象と有効範囲を確認し、未承認の作用だけを未完了にする。依存しない準備は進める。契約を変える必要が出たら、実装で迂回せず[入口の再開規則](../SKILL.md#gateの再開と状態)へ戻る。

## 条件に応じて設計を補う

| 条件 | 読む資料と完了要件 |
| --- | --- |
| PLANを新規作成、または実行責務を意味変更する | [推奨実行設定](plan-execution-settings.md)。各PLANの冒頭にmodel、推論レベル、選定理由、見直し条件を置く |
| 適用指示、REFERENCE、dependency管理、現行実装が再利用候補を示す | [再利用判定](reuse-assessment.md)。方式を決める前に対象sourceと利用側を確認する |
| 複数PLANへ分割する | [並列PLAN設計](parallel-plan-execution.md)。実行PLAN群と進行PLANを一度に揃え、Parallelization Topology Gateを通す |

候補が示されず、現行実装と条件からも再利用可能性がなければ、その根拠だけを短く記録する。単一PLANにはTopology manifestを要求しない。

PLANは実装順・進捗の正本とし、台帳へ実装チェックリストを複製しない。branch、commit SHA、worktree、port、session等の実行識別子とcontent digestは計画・review metadataへ入れない。外部sourceの版・licenseはREFERENCE、EVIDENCE、noticeまたはdependency管理を参照する。

## PLAN独立レビューGate

PLANを実装入力として固定する前に、作成者ともストーリーレビュー担当とも異なるエージェントを1名以上立ち上げる。判定質問は「別の実装者が、利用者契約を変えずに実装し、完了を再現可能な方法で検証できるか」。`$review-gate`を使い、[入口のReview Input](../SKILL.md#レビューへ渡す契約)を渡す。

一次情報はレビュー済み台帳、template、対象PLAN、関連実装・テスト・設計資料とする。再利用や複数PLANが適用される場合は、対応資料と検証結果も渡す。要約や作成者が選んだ一ファイルだけへ入力を狭めず、採否結論を前提にしない。

レビューでは次を確認する。

- 条件IDと各`例:`を、Phase、Gate、検証へ追跡でき、未確認を完了扱いしていない。
- 開始条件・担当・依存・停止位置が現行repositoryと一致し、同じ契約を通るroute、API、background処理、session、cache、保存先などの責務が漏れていない。
- 通常導線と適用される例外導線を検証できる。自動テスト、実画面、実サービス、証拠を使い分け、mockや静的語句で実結果を代用していない。
- 現在到達する外部作用・費用・秘密情報・個人情報・破壊的操作の承認境界と、安全な失敗状態が明確である。

推奨実行設定は各PLANの責務・可用性に照合する。再利用判断は[独立照合](reuse-assessment.md#独立レビューで採否を照合する)、複数PLANは[plan set review](parallel-plan-execution.md#6-plan-set-review)で固有の確認を行う。plan setは進行PLANと全実行PLANを同じreviewerが横断し、一度のGateで判定する。

現在の契約に必要な条件追跡、設定、開始条件、owner、承認、oracle、参照source、DAGの欠落・不一致を`fix-here`とする。内部設計の好み、将来規模への対応、別USの改善は指摘にしない。PLANで既存Storyを実現できず契約判断が必要なら、その衝突を返す。reviewerは新しい受け入れ条件を作らない。

mainは採用した修正だけをPLANへ反映し、影響範囲の再確認を経てGateを閉じる。計画だけの依頼では実装を開始しない。
