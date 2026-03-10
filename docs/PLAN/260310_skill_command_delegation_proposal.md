# スキル→コマンド委譲による構成最適化提案

## 注意書き
この計画に基づいて実行を進める際は、実装と並行して常にタスクリストのチェックを更新していくこと。

## 概要

既存スキル群（dev:epic, dev:story, dev:feedback, meta-skill-creator）が内部で独自に実装している「ヒアリング」「タスク分解」「深掘り」「CI修正」処理を、汎用コマンド（clarify, decomposition, dig, fix-ci）に委譲することで、プロンプトサイズ削減・実装精度向上・保守性改善を実現する。

## 背景

### 現状の課題

1. **重複実装**: 各スキルがヒアリング・分解・深掘りのロジックを独自に記述しており、質問の質やプロセスの深度にばらつきがある
2. **プロンプト肥大化**: 各スキルのSKILL.mdにヒアリングや分解のプロセス詳細が埋め込まれており、コンテキストウィンドウを圧迫している
3. **改善の分散**: clarifyコマンドの質問品質を改善しても、epicやstoryの内部ヒアリングロジックには波及しない
4. **専門性の希薄化**: 汎用コマンドは各責務に特化して設計されているのに対し、スキル内の実装は簡易版に留まりがち

### 汎用コマンドの強み

| コマンド | 行数 | 特化した機能 |
|----------|------|-------------|
| clarify.md | 123行 | 反復的ギャップ分析、9エリアの仕様チェックリスト、完全性チェック |
| decomposition.md | 185行 | コードベース探索→インタビュー→分解の3段階、具体的な検証ステップ付きTodo |
| dig.md | 233行 | 前提マッピング（6カテゴリ）、深さ優先の探索、完全性チェックリスト |
| fix-ci.md | 197行 | GitHub CLI統合、失敗タイプ分類、ループ修正、最終レポート |

---

## 提案一覧

### 重要度：高

#### 提案1: dev:story の Step 2（タスク分解）→ decomposition コマンドへの委譲

- **対象スキル**: dev:story（SKILL.md Step 2 + references/decompose-tasks.md）
- **委譲先コマンド**: decomposition（`.claude/commands/dev/decomposition.md`）
- **現状の問題**:
  - dev:story の Step 2 はコードベース探索→タスク分解→workflow分類を行うが、分解ロジックは `references/decompose-tasks.md`（138行）に記述されており、SKILL.md本体（102行）と合わせて240行相当のプロンプトを消費している
  - decomposition コマンドはコードベース探索（ステップ1）→不明点インタビュー（ステップ3）→詳細Todo作成（ステップ4-5）→レビュー（ステップ7）という、より成熟したプロセスを持っている
  - dev:story の分解は「分解して workflow を付与する」だけだが、decomposition は「各Todoが単独で実行可能な情報量を持つ」ことを保証する設計になっている
- **委譲内容**:
  - dev:story の Step 2 で decomposition コマンドを Task エージェントとして呼び出す
  - decomposition の出力（Todoリスト）を受け取り、dev:story 側で task-list.json のフォーマットに変換 + workflow フィールドを付与する
- **フロー変化**:
  - Before: `Step 1(分析) → Step 2(自前で分解 + workflow分類) → Step 3(レビュー) → Step 4(確認)`
  - After: `Step 1(分析) → Step 2a(decomposition委譲で分解) → Step 2b(workflow分類 + task-list.json変換) → Step 3(レビュー) → Step 4(確認)`
- **期待効果**:
  - **プロンプトサイズ**: references/decompose-tasks.md（138行）の大部分を削除可能。SKILL.md の Step 2 記述も約15行に簡素化。推定 **120行以上削減**
  - **精度向上**: decomposition の「各Todoが単独で実行可能」原則により、後続の dev:developing がより自律的に動作可能。不明点のインタビューステップ（ステップ3）が追加されることで、曖昧なタスクが減少
  - **保守性**: 分解ロジックの改善が全スキルに波及
