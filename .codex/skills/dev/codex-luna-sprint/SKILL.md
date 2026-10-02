---
name: codex-luna-sprint
description: "指示元が独立したLunaチャットへ委譲する作業を、永続的な担当・依存・検収記録を持つSprintで進める。"
---

# Codex Luna Sprint

指示元が成果・契約・担当境界・統合を持ち、独立したGPT-6 Luna maxチャットが担当範囲の調査・局所設計・実装・検証を担う。通常の分担は[codex-task-split](../tasks/codex-task-split/SKILL.md)で会話内に記録し、永続的な担当・依存・検収管理が必要な場合だけ本スキルを使う。

## 正本と起動契約

委譲判断、利用者の許可、合意した起動方式・開始元でのチャット作成、報告・修正の往復は[codex-task-split](../tasks/codex-task-split/SKILL.md)を正本とする。実際の利用者による委譲開始指示・承諾済み計画から、その作業範囲の新規Lunaチャット作成と指示元との通信許可を引き継ぐ。スキル呼出しだけ・提案依頼を開始許可にしない。Lunaには[共通作業契約](../tasks/codex-task-split/references/worker-work-contract.md)を渡す。

既存Story／PLANがあれば契約と進捗の正本として参照し、本文を複製しない。Story／PLANの作成・意味変更が必要な場合だけ[develop-user-story](../develop-user-story/SKILL.md)を適用する。既存の独立Gateや適用先が要求する検証は維持する。同じ対象・契約・判定質問・証拠・必要な役割分離を満たすレビューは再利用し、Sprintのために同じGateを追加しない。

## 1. 担当記録を準備する

[codex-task-split](../tasks/codex-task-split/SKILL.md)の工程1で成果・担当境界・依存を決め、必要な記録を用意する。

projectの既存正本に担当・依存・検収・回収を記録できる場合は、それを使い、initializerや別Sprint台帳を作らない。既存正本のない案件で新規の永続記録が明示承認され、実在するscriptの内容と出力先を確認できた場合だけ、`scripts/init_sprint.sh --slug <slug> --workspace <workspace>`を実行する。生成するのは`tasks.md`、`review.md`、`sprint-env.sh`と、必要時に使う`prompts/`・`reviews/`である。

- `tasks.md`は[担当記録](../tasks/codex-task-split/references/task-contract.md#担当記録)として、原依頼・正本への参照、指示元、担当境界・依存、Lunaチャット、依頼回・状態、検収への参照を持つ。目的・受入条件・既知の事実を既存資料や起動メッセージから二重転記しない。
- 全taskを指示元所有で登録する工程や、記録を埋めるための詳細設計を追加しない。委任しない作業まで起動雛形を作らない。

### 既存Sprintを使う場合

既存ディレクトリにinitializerを再実行しない。`product-frame.md`、`implementation-plan.md`、段階reviewが残っていれば、有効な合意・正本への参照として利用する。合意済み契約は維持し、不要な全文再作成や形式だけの移行は行わない。

旧記録の`worker_done`は検収待ちとして読む。完了済みtaskは書き換えず、次に委譲する作業からチャットID・依頼回と新契約を記録する。古いpromptをそのまま送らず、変更する担当責務が既存の承認済みPLANと衝突する場合は、適用されるGateで調整する。

## 2. 委任・検収の工程を進める

実行手順は[codex-task-split](../tasks/codex-task-split/SKILL.md)の工程2〜5を使う。本資料は記録方法だけを補う。

既存正本がある場合は、起動文はchatと既存refから参照してよく、prompts等の複製は不要。専用Sprintを使う場合、実際に委譲するtaskだけ、[起動メッセージ](../tasks/codex-task-split/references/task-contract.md#起動メッセージ)を`prompts/<作業ID>.md`へ保存して渡す。担当記録にある境界・依存はその箇所への参照で渡せる。Lunaが読むのは作業の正本と必要な文脈であり、Sprint資料一式を毎回転記しない。

チャットの正式ID・host、起動結果、依頼回、報告状態を既存の担当記録へ反映する。`review_ready`は指示元による検収待ちであり、製品全体・上位Gateの完了ではない。報告後は[検収契約](../tasks/codex-task-split/references/main-review.md)で採否と修正・引き取りを判断し、結果を記録する。

## 3. 統合・完了を記録する

検収結果と必要な統合・利用動作の確認を記録し、正本の進捗だけを更新する。各taskの終了だけで全体を完了にしない。チャットは自動archiveせず、元の作業範囲が終わったら終了する。

成果と検収結果、Lunaチャットへのリンク、修正・残リスクを短く報告する。初回の実作業では、指示元の事前設計量、差し戻し、レビュー・手直し量も記録する。取得できないモデル別使用量や削減率を推定しない。

待機前・再開時のcompleted回収、成果版による重複処理防止、未commitの正式化は共通の[回収・再開契約](../tasks/codex-task-split/references/main-review.md#1-回収と再開)を使う。Sprint独自の常設監視・再開規則・会計台帳は増やさない。
