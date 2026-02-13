# team-opencode-plan / team-opencode-exec 改善提案

> 作成日: 2026-02-13
> 対象スキル: `dev:team-opencode-plan`, `dev:team-opencode-exec`
> 参考資料:
> - [Claude Code Agent Teams 公式ドキュメント](https://code.claude.com/docs/en/agent-teams)
> - [Agent Teams を使ってわかったチーム設計の勘所と自動化の限界](https://zenn.dev/sc30gsw/articles/4eee68a83454a2)
> - [sc30gsw/claude-code-customes team-builder](https://github.com/sc30gsw/claude-code-customes/tree/main/.claude/skills/team-builder)

---

## 現状の課題分析

現行の `team-opencode-plan` / `team-opencode-exec` スキルを上記の参考資料と照らし合わせて分析した結果、以下の構造的課題を特定した。

### 課題 1: opencode への全面依存による3層トークンコスト

現行設計では、すべてのタスクが `CC(haiku) → opencode run → 外部モデル` という3層構造で実行される。Zenn記事の著者が指摘する通り、Teammate 内で Subagent を使うパターンと本質的に同じ問題を抱えている:

- トークンコスト3層化（Lead + CC haiku + opencode外部モデル）
- Teammate間の直接メッセージングのメリットが薄れる（opencode経由のため応答が遅い）
- opencode の障害がすべてのタスクに波及する Single Point of Failure

### 課題 2: Agent Teams の機能を活かしきれていない

公式ドキュメントが強調する Agent Teams の強み（Teammate間直接メッセージ、自己クレーム、プラン承認）が活用されていない:

- **Teammate間通信**: 現行は Wave 完了 → 次 Wave の一方通行。Teammate 同士が知見を共有・議論する仕組みがない
- **自己クレーム**: タスクは Leader が明示的に割り当て。自律的なタスク取得がない
- **プラン承認**: Teammate がいきなり実装に入る。計画→承認→実装のゲートがない

### 課題 3: 固定的な Wave 構造

全タスクが厳密な Wave 順序に縛られ、依存関係のないタスクでも前 Wave の完了を待つ必要がある。これは並列実行の効果を減殺する。

### 課題 4: モデル戦略の欠如

全エージェントが `haiku + 同一 OC_MODEL` 固定。ロールの複雑度に応じたモデル選択ができない。

### 課題 5: テンプレートの不在

毎回ゼロからチーム構成を設計する必要がある。よくあるパターン（feature-dev、refactor、investigation 等）の再利用ができない。

---

## 改善提案一覧

| # | 提案名 | インパクト | 実装難度 |
|---|--------|-----------|----------|
| 1 | [Hybrid 実行モード](#提案-1-hybrid-実行モードopencode-任意化) | 高 | 高 |
| 2 | [Adaptive モデル戦略](#提案-2-adaptive-モデル戦略) | 中〜高 | 中 |
| 3 | [Teammate 間コミュニケーション](#提案-3-teammate-間コミュニケーションの活用) | 中 | 中 |
| 4 | [テンプレートベースのチーム構成](#提案-4-テンプレートベースのチーム構成) | 中 | 低 |
| 5 | [依存グラフベースのタスク実行](#提案-5-依存グラフベースのタスク実行) | 中 | 高 |
| 6 | [Plan Approval ゲート](#提案-6-plan-approval-ゲート) | 中 | 低 |

---

## 提案 1: Hybrid 実行モード（opencode 任意化）

### 概要

現行の「全タスク opencode 経由」を見直し、3つの実行モードから選択可能にする。

```
実行モード選択
├── native   : CC Teammate が直接実装（opencode 不使用）
├── opencode : 現行通り opencode run 経由（外部モデル活用）
└── hybrid   : タスクごとに native / opencode を自動判定
```

### hybrid モードの判定基準

| 条件 | 実行方式 | 理由 |
|------|---------|------|
| コードベース探索・分析が主目的 | native | CC は Glob/Grep/Read で十分。opencode のオーバーヘッド不要 |
| 設定ファイル変更・軽量タスク | native | haiku/sonnet で十分な単純作業 |
| 複雑なロジック実装 | opencode | 外部の強力なモデル（codex等）の推論力が必要 |
| レビュー・テスト分析 | native | 読み取り専用タスクに opencode は過剰 |

### task-list.json のスキーマ変更

```json
{
  "id": "task-1-1",
  "name": "CSS変数定義",
  "role": "designer",
  "executionMode": "native",
  "opencodePrompt": "...",
  "nativePrompt": "...",
  ...
}
```

- `executionMode`: `"native"` | `"opencode"` | `"auto"`（hybrid モード時に自動判定）
- `nativePrompt`: native モード時の Teammate 用プロンプト（opencode 非経由）
- `opencodePrompt`: opencode モード時のプロンプト（既存）

### メリット

- **コスト削減**: native モードのタスクは2層（Lead + Teammate）で済む。3層コストを回避
- **レイテンシ改善**: opencode run の起動・応答待ちがなくなる
- **耐障害性向上**: opencode 障害時も native タスクは継続可能
- **Agent Teams の本領発揮**: Teammate が直接 Claude Code セッションとして動くため、Teammate 間メッセージング、自己クレーム等のネイティブ機能が活用可能

### デメリット

- **スキーマの複雑化**: `executionMode`, `nativePrompt` の追加でタスク定義が肥大化
- **判定ロジックの設計負荷**: hybrid モードの auto 判定が不正確だと逆効果
- **品質の不均一性**: native（haiku/sonnet）と opencode（codex等）で実装品質に差が出る可能性
- **既存計画との互換性**: 既存の task-list.json に `executionMode` がないため移行が必要
- **プロンプトの二重管理**: `opencodePrompt` と `nativePrompt` を両方メンテナンスする負荷

### 採用判断の観点

Zenn記事の知見「自動化そのものより設計パターンの体系化が価値」を踏まえると、hybrid モードの auto 判定に凝るよりも、**タスク設計時にユーザーが明示的に選択する方が実用的**。plan フェーズで `executionMode` を決定し、exec フェーズはそれに従うだけにするのが安全。

---

## 提案 2: Adaptive モデル戦略

### 概要

team-builder の4段階モデル戦略を参考に、ロールの複雑度に応じたモデル選択を導入する。

```
モデル戦略選択（AskUserQuestion）
├── deep     : 全 Teammate = opus      （最高品質）
├── adaptive : Lead/Architect = opus, Worker = sonnet（推奨）
├── fast     : 全 Teammate = sonnet    （速度重視）
└── budget   : 全 Teammate = haiku     （コスト最小、現行相当）
```

### ロール別モデルマッピング

| ロール | deep | adaptive | fast | budget |
|--------|------|----------|------|--------|
| architect | opus | opus | sonnet | sonnet |
| reviewer | opus | opus | sonnet | haiku |
| frontend-developer | opus | sonnet | sonnet | haiku |
| backend-developer | opus | sonnet | sonnet | haiku |
| tdd-developer | opus | sonnet | sonnet | haiku |
| designer | opus | sonnet | sonnet | haiku |
| tester | opus | sonnet | sonnet | haiku |
| researcher | opus | opus | sonnet | haiku |

### opencode との組み合わせ

モデル戦略は CC Teammate のモデル選択に適用される。opencode 実行時の `$OC_MODEL` は別途選択（現行通り）。提案 1 の hybrid モードと組み合わせると:

- **native タスク**: CC Teammate のモデルがそのまま適用される（adaptive なら sonnet）
- **opencode タスク**: CC Teammate は haiku（コスト最小）、実装は opencode の `$OC_MODEL` に委譲

### task-list.json への反映

```json
{
  "metadata": {
    "modelStrategy": "adaptive",
    "ocModel": "openai/gpt-5.3-codex"
  }
}
```

### メリット

- **コスト・品質の最適化**: ロールの重要度に応じたリソース配分
- **再現可能**: 戦略名を選ぶだけで一貫したモデル配置が得られる
- **Zenn記事で「中〜高」評価**: モデル戦略の体系化は実証済みの高効果パターン

### デメリット

- **選択の負荷**: ユーザーが最適な戦略を判断する必要がある
- **opencode 併用時の複雑さ**: CC モデルと opencode モデルの2軸選択になる
- **opus のコスト**: deep/adaptive 戦略は大幅なコスト増（特に Teammate 数が多い場合）
- **効果の不確実性**: haiku でも opencode に委譲すれば結果は同じ、という反論がある

### 採用判断の観点

提案 1 の hybrid モードなしでは効果が限定的。opencode にすべて委譲する現行設計では、CC Teammate のモデルは「opencode run コマンドを実行するだけ」なので haiku で十分という論理が成立する。**提案 1 とセットで採用するのが前提**。

---

## 提案 3: Teammate 間コミュニケーションの活用

### 概要

Agent Teams 最大の差別化要素である「Teammate 間の直接メッセージング」を活用し、以下のパターンを導入する。

### パターン A: 実装 → レビューの直接フィードバック

```
現行:
  Wave 1 (実装) → Wave 完了 → Wave 2 (レビュー) → Lead に報告 → Lead がユーザーに提示

改善:
  Wave 1 (実装) + Wave 2 (レビュー) を同一 Wave で実行
  実装者が完了 → SendMessage でレビュワーに通知
  レビュワーが確認 → SendMessage で実装者にフィードバック
  実装者が修正 → 再通知
  レビュワーが LGTM → Lead に報告
```

### パターン B: 競合仮説検証（調査タスク向け）

公式ドキュメントのベストプラクティスにある「competing hypotheses」パターン:

```
3人の調査エージェントが同時に異なる仮説を調査
→ 互いの発見を SendMessage で共有
→ 他者の仮説を反証しようとする
→ 生き残った仮説が最も信頼性が高い
```

### パターン C: コンテキスト共有（needsPriorContext の代替）

```
現行:
  needsPriorContext: true → git diff で前タスクの変更を確認

改善:
  前タスクの Teammate が完了時に SendMessage で要点を次タスクの Teammate に直接送信
  → git diff よりも意図・設計判断が伝わる
```

### agent-prompt-template.md への追加

```markdown
## Teammate Communication Protocol

### 実装完了時の通知（実装系ロール）
タスク完了後、以下の情報を reviewer ロールの Teammate に SendMessage:
- 変更したファイルの一覧
- 設計判断の要約（なぜその実装にしたか）
- 注意すべき点

### レビュー結果の通知（レビュー系ロール）
レビュー完了後、以下の情報を該当する実装者に SendMessage:
- 改善候補（重要度付き）
- 具体的な修正提案
```

### メリット

- **Agent Teams の本領発揮**: Subagent にはない最大の差別化要素を活用
- **フィードバック高速化**: Lead を経由せず直接やり取りで修正サイクルが短縮
- **コンテキスト品質向上**: git diff よりも意図が伝わる構造化メッセージ
- **公式推奨パターンに準拠**: competing hypotheses、直接メッセージングは公式ベストプラクティス

### デメリット

- **メッセージングコスト**: 各メッセージが Teammate のコンテキストを消費
- **制御の難しさ**: Teammate 間のやり取りが Lead の把握を超える可能性
- **デバッグ困難**: Teammate 間の直接通信は Lead から見えにくい
- **opencode 併用時の制約**: opencode run 中は Teammate が応答できないため、メッセージングのタイミング制御が必要
- **設計の複雑化**: 誰がいつ誰にメッセージを送るかのプロトコル設計が必要

### 採用判断の観点

パターン A（実装→レビュー直接フィードバック）は最も実用的。パターン B は調査タスク限定で効果的。パターン C は opencode 経由の場合は git diff の方が確実（Teammate が opencode 実行中は SendMessage を受け取れない）。**段階的に A から導入し、効果を見て B, C を検討**するのが安全。

---

## 提案 4: テンプレートベースのチーム構成

### 概要

team-builder の8テンプレートを参考に、よくあるチーム構成をテンプレート化し、plan フェーズの効率を上げる。

### テンプレート定義

```
references/team-templates/
├── feature-dev.json       # 機能開発（designer + developer + reviewer）
├── refactor.json          # リファクタリング（architect + developer + tester）
├── investigation.json     # 調査・バグ調査（researcher x3 競合仮説）
├── frontend-only.json     # フロントエンド（designer + frontend-dev + reviewer）
├── fullstack.json         # フルスタック（backend + frontend + tester + reviewer）
├── tdd-focused.json       # TDD重視（tdd-developer + reviewer）
└── security-review.json   # セキュリティ審査（reviewer x2 + tester）
```

### テンプレート例: feature-dev.json

```json
{
  "name": "feature-dev",
  "description": "標準的な機能開発（設計→実装→レビュー）",
  "waves": [
    {
      "id": 1,
      "roles": ["designer"],
      "purpose": "UI/UX設計、デザイントークン定義"
    },
    {
      "id": 2,
      "roles": ["frontend-developer", "backend-developer"],
      "purpose": "並列実装",
      "blockedBy": [1]
    },
    {
      "id": 3,
      "roles": ["reviewer"],
      "purpose": "品質レビュー",
      "blockedBy": [2]
    }
  ],
  "modelStrategy": "adaptive",
  "fileOwnership": {
    "designer": ["src/styles/**", "src/design/**"],
    "frontend-developer": ["src/components/**", "src/pages/**"],
    "backend-developer": ["src/api/**", "src/services/**"],
    "reviewer": []
  }
}
```

### plan フェーズでの利用フロー

```
0-0: ワークスペース初期化
0-1: テンプレート選択（AskUserQuestion）
     ├── feature-dev（推奨）
     ├── refactor
     ├── investigation
     ├── カスタム（従来通り opencode でゼロから設計）
0-2: ストーリー分析（テンプレートのロール構成をヒントとして渡す）
0-3: タスク分解（テンプレートの Wave 構造をベースに詳細化）
0-4: レビュー
```

### メリット

- **計画フェーズの高速化**: ゼロからチーム構成を考える必要がない
- **ベストプラクティスの自動適用**: ファイル所有権、Wave 依存関係が事前設計済み
- **再現性**: 同じテンプレートを使えば一貫した品質のチーム構成
- **Zenn記事の知見に合致**: 「テンプレートによるベストプラクティスのパッケージ化」は「中」評価だが、適用漏れ防止に有効

### デメリット

- **柔軟性の低下**: テンプレートに当てはまらないタスクでは逆に制約になる
- **メンテナンスコスト**: テンプレートの更新・追加が必要
- **過度な標準化**: プロジェクトごとの特性を無視する可能性
- **Zenn記事の指摘**: 「Claudeに直接言っても同等の構成を提案できる」ため、テンプレートの価値は「毎回の適用漏れ防止」に限定される

### 採用判断の観点

テンプレートは「ゼロからの設計」と「完全自動」の中間点として有用。**カスタムモードを必ず残し、テンプレートは「推奨デフォルト」として提供**するのが正しい位置づけ。テンプレートに固執するのではなく、opencode によるストーリー分析の「ヒント」として渡す設計が良い。

---

## 提案 5: 依存グラフベースのタスク実行

### 概要

現行の厳密な Wave 順序実行を、タスク間の依存グラフ（DAG）に基づく動的スケジューリングに置き換える。

### 現行 vs 改善

```
現行（Wave 式）:
  Wave 1: [A, B] → 全完了待ち → Wave 2: [C, D] → 全完了待ち → Wave 3: [E]

改善（DAG 式）:
  A ──→ C ──→ E
  B ──→ D ──↗

  A完了 → C開始（BやDの完了を待たない）
  B完了 → D開始（AやCの完了を待たない）
  C,D完了 → E開始
```

### task-list.json のスキーマ変更

```json
{
  "tasks": [
    { "id": "task-A", "dependsOn": [], ... },
    { "id": "task-B", "dependsOn": [], ... },
    { "id": "task-C", "dependsOn": ["task-A"], ... },
    { "id": "task-D", "dependsOn": ["task-B"], ... },
    { "id": "task-E", "dependsOn": ["task-C", "task-D"], ... }
  ]
}
```

Wave 構造を廃止し、フラットなタスク配列 + `dependsOn` に変更。

### 実行エンジンの変更

```
1. 全タスクをDAGとして読み込み
2. dependsOn が空のタスクを即座にスポーン
3. タスク完了時:
   a. 完了タスクに依存する未着手タスクを検索
   b. 依存がすべて解決済みのタスクをスポーン
4. 全タスク完了まで繰り返し
```

### メリット

- **並列度の最大化**: 依存関係のないタスクは即座に開始
- **待ち時間の削減**: Wave 全体の完了を待つ必要がない
- **柔軟性**: 任意の依存関係を表現可能
- **自己クレームとの親和性**: Agent Teams の自己クレーム機能と自然に統合

### デメリット

- **実装の複雑さ**: DAG のトポロジカルソート、循環依存検出、動的スケジューリングが必要
- **デバッグの困難さ**: 実行順序が動的に変わるため、問題発生時の再現が難しい
- **Wave 構造との互換性破壊**: 既存の task-list.json が使えなくなる
- **可読性の低下**: Wave 構造の方が人間にとって直感的（「フェーズ1→フェーズ2→フェーズ3」）
- **過剰最適化のリスク**: 多くの実際のタスクは Wave 式で十分。DAG が必要なほど複雑な依存関係は稀

### 採用判断の観点

理論的には優れているが、実際のユースケースでは Wave 構造で十分なことが多い。**Wave 構造を維持しつつ、Wave 内でのタスク間依存（`blockedBy`）を強化する方が実用的**。完全な DAG 化は YAGNI（You Ain't Gonna Need It）の可能性が高い。

---

## 提案 6: Plan Approval ゲート

### 概要

公式ドキュメントの「Require plan approval for teammates」機能を活用し、Teammate が実装前に計画を提出し、Lead が承認するゲートを設ける。

### 適用条件

すべてのタスクに適用すると遅くなるため、条件付きで適用:

| 条件 | Plan Approval |
|------|---------------|
| 複雑なロジック実装 | 必須 |
| 既存コードの大幅変更 | 必須 |
| 設定ファイル変更 | 不要 |
| レビュー・テスト | 不要 |
| 新規ファイル作成（単純） | 不要 |

### task-list.json への反映

```json
{
  "id": "task-2-1",
  "name": "認証ロジック実装",
  "role": "backend-developer",
  "requirePlanApproval": true,
  ...
}
```

### 実行フロー

```
1. Teammate スポーン（plan mode）
2. Teammate がタスクを分析し、実装計画を作成
3. Teammate → Lead に計画を SendMessage
4. Lead が検証:
   - ファイル所有権の違反がないか
   - 他タスクとの競合がないか
   - 技術的に妥当か
5. 承認 → Teammate が実装モードに移行
   拒否 → フィードバック付きで計画修正を要求
```

### メリット

- **手戻り削減**: 実装前に方向性を確認できる
- **ファイル競合防止**: 計画段階で他タスクとの重複を検出
- **品質向上**: 複雑なタスクでの「やり直し」コストを回避
- **公式機能の活用**: Agent Teams にネイティブで組み込まれた機能

### デメリット

- **実行速度の低下**: 承認待ちがボトルネックになる
- **Lead の負荷増大**: すべての計画をレビューする必要がある
- **過度な管理**: 単純なタスクにも適用すると官僚的
- **判定基準の曖昧さ**: どのタスクに plan approval を要求するかの基準が主観的

### 採用判断の観点

`requirePlanApproval` フラグを task-list.json に追加するだけの低コスト改善。**デフォルトは false にして、plan フェーズで複雑と判断されたタスクにのみ true を設定**する運用が適切。

---

## 総合評価と推奨ロードマップ

### Phase 1: 低コスト・高効果（即時適用可能）

| 提案 | 理由 |
|------|------|
| **提案 4: テンプレート** | 新規ファイル追加のみ。既存スキルへの変更不要 |
| **提案 6: Plan Approval** | task-list.json にフラグ追加のみ。既存フローへの影響最小 |

### Phase 2: 中程度の改修

| 提案 | 理由 |
|------|------|
| **提案 3: Teammate 間通信（パターン A のみ）** | agent-prompt-template.md の修正 + exec の Wave 構造微調整 |
| **提案 2: Adaptive モデル戦略** | モデル選択ロジックの追加。提案 1 と組み合わせると効果的 |

### Phase 3: 大規模改修（要検証）

| 提案 | 理由 |
|------|------|
| **提案 1: Hybrid 実行モード** | スキーマ変更 + 実行エンジンの大幅改修。効果は高いがリスクも高い |

### 保留（現時点では不採用推奨）

| 提案 | 理由 |
|------|------|
| **提案 5: DAG 実行** | YAGNI。Wave 構造で十分なケースが大半 |

---

## 参考: Zenn記事の知見との対応表

| Zenn記事の知見 | 本提案での反映 |
|---------------|---------------|
| 「自動化そのものより設計パターンの体系化が価値」 | 提案 4（テンプレート）に反映。自動判定より明示的な選択を推奨 |
| 「ベストプラクティスの事前組み込みが最も効果的」 | 提案 4（テンプレート）+ 提案 6（Plan Approval）で適用漏れ防止 |
| 「モデル戦略の体系化は中〜高評価」 | 提案 2（Adaptive モデル戦略）として独立提案 |
| 「Teammate内Subagentは3層コスト」 | 提案 1（Hybrid モード）で opencode 依存を選択的に排除 |
| 「AUTO推薦はClaudeの自然言語理解で代替可能」 | テンプレートの AUTO 選択は不採用。明示的なテンプレート選択を推奨 |
| 「Skill Injectionはリマインダー程度」 | agent-prompt-template.md の改善に留め、過度な skill injection を避ける |
| 「並列調査・レビューが最も効果的」 | 提案 3（Teammate 間通信）でレビューフィードバックを強化 |
| 「同一ファイル編集は気づかない上書き」 | 提案 4（テンプレート）の fileOwnership で事前防止 |