- **リスクと軽減策**:
  - **リスク**: decomposition は汎用コマンドのため、dev:story 固有の `workflow` 分類や `task-list.json` のスキーマを知らない
  - **軽減策**: decomposition への入力に story-analysis.json のコンテキストを渡し、出力後に dev:story 側で workflow 分類と task-list.json フォーマット変換を行う。decomposition 自体は変更不要
  - **リスク**: decomposition が fork コンテキストで実行されるため、Task エージェント経由で呼び出す場合のコンテキスト伝達
  - **軽減策**: build-prompt.sh パターンで story-analysis.json + コードベース探索結果を追加コンテキストとして渡す
- **実装方法概要**:
  1. dev:story の SKILL.md Step 2 を書き換え: decomposition を Task 委譲で呼び出す記述に変更
  2. decomposition の出力を task-list.json に変換するロジック（workflow 分類含む）を SKILL.md の Step 2b として記述
  3. references/decompose-tasks.md は「decomposition コマンドへの追加コンテキスト仕様」に簡素化（task-list.json スキーマ定義 + workflow 分類ルールのみ残す）

---

#### 提案2: dev:epic の Step 1（要件ヒアリング）→ clarify + dig コマンドへの委譲

- **対象スキル**: dev:epic（SKILL.md Step 1 + Step 5 の一部）
- **委譲先コマンド**: clarify（`.claude/commands/dev/clarify.md`）+ dig（`.claude/commands/dev/dig.md`）
- **現状の問題**:
  - dev:epic の Step 1 はユーザーから要件を聞き取るが、ヒアリングプロセスは「要件が不明確な場合は AskUserQuestion で段階的にヒアリング」という1行の記述に留まっている。質問の網羅性・深度が実行者に依存する
  - clarify は9エリアの仕様チェックリスト（機能要件・非機能要件・技術的制約・UI/UX・エッジケース・統合ポイント・データモデル・セキュリティ・パフォーマンス）を持ち、反復的にギャップを埋める設計
  - dig は6カテゴリの前提マッピング（実現可能性・ユーザー・スコープ・依存関係・スケジュール・アーキテクチャ）を持ち、深さ優先で未知を発見する設計
  - epic のレビュー（Step 6）で指摘される問題の多くは、Step 1 のヒアリング不足に起因する
- **委譲内容**:
  - Step 1 を2段階に分割:
    - Step 1a: clarify コマンドで要件の明確化（スコープ・機能・非機能要件の確定）
    - Step 1b: dig コマンドで前提・リスクの深掘り（トレードオフ・障害モード・依存関係の確認）
  - 両コマンドの出力を統合して Step 4（構造計画）のインプットとする
- **フロー変化**:
  - Before: `Step 1(自前ヒアリング) → Step 2(slug) → Step 3(初期化) → Step 4(構造計画) → Step 5(詳細化) → Step 6(レビュー) → Step 7(確認)`
  - After: `Step 1a(clarify委譲) → Step 1b(dig委譲) → Step 2(slug) → Step 3(初期化) → Step 4(構造計画) → Step 5(詳細化) → Step 6(レビュー) → Step 7(確認)`
- **期待効果**:
  - **プロンプトサイズ**: SKILL.md の Step 1 記述（約10行）自体は小さいが、clarify/dig が担保する品質により Step 6 のレビューでの差し戻しが減少し、全体の実行効率が向上
  - **精度向上**: clarify の9エリアチェックリストと dig の6カテゴリ前提マッピングにより、要件の網羅性が大幅に向上。特に非機能要件・エッジケース・障害モードの見落としが減少
  - **保守性**: ヒアリング品質の改善が clarify/dig の1箇所の修正で全スキルに波及
- **リスクと軽減策**:
  - **リスク**: clarify + dig の2段階実行により、ユーザーへの質問量が増加し、ヒアリング疲れが生じる可能性
  - **軽減策**: dig は clarify の出力を入力として受け取り、既に明確化された項目はスキップする。また、小規模フィーチャーの場合は dig をオプショナルとする（AskUserQuestion で「深掘りを行いますか？」と確認）
  - **リスク**: epicのドメイン固有のコンテキスト（executionType分類、ストーリー粒度の基準）が clarify/dig に伝わらない
  - **軽減策**: clarify/dig への入力プロンプトに「フィーチャー計画のためのヒアリングである」旨と、出力に含めるべき情報（スコープ・動機・制約）を指定する
