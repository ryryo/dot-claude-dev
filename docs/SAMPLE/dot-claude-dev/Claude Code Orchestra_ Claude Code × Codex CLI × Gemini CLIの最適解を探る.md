---
title: "Claude Code Orchestra: Claude Code × Codex CLI × Gemini CLIの最適解を探る"
source_url: "https://zenn.dev/mkj/articles/claude-code-orchestra_20260120"
source: Zenn
extracted_at: "2026-02-04T10:39:58.438Z"
word_count: 1601
content_length: 20296
---

## Claude Code Orchestra: Claude Code × Codex CLI × Gemini CLIの最適解を探る

こんにちは，松尾研究所の尾崎です．[25卒でデータサイエンティスト](https://zenn.dev/mkj/articles/123b0f2ca63bbc)をやっています．

最近はClaude CodeやCodex CLI，Gemini CLIといったCLIベースのAIコーディングアシスタントが急速に普及してきました．皆さんも日常的に使っている方が多いのではないでしょうか．

しかし，単一のツールだけでは対応しきれない場面が増えてきています．Claude Codeは最も利用されているであろうCLI Agentですが，複雑な設計判断はCodex CLIに劣るとの声もあります．一方でCodex CLIは深い推論が得意ですがレスポンスが重い．Gemini CLIは巨大なコンテキストとリサーチ能力に優れますが直接的なコード実装能力は前述の2つほどはないとの指摘も多いです．

本記事では，これら**3つのCLIエージェントを協調させる「オーケストレーション」テンプレート**を紹介します．Claude Codeをオーケストレーター（指揮者）として，Codex CLIとGemini CLIをそれぞれの得意分野で活用する開発環境です．この環境で快適に開発を進めるためのいくつかの工夫を共有しようと思います．

## 1\. なぜ複数のCLIエージェントを協調させるのか

### 各ツールの得意分野と限界

最新のCLIエージェントには，それぞれ得意分野と不得意な分野があるようです．明確に各社が強みを述べているわけではないですが，Xのエンジニアの皆さんの声を聴いていると，以下のように整理できると考えました．

| ツール | 得意なこと | 苦手なこと |
| --- | --- | --- |
| <strong>Claude Code</strong> | 高速な実装，コード編集，日常的な開発タスク | 複雑な設計判断，巨大なコンテキスト |
| <strong>Codex CLI</strong> | 深い推論，設計判断，デバッグ分析 | 高速なレスポンス |
| <strong>Gemini CLI</strong> | 巨大なコンテキスト，リサーチ，マルチモーダル | コーディング |

また単一ツールだけでは対応しにくい場面も増えてきています．

-   **Claude Codeだけ**: 複雑な設計判断で物足りなさを感じる，セカンドオピニオンが欲しい
-   **Codex CLIだけ**: 日常的な作業には重すぎる，レスポンスが遅い
-   **Gemini CLIだけ**: コーディングそのものがやや不安，実装作業には向かない

### 「別タブで開く」運用の問題点

「じゃあClaude CodeとCodex CLIを別々のタブで開いて使えばいいのでは？」と思うかもしれません．

![Claude CodeとCodex CLIを並べた開発環境](https://res.cloudinary.com/zenn/image/fetch/s--9nG0jLi_--/c_limit%2Cf_auto%2Cfl_progressive%2Cq_auto%2Cw_1200/https://storage.googleapis.com/zenn-user-upload/deployed-images/96c6d0cfe51cae6b741c89f9.png%3Fsha%3D803d82f13a5bd864fd6d8df243dd795d469e1e38)  
*別タブ運用：VSCodeでClaude Code（中央）とCodex CLI（右）を同時に開いた様子*

しかし，この運用には大きな問題がありまして．

| 問題 | 具体的な症状 |
| --- | --- |
| <strong>認知負担が大きい</strong> | 2つのタブを行き来し，それぞれの状態を把握する必要がある |
| <strong>コンテキストが分断される</strong> | Claude CodeはCodexに何を聞いたか知らない，Codexも逆を知らない |
| <strong>情報の橋渡しが手動</strong> | 「Codexがこう言ってた」と自分でコピペして伝える必要がある |
| <strong>判断の一貫性がない</strong> | お互いに相談しない部下2人を雇っているような状態 |

ので，実用上は結構厳しいのかなという印象です．Gemini CLI（VSCodeの拡張機能上はGoogle Code Assist）も併用となるとさらに大変ですね．

### マルチエージェントオーケストレーション

本テンプレートでは，\*\*Claude Codeをオーケストレーター（指揮者）\*\*として，CodexとGeminiを適材適所で活用するアーキテクチャを提案します．

**インターフェースはClaude Codeだけ．** ユーザーはClaude Codeとだけ対話し，必要に応じてClaude CodeがCodexやGeminiに相談します．

| 利点 | 具体的な効果 |
| --- | --- |
| <strong>認知負担が軽い</strong> | ユーザーはClaude Codeとだけ対話すればよい |
| <strong>コンテキストが統合される</strong> | Claude CodeがCodex/Geminiへの相談内容と結果を把握 |
| <strong>情報の橋渡しが自動</strong> | Claude Codeが必要な情報を適切に伝達・要約 |
| <strong>判断の一貫性がある</strong> | オーケストレーターが全体を統括し，矛盾のない意思決定 |

### 役割分担の詳細

| 役割 | エージェント | いつ使うか |
| --- | --- | --- |
| <strong>オーケストレーター</strong> | Claude Code | 常時：メインの開発作業，他エージェントへの委譲判断 |
| <strong>深い推論</strong> | Codex CLI | 設計判断，デバッグ，トレードオフ分析，コードレビュー |
| <strong>リサーチ</strong> | Gemini CLI | ライブラリ調査，リポジトリ全体分析，マルチモーダル処理 |
| <strong>並列実行</strong> | サブエージェント | 独立した小タスクの並列処理 |

このアプローチにより，**それぞれのツールの強みを活かした開発フロー**が実現できます．

## 2\. テンプレートの全体構造

![全体像](https://res.cloudinary.com/zenn/image/fetch/s--IdDTRBIe--/c_limit%2Cf_auto%2Cfl_progressive%2Cq_auto%2Cw_1200/https://storage.googleapis.com/zenn-user-upload/deployed-images/e30181073f8556492e52660a.png%3Fsha%3D37d82c32959dd5f21b53bcdddd7d600a48745c41)

### ディレクトリ構成

本テンプレートは以下のような構成になっています．

```
project/
├── CLAUDE.md                    # プロジェクトのメインドキュメント
├── pyproject.toml               # Pythonプロジェクト設定（uv, ruff, mypy, pytest）
│
├── .claude/                     # Claude Code (Orchestrator) の設定
│   ├── settings.json            # 権限設定 + Hooks定義
│   ├── agents/                  # サブエージェント定義
│   │   └── general-purpose.md   # 汎用サブエージェント（Codex/Gemini呼び出し可能）
│   ├── hooks/                   # 自動協調提案フック (Python)
│   │   ├── agent-router.py      # ユーザー入力からエージェント振り分け
│   │   ├── check-codex-before-write.py  # 編集前のCodex相談提案
│   │   ├── check-codex-after-plan.py    # 計画後のCodexレビュー提案
│   │   ├── suggest-gemini-research.py   # Web検索時のGemini提案
│   │   ├── post-implementation-review.py # 実装後のCodexレビュー提案
│   │   └── post-test-analysis.py        # テスト失敗時の分析提案
│   ├── rules/                   # 常時適用ルール（7ファイル）
│   │   ├── language.md          # 言語設定（英語で思考，日本語で応答）
│   │   ├── codex-delegation.md  # Codexへの委譲ルール
│   │   ├── gemini-delegation.md # Geminiへの委譲ルール
│   │   ├── coding-principles.md # シンプルさ，単一責任，早期リターン
│   │   ├── dev-environment.md   # uv, ruff, mypy, pytest の使用方法
│   │   ├── security.md          # 機密情報管理，入力検証
│   │   └── testing.md           # TDD, AAA パターン, カバレッジ 80%
│   ├── docs/                    # 知識ベース
│   │   ├── DESIGN.md            # 設計ドキュメント（自動更新）
│   │   ├── research/            # Geminiの調査結果
│   │   │   └── *.md             # トピック別リサーチファイル
│   │   └── libraries/           # ライブラリドキュメント
│   ├── logs/                    # ログディレクトリ
│   │   └── cli-tools.jsonl      # Codex/Gemini の入出力ログ
│   └── skills/                  # スキル定義（13スキル）
│       ├── startproject/        # マルチエージェント協調によるプロジェクト開始
│       ├── codex-system/        # Codex CLI連携の詳細
│       ├── gemini-system/       # Gemini CLI連携の詳細
│       ├── checkpointing/       # セッション永続化 & スキル抽出
│       ├── design-tracker/      # 設計記録スキル
│       ├── plan/                # 実装計画作成
│       ├── tdd/                 # テスト駆動開発
│       ├── simplify/            # コードリファクタリング
│       ├── init/                # プロジェクト初期化
│       ├── research-lib/        # ライブラリ調査（gemini-systemエイリアス）
│       ├── update-design/       # DESIGN.md更新
│       └── update-lib-docs/     # ライブラリドキュメント更新
│
├── .codex/                      # Codex CLI の設定
│   ├── AGENTS.md                # Codex用のコンテキスト
│   └── skills/
│       └── context-loader/      # .claude/のコンテキストを読み込む
│
└── .gemini/                     # Gemini CLI の設定
    ├── GEMINI.md                # Gemini用のコンテキスト
    ├── settings.json            # Gemini設定（gemini-3-pro-preview）
    └── skills/
        └── context-loader/      # .claude/のコンテキストを読み込む
```

### 設計のポイント

#### 1\. 知識ベースの一元管理

`.claude/docs/` に設計ドキュメント，リサーチ結果，ライブラリ情報を集約しています．Codex CLI と Gemini CLI の両方に `context-loader` スキルがあり，タスク開始時に `.claude/` のコンテキスト（ルール，設計決定，ライブラリ制約）を自動的に読み込みます．これにより，**どのツールを使っても同じ知識にアクセスできる**状態を維持できます．

![知識ベースのディレクトリ構造](https://res.cloudinary.com/zenn/image/fetch/s--JcR9i_UZ--/c_limit%2Cf_auto%2Cfl_progressive%2Cq_auto%2Cw_1200/https://storage.googleapis.com/zenn-user-upload/deployed-images/3649f34ea1544d2eb42ab5a5.png%3Fsha%3D7e1ba2db73c7283dada48199840ae204c4a5a32c)  
*`.claude/docs/libraries/` にライブラリドキュメントを集約*

#### 2\. Hooksによる自動協調提案

6つのPythonスクリプトが，ユーザーの入力やツール使用に応じて**自動的に適切なエージェントへの協調を提案**します．ユーザーが「Codexに聞いて」「Geminiで調べて」と明示的に指示する必要がありません．

#### 3\. 3つのCLIエージェントの協調

-   **Claude Code（`.claude/`）**: オーケストレーターとして全体を統括し，必要に応じて他のエージェントに委譲
-   **Codex CLI（`.codex/`）**: 深い推論が必要な設計判断，デバッグ，コードレビューを担当
-   **Gemini CLI（`.gemini/`）**: 大規模コンテキストが必要なリサーチ，リポジトリ分析，マルチモーダル処理を担当

#### 4\. 自動記憶

設計決定やライブラリの制約を自動的に記録する仕組みを組み込んでいます．Geminiの調査結果は `.claude/docs/research/` に保存され，後からClaude CodeやCodexが参照できます．

#### 5\. サブエージェントパターンによるコンテキスト管理

Claude Codeの実効コンテキストは約70-100kトークン（ツール定義で減少）です．本テンプレートでは，**サブエージェント（Task tool）を活用してコンテキストを保護**します．

```
Claude Code (Main Orchestrator)
├─ 実効コンテキスト: ~70-100k tokens
├─ 役割: ユーザーとの対話，タスク管理，実行
│
└─ サブエージェントに委譲:
    ├─ Codex CLI → 設計判断，デバッグ（重い出力はサブエージェントが吸収）
    └─ Gemini CLI → リサーチ，分析（1Mトークンの出力を要約して返却）
```

**サブエージェントを使う理由:**

-   **コンテキスト保護**: メインのオーケストレーターを軽量に保つ
-   **並列作業**: 複数のサブエージェントを同時実行可能
-   **出力フィルタリング**: 大きな出力を要約してから返却
-   **重い処理の分離**: Codexの詳細分析やGeminiの大規模リサーチを隔離

![Taskツールによる並列ライブラリ調査](https://res.cloudinary.com/zenn/image/fetch/s--ugT8qdWX--/c_limit%2Cf_auto%2Cfl_progressive%2Cq_auto%2Cw_1200/https://storage.googleapis.com/zenn-user-upload/deployed-images/5bfdc5a27eb4bc9daba2e4f8.png%3Fsha%3D92060027c6f074160511204fb562ad4226c85edd)  
*Claude CodeのTaskツールで複数のライブラリを並列に調査している様子*

## 3\. 参考にしたリソース

本テンプレートは，以下の2つのリソースから大きな影響を受けています．

### Anthropic公式: Claude Code Best Practices

Anthropicが公式に公開しているClaude Codeのベストプラクティスです．本テンプレートでは特に以下の考え方を取り入れています．

| 公式ベストプラクティス | 本テンプレートでの適用 |
| --- | --- |
| <strong>CLAUDE.md</strong> による文脈提供 | プロジェクト固有の情報をCLAUDE.mdに集約 |
| <strong>Explore-Plan-Code-Commit</strong> ワークフロー | <code>/plan</code>, <code>/tdd</code>, <code>/startproject</code> スキルで実現 |
| <strong>マルチClaude並列実行</strong> | Codex/Geminiをバックグラウンドで並列実行 |
| <strong>Course Correction</strong> | Hooksによる自動的な軌道修正提案 |

#### 公式ベストプラクティスの詳細

**1\. CLAUDE.mdファイルの作成**

> Claudeが自動的に読み込む`CLAUDE.md`ファイルに重要な情報を記載します．

記載すべき内容:

-   Bashコマンド，コアファイルの場所
-   コードスタイルガイドライン，テスト手順
-   リポジトリのエチケット，開発環境のセットアップ

本テンプレートでは，`CLAUDE.md` に加えて `.claude/rules/` で常時適用ルールを分離し，管理しやすくしています．

**2\. 探索→計画→コード→コミット ワークフロー**

> 複雑な問題では，早期の調査と計画が結果を大幅に改善します．

公式が推奨するワークフロー:

1.  コードを書かずに関連ファイルを読むようClaudeに依頼
2.  思考モードを使って計画を要求（"think", "think hard", "ultrathink"）
3.  Claudeに実装させる
4.  コミットとドキュメント更新を要求

本テンプレートの `/startproject` は，このワークフローを**Geminiのリサーチ**と**Codexのレビュー**で強化しています．

**3\. マルチClaude ワークフロー**

> 1つのClaudeインスタンスがコードを書き，別のインスタンスがレビューまたはテスト．コンテキストを分離することで，単一インスタンスのワークフローより良い結果が得られることがあります．

本テンプレートでは，この考え方を拡張し，**Claude + Codex + Gemini** の3エージェント協調を実現しています．

**4\. 戦略的な軌道修正**

> コーディング前に計画を依頼してアプローチを確認．Escapeを押すとどのフェーズでも中断可能．

本テンプレートの6つのHooksは，この軌道修正を**自動化**します．ユーザーが明示的に指示しなくても，適切なタイミングでCodexやGeminiへの相談を提案します．

### Everything Claude Code

Affaan Mustafa氏が公開しているClaude Codeの設定コレクションです．2025年9月のAnthropic × Forum Venturesハッカソン（NYC）優勝者で，10ヶ月以上の実践から得られた設定が詰まっています．

> Everything Claude Code の詳しい解説は [こちらの記事](https://zenn.dev/tmasuyama1114/articles/everything-claude-code-concepts) がわかりやすいです．

#### Everything Claude Codeの構成

| 構成要素 | 内容 |
| --- | --- |
| <strong>Agents</strong> | 9つの専門サブエージェント（planner, architect, code-reviewer, tdd-guide等） |
| <strong>Skills</strong> | 11のワークフロー定義（tdd-workflow, backend-patterns, verification-loop等） |
| <strong>Commands</strong> | 15のスラッシュコマンド（/tdd, /plan, /code-review, /e2e等） |
| <strong>Rules</strong> | 8つの常時適用ルール（security, coding-style, testing, git-workflow等） |
| <strong>Hooks</strong> | セッション管理，自動フォーマット，状態保存 |
| <strong>Contexts</strong> | 3つの動的プロンプト（dev, review, research） |

本テンプレートでは，特に以下の概念を採用しています．

| Everything Claude Code | 本テンプレートでの適用 |
| --- | --- |
| <strong>Hooks</strong> による自動化 | 6つのHooksでエージェント協調を自動提案 |
| <strong>Skills</strong> によるワークフロー定義 | <code>/startproject</code>, <code>/codex-system</code>, <code>/gemini-system</code> 等 |
| <strong>Rules</strong> による常時適用ルール | <code>coding-principles</code>, <code>security</code>, <code>testing</code> 等 |
| <strong>Agents</strong> によるサブエージェント | Codex/Geminiを外部エージェントとして活用 |

### 本テンプレートの独自性

Everything Claude Codeが**Claude Code単体の最適化**に焦点を当てているのに対し，本テンプレートはあくまでも**3つのCLIエージェントの協調**のアプローチの高度化を目指しています．

| 観点 | Everything Claude Code | 本テンプレート |
| --- | --- | --- |
| <strong>焦点</strong> | Claude Code単体の最大活用 | 3ツールのオーケストレーション |
| <strong>サブエージェント</strong> | 9つの内部エージェント | 内部 + 外部CLI（Codex, Gemini） |
| <strong>リサーチ</strong> | Claude Code + WebSearch | Gemini CLIに委譲（1Mトークン対応） |
| <strong>深い推論</strong> | Opus 4.5 モデル選択 | Codex CLI（gpt-5.2-codex）に委譲 |
| <strong>知識共有</strong> | Claude Code内で完結 | 3ツール間で共有 |
| <strong>マルチモーダル</strong> | 限定的 | Gemini CLIで pdf/動画/音声対応 |

#### コンテキスト管理の違い

**Everything Claude Code**は，Claude Code内部でのコンテキスト最適化に注力しています:

-   モデル選択（Haiku, Sonnet, Opus）による効率化
-   システムプロンプトのスリム化
-   MCPは10個以下，ツールは80個以下を推奨

**本テンプレート**は，外部CLIへの委譲でコンテキストを保護します:

-   重い分析はCodexサブエージェントに委譲
-   大規模リサーチはGemini（1Mトークン）に委譲
-   メインのClaudeは軽量なオーケストレーションに集中

### MCPベースアプローチとの比較

複数のCLIエージェントを協調させるアプローチとして，MCPを使った方法も注目されています．

-   [Claude Code+Codex CLI+Gemini CLIのMCPマルチエージェント構成](https://dev.classmethod.jp/articles/claude-code-codex-gemini-mcp/)
-   [Claude CodeにCodex CLIとGemini CLIを仕込んでレビューを強化する](https://toranoana-lab.hatenablog.com/entry/2025/12/08/120000)
-   [Claude Codeの仲間にCodex CLIとGemini CLIを追加する](https://qiita.com/hiropon122/items/c130168ca3fc0f1f6aaa)

これらの記事では，MCPサーバー経由でCodex CLIやGemini CLIをClaude Codeのツールとして追加しています．

```
# MCPベースのセットアップ例
claude mcp add -s user codex -- codex mcp-server
claude mcp add -s user gemini-cli -- npx mcp-gemini-cli
```

しかし，MCPベースのアプローチには課題も報告されています．Qiitaの記事では以下のように述べられています．

> 最初はMCPサーバで実現してみたのですが、ハングしたり回答が遅かったりと不安定だったところに、Agent Skillが登場したのでAgent Skillで実装してみたところ安定して動くようになりました。  
> — [Claude Codeの仲間にCodex CLIとGemini CLIを追加する](https://qiita.com/hiropon122/items/c130168ca3fc0f1f6aaa)

本テンプレートは，MCPではなく**Skillsベース**のアプローチを採用しています．以下にその違いと優位性を整理します．

#### MCPベース vs Skillsベース

| 観点 | MCPベース | Skillsベース（本テンプレート） |
| --- | --- | --- |
| <strong>安定性</strong> | 「ハングしたり回答が遅かったりと不安定」との報告あり | 直接CLIを呼び出すため安定 |
| <strong>Gemini連携</strong> | サードパーティ製MCPサーバーに依存 | 公式CLIを直接使用 |
| <strong>協調のタイミング</strong> | ユーザーが明示的に呼び出す必要 | <strong>Hooksが自動的に提案</strong> |
| <strong>ワークフロー</strong> | 単発のツール呼び出し | <strong>複合フェーズを定義可能</strong> |
| <strong>並列実行</strong> | MCPサーバーの同時呼び出しは不安定 | <strong>バックグラウンドで安定した並列処理</strong> |
| <strong>コンテキスト共有</strong> | 各MCPは独立 | <strong>context-loaderで3CLI間で知識共有</strong> |
| <strong>出力制御</strong> | そのままメインコンテキストに流入 | <strong>サブエージェントで要約してから返却</strong> |

#### Skillsベースの優位性

**1\. Proactive（能動的）な協調提案**

MCPは「呼ばれるのを待つ」受動的なツールです．ユーザーが「Codexに聞いて」と明示的に指示する必要があります．

一方，Skillsベースでは**Hooksと組み合わせて自動的に協調を提案**できます．ユーザーが「認証機能を実装して」と言っただけで，Claude Codeが「これは設計判断が必要だ，Codexに相談しよう」と自律的に判断します．

**2\. ワークフローの抽象化**

MCPは単発のツール呼び出しに限定されます．本テンプレートの`/startproject`のような「調査→計画→レビュー→実行→記録→品質保証」という**6フェーズの複合ワークフローをカプセル化**することはできません．

Skillsは複数のステップを一つのコマンドにまとめ，再利用可能な形で定義できます．

**3\. コンテキスト保護**

MCPの出力はそのままメインコンテキストに流入します．Geminiが1Mトークン分の分析結果を返すと，Claude Codeのコンテキストが圧迫されます．

Skillsベースでは**サブエージェント（Task tool）経由で出力をフィルタリング/要約**してから返却できます．重い処理を隔離し，メインのオーケストレーターを軽量に保てます．

**4\. 依存関係の少なさ**

MCPベースでは，各AIのMCPサーバー実装に依存します．特にGemini CLI用のMCPサーバーは非公式のサードパーティ製であり，更新が止まるリスクがあります．

Skillsベースでは**各CLIの公式インターフェース**をそのまま使用するため，CLIがアップデートされても追従しやすいです．

## 4\. Hooksによる自動協調提案

本テンプレートの特徴的な機能の一つが，**Hooksによる自動協調提案**です．6つのPythonスクリプトが，ユーザーの入力やツール使用を監視し，適切なエージェントへの協調を自動的に提案します．

### 6つのHooks

| Hook | トリガー | 提案内容 |
| --- | --- | --- |
| <strong>agent-router</strong> | ユーザー入力時 | 入力内容から適切なエージェントを判定 |
| <strong>check-codex-before-write</strong> | ファイル編集前 | 複雑な変更前にCodex相談を提案 |
| <strong>check-codex-after-plan</strong> | Task完了後 | 計画作成後にCodexレビューを提案 |
| <strong>suggest-gemini-research</strong> | WebSearch/WebFetch前 | Web検索の代わりにGeminiリサーチを提案 |
| <strong>post-implementation-review</strong> | ファイル編集後 | 大きな実装後にCodexレビューを提案 |
| <strong>post-test-analysis</strong> | Bash実行後 | テスト失敗時にCodex分析を提案 |

### agent-routerの仕組み

ユーザーの入力を解析し，以下のようなキーワードを検出してエージェントを振り分けます．

**Codexへの振り分けトリガー:**

-   設計判断: 「設計」「アーキテクチャ」「どう実装」「design」「architecture」
-   デバッグ: 「なぜ動かない」「error」「bug」「debug」
-   比較分析: 「どちらがいい」「compare」「trade-off」「トレードオフ」
-   レビュー: 「リファクタ」「レビュー」「refactor」「review」

**Geminiへの振り分けトリガー:**

-   リサーチ: 「調べて」「リサーチ」「research」「investigate」
-   マルチモーダル: 「pdf」「動画」「video」「audio」「音声」
-   ドキュメント: 「ドキュメント」「library」「docs」「ライブラリ」

```
# agent-router.py の抜粋
def detect_agent(prompt: str) -> tuple[str | None, str]:
    prompt_lower = prompt.lower()

    # Check Codex triggers
    for trigger in CODEX_TRIGGERS:
        if trigger in prompt_lower:
            return "codex", trigger

    # Check Gemini triggers
    for trigger in GEMINI_TRIGGERS:
        if trigger in prompt_lower:
            return "gemini", trigger

    return None, ""
```

### Hooksの設定

`.claude/settings.json` でHooksを設定しています．

```
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/agent-router.py\"",
            "timeout": 5
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{ "type": "command", "command": "...check-codex-before-write.py" }]
      },
      {
        "matcher": "WebSearch|WebFetch",
        "hooks": [{ "type": "command", "command": "...suggest-gemini-research.py" }]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Task",
        "hooks": [{ "type": "command", "command": "...check-codex-after-plan.py" }]
      },
      {
        "matcher": "Bash",
        "hooks": [{ "type": "command", "command": "...post-test-analysis.py" }]
      },
      {
        "matcher": "Edit|Write",
        "hooks": [{ "type": "command", "command": "...post-implementation-review.py" }]
      }
    ]
  }
}
```

## 5\. Codex CLI との連携（codex-system スキル）

### Codex CLI の役割

Codex CLI（gpt-5.2-codex）は，**深い推論が必要なタスク**を担当します．

| タスク | Codexが得意な理由 |
| --- | --- |
| <strong>設計判断</strong> | 複数の選択肢を深く分析，トレードオフを整理 |
| <strong>デバッグ</strong> | 根本原因の特定，複雑なバグの分析 |
| <strong>コードレビュー</strong> | アーキテクチャの問題点，改善点の指摘 |
| <strong>リファクタリング</strong> | より良い設計への具体的な提案 |

### いつCodexに相談するか

**MUST（必ず相談）:**

| 場面 | 例 |
| --- | --- |
| <strong>設計判断の前</strong> | 「どう構造化すべき？」「どのアプローチが良い？」 |
| <strong>複雑な実装の前</strong> | 新機能設計，3+ファイルへの変更，API設計 |
| <strong>デバッグ時</strong> | 原因が明確でない，最初の修正が失敗した |
| <strong>計画時</strong> | 複数ステップのタスク，トレードオフの評価 |

**相談不要:**

-   単純なファイル編集（タイポ修正，小さな変更）
-   標準的な操作（git commit, テスト実行, lint）
-   解が自明な些細なコード変更

### Quick Rule

**「うーん，これどうしよう？」と思ったら → Codexに相談**

### 実行モードとバックグラウンド実行

Codexに相談する際，**常にバックグラウンドで実行**します．これにより，Codexが分析している間もClaude Codeは別の作業を並行して進められます．

**Analysis Only（分析のみ）:**

```
codex exec --model gpt-5.2-codex --sandbox read-only --full-auto "Analyze: {question}" 2>/dev/null
```

**Delegate Work（作業委譲）:**

```
codex exec --model gpt-5.2-codex --sandbox workspace-write --full-auto "Task: {description}" 2>/dev/null
```

### 言語プロトコル

1.  **Codexへは英語で質問** - 推論精度が向上
2.  **英語で回答を受け取る**
3.  **ユーザーには日本語で報告**

## 6\. Gemini CLI との連携（gemini-system スキル）

### なぜGeminiにリサーチを委譲するのか

Claude CodeでWebFetchを使ってリサーチすることも可能ですが，複数のドキュメントを調査する場合，以下のような問題が発生します．

![WebFetchを大量に実行している様子](https://res.cloudinary.com/zenn/image/fetch/s--CbwR1InD--/c_limit%2Cf_auto%2Cfl_progressive%2Cq_auto%2Cw_1200/https://storage.googleapis.com/zenn-user-upload/deployed-images/7fcba3dc2b46e26c34deb298.png%3Fsha%3D88b894c9466eca5de79fc8cc182b9665e97aa038)  
*Claude CodeでWebFetchを多用すると，コンテキストが圧迫される*

この例では，LangChain + Neo4jのドキュメントを調査するために8回以上のWebFetchが実行されています．これにより：

-   コンテキストが急速に消費される
-   応答が遅くなる
-   本来の実装作業に使えるコンテキストが減少

**Gemini CLI（1Mトークン）に委譲**することで，この問題を解決できます．Geminiが大量のドキュメントを処理し，要約だけをClaude Codeに返却します．

### Gemini CLI の役割

Gemini CLI（gemini-3-pro-preview）は，**リサーチと大規模コンテキスト処理**を担当します．

| タスク | Geminiが得意な理由 |
| --- | --- |
| <strong>リポジトリ全体分析</strong> | 1Mトークンのコンテキストで全体把握 |
| <strong>ライブラリ調査</strong> | Google検索グラウンディングで最新情報 |
| <strong>マルチモーダル</strong> | pdf，動画，音声の解析 |
| <strong>ドキュメント検索</strong> | 最新ドキュメントの検索と要約 |

### Gemini vs Codex の使い分け

| タスク | Gemini | Codex |
| --- | --- | --- |
| リポジトリ全体理解 | ✓ |   |
| ライブラリ調査 | ✓ |   |
| マルチモーダル（pdf/動画/音声） | ✓ |   |
| 最新ドキュメント検索 | ✓ |   |
| 設計判断 |   | ✓ |
| デバッグ |   | ✓ |
| コード実装 |   | ✓ |

### 実行コマンド

```
# リサーチ
gemini -p "Research: {topic}" 2>/dev/null

# コードベース分析
gemini -p "Analyze: {aspect}" --include-directories src,lib 2>/dev/null

# マルチモーダル（pdf/動画/音声）
gemini -p "Extract: {what}" < /path/to/file.pdf 2>/dev/null
```

### 調査結果の保存

Geminiの調査結果は `.claude/docs/research/{topic}.md` に保存されます．これにより，Claude CodeやCodexが後から参照できます．

## 7\. /startproject ワークフロー

`/startproject` は，本テンプレートの目玉機能です．**3つのエージェントが協調してプロジェクトを開始**するワークフローを提供します．

### ワークフロー概要（6フェーズ）

```
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1: Gemini CLI (Research) [Background]                    │
│  → リポジトリ分析・ライブラリ調査                                │
│  → Output: .claude/docs/research/{feature}.md                   │
├─────────────────────────────────────────────────────────────────┤
│  Phase 2: Claude Code (Requirements)                            │
│  → ユーザーから要件ヒアリング（目的，スコープ，制約，成功基準）  │
│  → 実装計画のドラフト作成                                        │
├─────────────────────────────────────────────────────────────────┤
│  Phase 3: Codex CLI (Design Review) [Background]                │
│  → Geminiのリサーチ + Claudeの計画を読み込み                     │
│  → 計画の深いレビュー・リスク分析・実装順序の提案                │
├─────────────────────────────────────────────────────────────────┤
│  Phase 4: Claude Code (Task Creation)                           │
│  → 全入力を統合                                                  │
│  → タスクリスト作成 (TodoWrite)                                  │
│  → ユーザー確認                                                  │
├─────────────────────────────────────────────────────────────────┤
│  Phase 5: Claude Code (Documentation)                           │
│  → CLAUDE.md にプロジェクトコンテキストを追記                    │
│  → .claude/docs/DESIGN.md に設計決定を記録                       │
├─────────────────────────────────────────────────────────────────┤
│  Phase 6: Multi-Session Review (Quality Assurance)              │
│  → 新しいClaudeセッションで客観的なコードレビュー                │
│  → または Codex に実装後レビューを委託                           │
│  → 実装バイアスを排除した品質保証                                │
└─────────────────────────────────────────────────────────────────┘
```

### 使用例

```
ユーザー: /startproject ユーザー認証機能を追加したい
```

**Phase 1: Gemini によるリサーチ（バックグラウンド）**

```
gemini -p "Analyze this repository for implementing: ユーザー認証機能

Provide comprehensive analysis:
1. Repository Structure
2. Relevant Existing Code
3. Library Investigation
4. Technical Considerations
5. Recommendations" --include-directories . 2>/dev/null
```

**Phase 2: Claude による要件ヒアリング**

Claude がユーザーに以下を確認:

1.  **目的**: 何を達成したいですか？
2.  **スコープ**: 含めるもの・除外するものは？
3.  **技術的要件**: 特定のライブラリ，パターン，制約は？
4.  **成功基準**: 完了の判断基準は何ですか？

**Phase 3: Codex によるレビュー（バックグラウンド）**

```
codex exec --model gpt-5.2-codex --sandbox read-only --full-auto "
Review this implementation plan for: ユーザー認証機能

## Gemini Research Summary
{Geminiの調査結果}

## Draft Plan
{Claudeの計画ドラフト}

Provide:
1. Plan Assessment
2. Risk Analysis
3. Implementation Order
4. Refinements
" 2>/dev/null
```

**Phase 4: タスクリスト作成**

Claudeがすべての入力を統合し，TodoWriteでタスクリストを作成．ユーザーに最終確認を求めます．

**Phase 5: ドキュメント更新**

-   `CLAUDE.md` にプロジェクトコンテキストを追記（次回セッションでも文脈を維持）
-   `.claude/docs/DESIGN.md` に設計決定を記録

**Phase 6: マルチセッションレビュー（品質保証）**

実装完了後，**新しいClaudeセッション**または**Codex**で客観的なコードレビューを実施します．

```
# 新しいセッションでレビュー
git diff main...HEAD | claude -p "Review this implementation..."

# または Codex に委託
codex exec --model gpt-5.2-codex --sandbox read-only --full-auto "Review implementation..." 2>/dev/null
```

### バックグラウンド実行による並列作業

## 8\. /checkpointing スキル（セッション永続化）

長時間の開発セッションでは，コンテキストの喪失や作業パターンの記録が課題になります．`/checkpointing` スキルはこれを解決します．

### 3つのモード

| モード | コマンド | 用途 |
| --- | --- | --- |
| <strong>Session History</strong> | <code>/checkpointing</code> | Codex/Geminiの相談ログをエージェント設定ファイルに追記 |
| <strong>Full Checkpoint</strong> | <code>/checkpointing --full</code> | gitコミット，ファイル変更，CLI相談を完全保存 |
| <strong>Skill Analysis</strong> | <code>/checkpointing --full --analyze</code> | 作業パターンを分析し，再利用可能なスキル候補を抽出 |

### Full Checkpointの出力

```
# Checkpoint: 2026-01-28 14:30:00

## Summary
- Commits: 5
- Files changed: 12
- CLI consultations: 3 (Codex: 2, Gemini: 1)

## Git Changes
[コミット一覧とdiff要約]

## CLI Consultations
[Codex/Geminiへの相談内容と回答要約]
```

### Skill Analysis（スキル抽出）

`--analyze` オプションを付けると，サブエージェントが作業パターンを分析し，再利用可能なスキル候補を提案します．

**抽出されるパターン例:**

-   TDDワークフロー（テスト作成 → 実装 → リファクタ）
-   リサーチ → 設計 → 実装のシーケンス
-   特定のライブラリ導入手順

## 9\. Rules（常時適用ルール）

Rulesは，常に従うべきルールを定義します．本テンプレートでは以下のルールを用意しています．

| ルール | 内容 |
| --- | --- |
| <strong>language</strong> | 思考は英語，ユーザーへの応答は日本語 |
| <strong>codex-delegation</strong> | Codexへの相談ルール |
| <strong>gemini-delegation</strong> | Geminiへの委譲ルール |
| <strong>coding-principles</strong> | シンプルさ，単一責任，早期リターン，型ヒント |
| <strong>dev-environment</strong> | uv，ruff，ty，marimo の使用方法 |
| <strong>security</strong> | 機密情報管理，入力検証，SQLi/XSS防止 |
| <strong>testing</strong> | TDD，AAA パターン，カバレッジ 80% |

本テンプレートでは全ファイルに適用するルールを採用していますが，Claude Codeのrulesは`paths`フロントマターで特定ファイルにのみ適用することも可能です．

```
---
paths:
  - "src/api/**/*.ts"
---

# API固有のルール
このルールはsrc/api/配下の.tsファイルにのみ適用されます．
```

プロジェクトの規模や要件に応じて，全体適用ルールとパス指定ルールを使い分けてください．

## 10\. 導入方法

### Prerequisites

3つのCLIツールをインストールしておく必要があります．

```
# Claude Code
npm install -g @anthropic-ai/claude-code
claude login

# Codex CLI
npm install -g @openai/codex
codex login

# Gemini CLI
npm install -g @google/gemini-cli
gemini login
```

### 既存プロジェクトへの適用（推奨）

既存プロジェクトのルートで以下を実行:

```
git clone --depth 1 https://github.com/DeL-TaiseiOzaki/claude-code-orchestra.git .starter \
  && cp -r .starter/.claude .starter/.codex .starter/.gemini .starter/CLAUDE.md . \
  && rm -rf .starter \
```

これにより，設定ファイルとスキル定義のみがコピーされます．

## 11\. まとめ

本記事では，Claude Code，Codex CLI，Gemini CLI の3つを協調させる「マルチエージェントオーケストレーション」テンプレートを紹介しました．

### ポイントの振り返り

1.  **3エージェントの役割分担**: Claude Code（オーケストレーター），Codex（深い推論），Gemini（リサーチ）
2.  **Hooksによる自動協調提案**: 6つのフックがエージェント協調を自動的に提案
3.  **`/startproject` ワークフロー**: 6フェーズ（調査 → 計画 → レビュー → 実行 → 記録 → 品質保証）
4.  **サブエージェントパターン**: コンテキストを保護しながら重い処理を外部CLIに委譲
5.  **`/checkpointing` スキル**: セッション永続化と作業パターンからのスキル抽出
6.  **マルチセッションレビュー**: 実装バイアスを排除した客観的な品質保証
7.  **知識ベースの一元管理**: `.claude/docs/` に設計，リサーチ結果，ライブラリ情報を集約

### 今後の展望

CLIエージェントの進化は速く，今後も新しい機能が追加されていくでしょう．このテンプレートも，それに合わせて進化させていきたいと思います．

何か質問やフィードバックがあれば，ぜひGitHubのIssueでお知らせください．

## 参考リンク

### 公式リソース

-   [Claude Code 公式ドキュメント](https://docs.anthropic.com/en/docs/claude-code)
-   [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices) - Anthropic公式ベストプラクティス
-   [OpenAI Codex CLI](https://github.com/openai/codex)
-   [Google Gemini CLI](https://github.com/google/gemini-cli)

### テンプレート・設定集

-   [claude-code-orchestra](https://github.com/DeL-TaiseiOzaki/claude-code-orchestra) - 本記事で紹介したテンプレート
-   [Everything Claude Code](https://github.com/affaan-m/everything-claude-code) - Anthropicハッカソン優勝者の設定集
-   [Everything Claude Code 解説記事](https://zenn.dev/tmasuyama1114/articles/everything-claude-code-concepts) - 日本語での詳細解説