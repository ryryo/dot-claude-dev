# GitHub Issues ハイブリッド統合設計

個人開発における spec/plan 管理システムと GitHub Issues の統合方針。

---

## 現状の構造

2層がローカルで完結している：

| 層 | ファイル | 役割 |
|---|---|---|
| 設計層 | spec.md | 人間可読な設計・背景・アーキテクチャ |
| 実行層 | tasks.json v2 | 構造化された進捗・ステップ・レビュー結果 |

`sync-spec-md.mjs` フックが PostToolUse で自動同期し、ダッシュボードが GitHub API 経由で複数リポジトリの tasks.json を横断表示する。

---

## 現在のシステムの弱点

### 最大の問題：「スレッド化」工程の欠如

現在のフロー：

```
アイデア → (長い /dev:spec 作業) → tasks.json + spec.md → (任意でIssue化)
```

`/dev:spec` は完成度の高い仕様書を要求する設計のため、軽い課題やアイデアを捉えたい場合でもフル spec 作成を経なければ管理対象にならない。結果として「気になってはいるが spec を書くほどでもない」タスクが漂流する。

**根本原因：** アイデアを即座にスレッドに変換するステップがない。

### Git/CI 観点の欠如

現在の git 関連の仕組み：
- `commit-check.sh`（Stop フック）：未コミット行数 100 超で警告
- worktree モード：feature/{slug} ブランチを自動切り替え

不足しているもの：
- spec-run の実行結果（PASSED/FAILED）と CI の連動
- PR 作成 → CI → Issue クローズ のパイプライン

---

## ハイブリッド設計方針

**原則：tasks.json が Source of Truth であることは崩さない。**  
GitHub Issues は「スレッド・インデックス・CI アンカー」として使う。

### 情報の分担

| 情報 | tasks.json | GitHub Issue |
|---|---|---|
| impl（実装手順） | ◎ | × |
| steps/review 結果 | ◎ | × |
| affectedFiles | ◎ | × |
| Gate 構造・依存関係 | ◎ | × |
| 進捗パーセント | ◎ | ラベルで近似 |
| アイデアのスレッド | × | ◎ |
| CI 連動・自動クローズ | × | ◎ |
| PR/commit リンク | △ | ◎ |

境界が明確なので二重管理にならない。

---

## フェーズ別実装方針

### フェーズ1：dev:thread（最優先）

軽量 Issue 作成スキル。spec なしで Issue だけを即座に作る：

```
アイデア → dev:thread → Issue 作成（2-3行で完結）→ 熟成 → /dev:spec で肉付け
```

Issue 作成に必要な最低情報：
- タイトル（1行）
- 背景（2-3行）
- ラベル（kind:feature / kind:bug / kind:debt）

これにより「spec を書く気になった Issue」だけが /dev:spec に進む。

### フェーズ2：Spec と Issue の紐付け

1 spec ディレクトリ = 1 GitHub Issue。`relatedIssues` フィールドは tasks.json にすでに存在する。

| tasks.json | GitHub Issue |
|---|---|
| title | Issue タイトル |
| summary | Issue 本文冒頭 |
| status | ラベル（status:in-progress 等） |
| spec.md への相対パス | Issue 本文にリンク |

`/dev:spec` の最終ステップで Issue 番号を tasks.json の `relatedIssues` に記録する。

### フェーズ3：PR 自動作成 + CI 連動

**前提：worktree モード使用時のみ適用。**

spec-run 完了後の理想フロー：

```
Gate N 完了（worktree モード）
    ↓
feature/{slug} ブランチに自動コミット
    ↓
PR 作成（gh pr create）
  - 本文に tasks.json のチェックリストを展開
  - 「Closes #{issue_number}」を自動挿入
    ↓
CI が発火
  - テスト通過 → PR に ✅
  - テスト失敗 → /dev:fix-ci を起動
    ↓
全 Gate 完了 → PR マージ → Issue 自動クローズ
```

CI で判定すべき基準：

| CI チェック | tasks.json 対応 |
|---|---|
| ユニットテスト | IMPL ステップ |
| 型チェック | VERIFY ステップ |
| リント | VERIFY ステップ |
| ビルド成功 | Gate passCondition |

**main 直接コミット（非 worktree）の場合は PR 作成対象なし。** 粒度が小さいタスクは引き続き main に直接コミットする運用で問題ない。

---

## ブランチとワークツリーの使い分け

**ブランチ**はコミット履歴のポインタ。通常1リポジトリで同時に1つしかチェックアウトできない。

**ワークツリー**（`git worktree add`）は物理的に別のディレクトリで同じリポジトリを展開する機能。各ディレクトリが別ブランチを向き、`.git` オブジェクトは共有される。

```
~/myproject/          ← main ブランチ
~/myproject-feat-A/   ← feature/A ブランチ（同じ .git を共有）
~/myproject-feat-B/   ← feature/B ブランチ（同じ .git を共有）
```

AI 開発でワークツリーが有効なケース：
- 複数の大きめ spec を並行実行するとき（1エージェント=1ワークツリー=競合なし）
- 実行中に割り込みタスクが入ったとき（main を触らず別ワークツリーで対応）

1日で完了する小さいタスクを main で直接作業する場合はワークツリー不要。

---

## 実装優先度まとめ

| 優先度 | 内容 | 難易度 |
|---|---|---|
| 1 | `dev:thread` スキル作成（軽量 Issue 作成） | 低 |
| 2 | `/dev:spec` 完了時に Issue 番号を `relatedIssues` に記録 | 低 |
| 3 | spec-run の worktree モード完了時に PR 自動作成（`Closes #N` 付き）+ CI 連動 | 中 |