- **実装方法概要**:
  1. dev:epic の SKILL.md Step 1 を Step 1a（clarify 委譲）+ Step 1b（dig 委譲、オプショナル）に書き換え
  2. clarify/dig の出力を epic の後続ステップ（Step 4: 構造計画）のコンテキストとして渡すためのブリッジロジックを追加
  3. Step 1 の既存記述を「clarify の出力を確認し、追加のコードベース調査が必要なら Task（Explore）で補完する」に簡素化

---

### 重要度：中

#### 提案3: meta-skill-creator の Phase 0（collaborative ヒアリング）→ clarify + dig コマンドへの段階的移行

- **対象スキル**: meta-skill-creator（SKILL.md Part 0 + agents/interview-user.md）
- **委譲先コマンド**: clarify（`.claude/commands/dev/clarify.md`）+ dig（`.claude/commands/dev/dig.md`）
- **現状の問題**:
  - meta-skill-creator の collaborative モードは Phase 0-1〜0-6 の6段階ヒアリング（223行の interview-user.md + SKILL.md 本体の Phase 0 記述約25行）を持つ
  - このヒアリングは「スキル作成」に特化した質問パターン（ゴール・機能・外部連携・スクリプト・構成・優先事項）を持ち、clarify/dig の汎用パターンとは質問の切り口が異なる
  - ただし、本質的には clarify（要件の明確化）と dig（前提の深掘り）の組み合わせであり、共通化の余地がある
- **委譲内容**:
  - Phase 0-1〜0-3（ゴール特定・機能ヒアリング・外部連携ヒアリング）を clarify コマンドに委譲
  - Phase 0-4〜0-6（スクリプト・構成・優先事項）は meta-skill-creator 固有のドメイン知識が必要なため残す
  - dig による前提チェックは Phase 0-4（要件確認）の前にオプショナルで挿入
- **フロー変化**:
  - Before: `Phase 0-1(ゴール) → 0-2(機能) → 0-3(外部連携) → 0-4(スクリプト) → 0-5(構成) → 0-6(優先事項) → 0-7(要件確認)`
  - After: `clarify委譲(ゴール+機能+外部連携) → 0-4(スクリプト) → 0-5(構成) → 0-6(優先事項) → dig委譲(前提チェック、オプショナル) → 0-7(要件確認)`
- **期待効果**:
  - **プロンプトサイズ**: interview-user.md の Phase 0-1〜0-3 部分（約80行）を削除可能。SKILL.md 本体の collaborative セクションも簡素化。推定 **70〜80行削減**
  - **精度向上**: clarify の構造化されたギャップ分析により、スキル作成に必要な要件の網羅性が向上
  - **保守性**: ヒアリングプロセスの改善が波及
- **リスクと軽減策**:
  - **リスク（高）**: meta-skill-creator のヒアリングは「スキル」というドメインに深く特化しており、clarify の汎用的な質問パターンでは「スクリプトタイプの選択」「構成タイプの判定」「抽象度レベルの判定」といったドメイン固有の知識が活かせない
  - **軽減策**: clarify への入力プロンプトに「スキル作成のための要件ヒアリング」という文脈と、interview-result.json のスキーマ（期待する出力構造）を指定する。Phase 0-4 以降のドメイン固有部分は委譲しない
  - **リスク（中）**: 抽象度レベル判定（L1/L2/L3）が clarify の責務外
  - **軽減策**: 抽象度レベル判定は meta-skill-creator 側に残し、clarify の出力を受けてから判定する
- **実装方法概要**:
  1. agents/interview-user.md の Phase 0-1〜0-3 を clarify コマンドへの委譲記述に書き換え
  2. clarify の出力を interview-result.json のスキーマにマッピングするブリッジロジックを追加
  3. Phase 0-4 以降はそのまま残す
  4. dig のオプショナル挿入は Phase 2 で実装（Phase 1 で基本的な委譲を完了してから）

---

#### 提案4: dev:developing に fix-ci コマンドを統合（CI失敗時の自動修正パス追加）

