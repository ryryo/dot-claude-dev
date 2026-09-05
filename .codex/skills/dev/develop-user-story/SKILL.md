---
name: develop-user-story
description: ユーザーストーリーの追加・精緻化と、US IDを指定した計画・実装・レビュー・Journey検証を行う。台帳を製品契約の正本とし、Gateと開発状態を管理する。
---

# Develop User Story

適用先のストーリー台帳から、利用者成果、実装、検証の契約を組み立てる。依頼された操作と、その完了に必要なGateまで進める。

## 正本と対象を解決する

repository root、適用されるAGENTS.md、既存差分を確認する。台帳は利用者が指定したpathを優先し、指定がなければ対象PLANと同階層、その祖先、repository rootの`docs/USER_STORIES.md`の順に探す。複数候補が残る場合だけ確認する。

解決した台帳の対象US、全体ルール、状態、受け入れ条件を読み、今回の判断に必要な同scopeのPLAN、EVIDENCE、実装、テストを確認する。コードから判明する事実は調べ、利用者成果やscopeを変える未確定事項だけを質問する。

台帳は製品契約、PLANは実装順と進捗、コードとテストは実装証拠、EVIDENCEは必要な実検証証拠の正本である。下位の都合で上位契約を弱めず、既存の他者差分を上書きしない。

追加・実装・検証で対象USが未指定なら、依頼と台帳の優先度から一件へ絞る。複数USを同じ実装scopeへ含めるのは、利用者成果として分離できない場合だけとする。残るscope全体の計画化では複数USを入力にしてよいが、USを結合せず条件IDで追跡する。

## 操作に応じて読む

| 操作 | 詳細と終了位置 |
| --- | --- |
| Storyの追加・意味変更 | [Story作成](references/story-authoring.md)。ストーリー独立レビューGateまで |
| PLANの作成・実行責務の意味変更 | [PLAN作成](references/plan-workflow.md)。PLAN独立レビューGateまで。再利用・複数PLANの資料は該当時だけ読む |
| PLANの実装・再開 | [実装](references/implementation.md)。担当する検証・Journey・handoff、または指定停止Gateまで |
| Story／PLAN／実装のレビュー | 対象資料の独立レビューGateと[review-gate](../review-gate/SKILL.md)。判定・指定先への送信まで |
| Journey・実サービス・release確認 | [Journey検証](references/journey-verification.md)。固定条件の判定と結果記録まで |
| 状態・証拠の記録だけ | [結果記録](references/journey-verification.md#状態と証拠を更新する)。既存結果を反映しvalidatorで確認 |

資料の後工程を読むだけで開始しない。意味変更には必要なGateを通すが、追加だけ・計画だけ・レビューだけの依頼から実装へ進まない。指定された送信やhandoffが停止Gateなら、成功を確認して終了し、待機し続けない。

## レビューへ渡す契約

観点選定、正本照合、全観点の探索、候補分類、GO／NO-GO、増分再確認はreview-gateを正本とする。本skillはGate固有の質問、一次情報、役割分離、条件IDと開発状態を担当する。

Review Briefより先に、依頼・台帳・PLAN・Gate質問からReview Inputを固定する。`condition_ids`は次で決め、Briefや実装から逆算しない。

1. 依頼から対象Story／Gate／plan setを決め、解決した台帳から対象条件IDを直接抽出する。
2. PLAN対象では担当IDも別に抽出し、台帳へ照合する。candidateは担当ID、Story完了を所有する統合PLANは台帳の対象ID全件を使う。
3. Story Gateは台帳の対象ID、PLAN／実装Gateは照合済みの担当IDを過不足なく渡す。

現在契約、変更surface、全体不変条件、既存handoffも同じ一次情報から固定する。handoffは`id`、`gate`、`owner`、`contract`を持つ。review-gateが返す`later-gate`を、次の意味で開発へ引き継ぐ。

| 振り分け | 必要な前提 |
| --- | --- |
| `plan-input` | Storyが成立し、その成果の実装・検証方法をPLANで決める |
| `implementation-risk` | 固定PLANと名前付き実装Gate、owner、handoff契約がある |
| `journey-risk` | 実装契約が成立し、実画面・実サービス・目視品質・費用を伴う確認だけが残る |

現在適用される既存契約同士が衝突し、どちらを正とするか決めないとGateへ答えられない場合だけ`契約判断待ち`とする。名前付きhandoffを示せない将来用途や一般的な改善は`非適用`とし、曖昧な後続作業へ送らない。

## Gateの再開と状態

Storyのタイトル、きっかけ、活動、目的、scope、導線、受け入れ条件を意味的に変えたらストーリー独立レビューGate、PLANの実装・検証契約を変えたらPLAN独立レビューGateを再開する。実装成果・外部状態の意味変更も影響する実装Gateを再開する。コードだけでなく、テスト、設定、schema、依存、コンテンツ、prompt、静的・生成アセット、デプロイ済み設定を含む。

review-gateで再確認する観点を決め、影響したStory、PLAN、実装Gateを依存順に通す。その後、関係するJourneyだけを再実施する。影響しない観点・別Story・後続Gateを全面的にやり直さない。

状態、チェック欄、検証結果、証拠link、PLAN進捗、誤字・書式だけの更新はGateを失効させない。未確認を完了にする更新や、記録に見せかけた契約変更はこの例外に含めない。

| 状態 | 意味 |
| --- | --- |
| `todo` | 着手前 |
| `doing` | 実行中。未実装の条件が残る場合も維持する |
| `implemented` | コードと必要な自動検証が成立し、実装後独立レビューGateを通過した |
| `verified` | 全受け入れ条件を必要な検証水準で確認した |
| `blocked` | 外部条件により進められない。理由と未確認条件を示す |

影響Gateと必要なJourneyを通さず、`implemented`／`verified`へ進めない。結果の記入形式はJourney資料で管理する。

## 永続文書の書き方

日本語で、目的・判断・操作・例外・完了条件を分けて書く。一文へ詰め込まず、必要な列挙や対応は表・箇条書きにする。固有名詞、コード識別子、command、path、schema field、運用ラベル以外の不要な英単語を避け、同じ概念は同じ言葉で表す。

条件ID、Gate、責務、検証基準、停止条件、template／validatorの書式は保つ。Review Input、Brief、manifest、review履歴、case台帳、一時path、branch、commit SHA、worktree、session等の実行識別子を台帳・PLAN・EVIDENCEへ保存しない。
