# team-opencode-plan Phase 0-3 改善案: コードベース探索の委譲

**作成日**: 2026-02-13
**対象スキル**: `dev:team-opencode-plan`
**Phase**: Phase 0-3（コード探索＆タスク分解）

## 現状の問題

### 現在の設計（SKILL.md Phase 0-3）

```
1. リーダーが対象コードベースを探索（Glob, Grep, Read）し、コンテキスト情報を収集する
2. 収集した情報を opencode に渡してタスク分解を実行
```

### 問題点

1. **冗長な作業**: リーダーとopencode で二重にコードベース探索が発生する可能性
2. **時間の浪費**: リーダーがファイルを読み込む時間が追加でかかる
3. **設計の矛盾**: opencode CLI はローカルで動作し、ファイルシステムに完全にアクセスできるため、リーダーの探索は理論上不要

### 実際の事例（2026-02-13セッション）

**タスク**: editorページのボタンホバーUX改善

**リーダーの探索**:
- `editor.tsx`, `Button.tsx`, `GenerateButton.tsx`, `WorkflowActions.tsx` を Read
- 現在の問題点を特定（cursor: pointer欠如、hover背景色の問題）
- 探索に約5-10分を費やした

**結果**: opencode が生成した task-list.json には、リーダーが収集した情報が反映されたが、**opencode 自身もこれらのファイルを探索できるはず**

## 改善案

### 案A: opencode に完全委譲（推奨）

Phase 0-3 を以下のように変更：

```
### 0-3: タスク分解 → task-list.json（opencode実行）

1. `references/prompts/task-breakdown.md` を Read で読み込み、変数を置換して opencode run を実行

**変数置換テーブル**:
| 変数 | 値の取得元 |
|------|-----------|
| `{story_analysis}` | `$PLAN_DIR/story-analysis.json` の内容 |
| `{plan_dir}` | `$PLAN_DIR`（0-0 で取得） |
```

**変更点**:
- `{codebase_context}` 変数を削除
- リーダーのコードベース探索ステップを削除
- opencode に「コードベース探索→タスク分解」を一貫して実行させる

**プロンプトの改善**（task-breakdown.md）:

```markdown
Based on the story analysis, perform the following:

1. **Explore the codebase** to identify:
   - Target files (components, pages, utilities related to the story)
   - Current implementation status and issues
   - Design system patterns (CSS variables, class naming conventions)
   - Existing tests and documentation

2. **Break down into detailed tasks** by role:
   - Designer: Specification tasks
   - Frontend/Backend: Implementation tasks
   - Reviewer: Verification tasks

3. **Output** `{plan_dir}/task-list.json` with:
   - Specific file paths in `context.targetFiles`
   - Concrete acceptance criteria
   - Design system references in `context.designSystemRefs`

## Story Analysis
{story_analysis}

## Output Path
{plan_dir}/task-list.json
```

### 案B: 軽量な探索のみ（折衷案）

リーダーは「探索の起点」のみ提供し、詳細は opencode に任せる：

```
1. リーダーが起点ファイルを特定（Glob のみ）
   例: `src/**/Button*.tsx`, `src/routes/editor.tsx`
2. ファイルパス一覧を opencode に渡す
3. opencode が詳細な探索とタスク分解を実行
```

**利点**: opencode の探索範囲を絞り込める
**欠点**: リーダーの作業が完全には削減されない

## メリット・デメリット比較

| 項目 | 現状 | 案A（完全委譲） | 案B（折衷） |
|------|------|-----------------|-------------|
| **リーダーの作業時間** | 長い（5-10分） | 短い（0-1分） | 中（2-5分） |
| **opencode の負荷** | 中 | 高 | 中 |
| **タスク品質** | 高 | 高（同等） | 高 |
| **エラーリスク** | 低 | 中（探索失敗の可能性） | 低 |
| **保守性** | 低（手順が多い） | 高（シンプル） | 中 |

## 推奨

**案A（完全委譲）を採用**し、以下の対策でリスクを軽減：

1. **リトライ機構**: opencode の探索失敗時は最大3回リトライ
2. **検証ステップ**: task-list.json 生成後、リーダーが targetFiles の妥当性を検証
3. **フォールバック**: 3回失敗時のみ、リーダーが探索してコンテキストを提供

## 実装ステップ

1. `references/prompts/task-breakdown.md` を更新
2. SKILL.md の Phase 0-3 を更新
3. 変数置換テーブルから `{codebase_context}` を削除
4. テスト: 簡単なタスクで検証
5. 本番適用

## 関連スキル

- `dev:team-opencode-plan`: 計画作成スキル（要更新）
- `dev:team-opencode-exec`: 実行スキル（影響なし）

## 参考

- 2026-02-13 セッション: ボタンホバーUX改善タスク
- ユーザー指摘: "opencode は外部サービスでなくcliで動作し別にコードは参照できるのでは"

---

**Status**: 提案
**優先度**: 中
**影響範囲**: dev:team-opencode-plan のみ