- **対象スキル**: dev:developing（SKILL.md 全体）
- **委譲先コマンド**: fix-ci（`.claude/commands/dev/fix-ci.md`）
- **現状の問題**:
  - dev:developing は TDD/E2E/TASK の各ワークフローで品質チェック（CHECK: lint/format/build）を行うが、CI失敗時の対応フローがない
  - 現状、SPOT レビュー後にプッシュして CI が失敗した場合、ユーザーが手動で fix-ci コマンドを実行する必要がある
  - fix-ci コマンドは CI 失敗の自動診断・修正に特化した成熟したワークフローを持っている
- **委譲内容**:
  - dev:developing の Phase 3（計画ステータス更新）の後に「Phase 3.5: CI検証」を追加
  - PR が存在する場合、fix-ci コマンドを Task エージェントとして呼び出し、CI 全通過を確認
  - CI 失敗時は fix-ci が自動修正を試みる
- **フロー変化**:
  - Before: `Phase 2(タスク実行) → Phase 3(ステータス更新) → 完了`
  - After: `Phase 2(タスク実行) → Phase 3(ステータス更新) → Phase 3.5(fix-ci委譲、PR存在時のみ) → 完了`
- **期待効果**:
  - **精度向上**: CI 失敗による手戻りが自動解決され、ストーリー完了の信頼性が向上
  - **プロンプトサイズ**: 新規追加のため削減効果はないが、CI修正ロジックを dev:developing に内蔵する必要がなくなる（将来の肥大化防止）
  - **保守性**: CI 修正ロジックが fix-ci に集約
- **リスクと軽減策**:
  - **リスク**: fix-ci は PR ベースで動作するため、dev:developing の実行時点で PR が存在しない場合がある（dev:feedback で PR を作成する設計のため）
  - **軽減策**: Phase 3.5 は「PR が存在する場合のみ」実行する条件分岐を追加。PR 未作成の場合はスキップし、dev:feedback でのPR作成後に fix-ci を使用するフローを案内する
  - **リスク**: fix-ci の実行時間が長い（CI 待ち + 修正 + 再CI のループ）
  - **軽減策**: タイムアウトを設定し、1回の修正試行で解決しない場合はユーザーに報告して続行を確認する
- **実装方法概要**:
  1. dev:developing の SKILL.md に Phase 3.5（CI検証）を追加（約10行）
  2. fix-ci を Task エージェントとして呼び出す記述を追加
  3. PR 存在判定のロジック（`gh pr view` の結果確認）を追加

---

#### 提案5: dev:feedback の Step 1（品質ゲート）に dig コマンドの前提チェックを導入

- **対象スキル**: dev:feedback（SKILL.md Step 1 + Step 3）
- **委譲先コマンド**: dig（`.claude/commands/dev/dig.md`）
- **現状の問題**:
  - dev:feedback の Step 3 で「高リスク前提発見時のルール化・改善候補検討」を行っているが、前提の発見プロセスは体系化されていない
  - dig コマンドは6カテゴリの前提マッピングと深さ優先の探索プロセスを持ち、前提の発見に特化している
  - Step 1 の Critical issues 確認時の AskUserQuestion も、dig の探索的質問パターンを活用できる余地がある
- **委譲内容**:
  - Step 3 の「改善候補検討」フェーズで、dig コマンドの前提マッピング手法を参照する（完全委譲ではなく、dig の手法をStep 3の参照ガイドラインとして組み込む）
- **フロー変化**:
  - Before: `Step 1(レビュー) → Step 2(DESIGN.md更新) → Step 3(改善提案、独自ロジック)`
  - After: `Step 1(レビュー) → Step 2(DESIGN.md更新) → Step 3(改善提案、dig手法を参照した前提マッピング付き)`
- **期待効果**:
  - **精度向上**: dig の6カテゴリ前提マッピングにより、改善候補の網羅性が向上
  - **プロンプトサイズ**: 大きな削減はない（参照追加のため微増の可能性）
  - **保守性**: dig の前提マッピング手法が改善されれば feedback にも波及
- **リスクと軽減策**:
  - **リスク**: dev:feedback の Step 3 は「実装後の振り返り」であり、dig の「プラン前の探索」とはフェーズが異なる
  - **軽減策**: dig 全体を委譲するのではなく、前提マッピングの手法（6カテゴリ分類）のみを参照ガイドラインとして組み込む。dig の「質問→回答→フォローアップ」のインタラクティブ部分は使用しない
- **実装方法概要**:
  1. dev:feedback の references/propose-manage.md に dig の前提カテゴリ一覧を参照情報として追加
  2. SKILL.md の Step 3 に「dig の前提マッピング手法で改善候補を整理」という記述を1行追加

---

### 重要度：低

#### 提案6: dev:story の Step 1（ストーリー分析）→ clarify コマンドの部分適用

- **対象スキル**: dev:story（SKILL.md Step 1 + references/analyze-story.md）
- **委譲先コマンド**: clarify（`.claude/commands/dev/clarify.md`）
- **現状の問題**:
  - dev:story の Step 1 はストーリーの goal・scope・acceptanceCriteria を抽出するが、これは clarify の「機能要件の明確化」プロセスと重複する
  - ただし、analyze-story.md（76行）は簡潔かつ story-analysis.json の具体的なスキーマに特化しており、現状でも十分機能している
- **委譲内容**:
  - plan.json が存在しない場合（ストーリーを新規に聞き取る場合）に、clarify コマンドで要件を明確化した後に story-analysis.json を生成する
- **フロー変化**:
  - Before: `Step 1(自前で聞き取り + story-analysis.json生成)`
  - After: `Step 1a(clarify委譲で要件明確化) → Step 1b(clarify出力から story-analysis.json変換)`
- **期待効果**:
  - **プロンプトサイズ**: analyze-story.md（76行）の削減可能性があるが、story-analysis.json のスキーマ変換ロジックが必要になるため、実質的な削減は **30行程度**
  - **精度向上**: clarify の反復的ギャップ分析により、scope.excluded の見落としが減少する可能性があるが、改善幅は限定的
  - **保守性**: 一定の改善はあるが、analyze-story.md 自体が十分に小さく安定している
- **リスクと軽減策**:
  - **リスク**: clarify の汎用的な出力を story-analysis.json のスキーマに変換するオーバーヘッドが、削減効果を上回る可能性
  - **軽減策**: plan.json が存在する場合（dev:epic 連携時）は既にストーリー情報が構造化されているため、clarify 委譲は plan.json 非存在時のみに限定する
  - **リスク**: story-analysis.json の slugCandidates 生成は clarify の責務外
  - **軽減策**: slug 生成は引き続き agents/resolve-slug.md に委譲する（現状通り）
- **実装方法概要**:
  1. dev:story の SKILL.md Step 1 に clarify 委譲のオプショナルパスを追加（plan.json 非存在時のみ）
  2. clarify の出力を story-analysis.json に変換するマッピングロジックを追加
  3. analyze-story.md はスキーマ定義のリファレンスとして簡素化して残す

---

#### 提案7: dev:epic の Step 5（ストーリー詳細化）→ decomposition コマンドの手法参照

- **対象スキル**: dev:epic（SKILL.md Step 5）
- **委譲先コマンド**: decomposition（`.claude/commands/dev/decomposition.md`）
- **現状の問題**:
  - dev:epic の Step 5 は各ストーリーの技術詳細（acceptanceCriteria, affectedFiles, testImpact, technicalNotes 等）を埋めるが、これは decomposition の「コードベース探索→詳細化」プロセスと部分的に重複する
  - ただし、Step 5 の責務は「ストーリーレベルの技術詳細」であり、decomposition の「タスクレベルの分解」とは粒度が異なる
- **委譲内容**:
  - 直接委譲ではなく、decomposition のコードベース探索手法（ステップ1: プロジェクト構造・既存パターン・関連ファイル・依存関係の探索）を Step 5 の参照ガイドラインとして組み込む
- **フロー変化**:
  - Before/After の変化は最小限（参照ガイドラインの追加のみ）
- **期待効果**:
  - **精度向上**: decomposition の体系的な探索手法により、affectedFiles や testImpact の網羅性が向上する可能性
  - **プロンプトサイズ**: 変化なし（参照追加のため微増）
  - **保守性**: 限定的
- **リスクと軽減策**:
  - **リスク**: ほぼなし（参照追加のみのため）
  - **軽減策**: 不要
- **実装方法概要**:
  1. dev:epic の SKILL.md Step 5 に「decomposition のコードベース探索手法を参照」という注記を1行追加
  2. 必要であれば references/ に探索ガイドラインを追加

---

## 影響範囲

### 直接影響を受けるファイル

| ファイル | 影響の種類 | 関連提案 |
|----------|-----------|---------|
| `.claude/skills/dev/story/SKILL.md` | Step 2 書き換え + Step 1 オプショナルパス追加 | 提案1, 6 |
| `.claude/skills/dev/story/references/decompose-tasks.md` | 大幅簡素化（スキーマ定義のみ） | 提案1 |
| `.claude/skills/dev/story/references/analyze-story.md` | 簡素化（スキーマリファレンスのみ） | 提案6 |
| `.claude/skills/dev/epic/SKILL.md` | Step 1 書き換え + Step 5 参照追加 | 提案2, 7 |
| `.claude/skills/dev/meta-skill-creator/SKILL.md` | Part 0 collaborative セクション簡素化 | 提案3 |
| `.claude/skills/dev/meta-skill-creator/agents/interview-user.md` | Phase 0-1〜0-3 書き換え | 提案3 |
| `.claude/skills/dev/developing/SKILL.md` | Phase 3.5 追加 | 提案4 |
| `.claude/skills/dev/feedback/SKILL.md` | Step 3 に参照追加 | 提案5 |
| `.claude/skills/dev/feedback/references/propose-manage.md` | dig 前提カテゴリ参照追加 | 提案5 |

### 間接的に影響を受ける機能

- **dev:developing**: dev:story の task-list.json の品質向上により、タスク実行時の自律性が向上
- **dev:feedback**: dev:epic/story のヒアリング品質向上により、振り返り時に発見される「見落とし」が減少
- **全スキル**: clarify/decomposition/dig の改善が自動的に波及

---

## タスクリスト

### Phase 1: 高重要度の実装（提案1, 2）

- [ ] [TASK] dev:story の Step 2 を decomposition 委譲に書き換え（SKILL.md 編集）
- [ ] [TASK] references/decompose-tasks.md を簡素化（task-list.json スキーマ + workflow 分類ルールのみ残す）
- [ ] [TASK] 委譲フローの動作検証（サンプルストーリーで task-list.json 生成を確認）
- [ ] [TASK] dev:epic の Step 1 を Step 1a（clarify 委譲）+ Step 1b（dig 委譲、オプショナル）に書き換え
- [ ] [TASK] clarify/dig 出力を epic 後続ステップに渡すブリッジロジック追加
- [ ] [TASK] 委譲フローの動作検証（サンプルフィーチャーで PLAN.md 生成を確認）

### Phase 2: 中重要度の実装（提案3, 4, 5）

- [ ] [TASK] meta-skill-creator の agents/interview-user.md Phase 0-1〜0-3 を clarify 委譲に書き換え
- [ ] [TASK] SKILL.md Part 0 collaborative セクションの簡素化
- [ ] [TASK] clarify 出力→interview-result.json マッピングロジック追加
- [ ] [TASK] dev:developing の SKILL.md に Phase 3.5（CI検証 / fix-ci 委譲）を追加
- [ ] [TASK] dev:feedback の references/propose-manage.md に dig 前提カテゴリ参照を追加
- [ ] [TASK] dev:feedback の SKILL.md Step 3 に dig 手法参照の記述追加

### Phase 3: 低重要度の実装（提案6, 7）+ 全体検証

- [ ] [TASK] dev:story の Step 1 に clarify 委譲のオプショナルパス追加（plan.json 非存在時のみ）
- [ ] [TASK] dev:epic の Step 5 に decomposition 探索手法の参照注記追加
- [ ] [TASK] 全スキルの統合テスト（各ワークフローのエンドツーエンド実行確認）
- [ ] [TASK] CLAUDE.md のスキル説明を更新（委譲先コマンドの情報を反映）
