# assign-workflow

## 役割

タスクリストをTDD/E2E/TASKに分類し、TODO.mdを生成する。

## 推奨モデル

**haiku** - 単純な分類タスクに最適

## 入力

- `task-list.json`

## 出力

`TODO.md`

## 判定基準

### TDD対象
- 入出力が明確に定義可能
- アサーションで検証可能
- ロジック層（ビジネスロジック、バリデーション、計算）
- 副作用がない、またはモック可能

### E2E対象
- 視覚的な確認が必要
- UX/UI判断が含まれる
- プレゼンテーション層
- レスポンシブ対応、アニメーション

### TASK対象
- テスト不要（設定ファイル、環境構築）
- UI検証不要（コマンド実行結果で検証可能）
- 一回限りのセットアップ

→ 詳細: [../references/tdd-criteria.md] | [../references/e2e-criteria.md] | [../references/task-criteria.md]

## プロンプト

```
task-list.jsonを読み込み、各タスクをTDD/E2E/TASKに分類してください。

## タスクリスト
{task_list}

## 判定基準

### TDD（テスト駆動開発）
- 入出力が明確
- アサーションで検証可能
- ロジック層

例: validateEmail, calculateTotal, parseJson

### E2E（視覚的検証）
- 視覚的確認が必要
- UX判断が含まれる
- UIコンポーネント

例: LoginForm, Dashboard, Modal

### TASK（セットアップ/設定）
- テスト不要
- UI検証不要
- 一回限りのセットアップ

例: npm init, ESLint設定, Docker環境構築

## 出力形式（TODO.md）

```markdown
# TODO

## フェーズ1: {フェーズ名}

### TASKタスク
- [ ] [TASK][EXEC] {タスク名} 実行
- [ ] [TASK][VERIFY] {タスク名} 検証

### TDDタスク
- [ ] [TDD][RED] {タスク名} のテスト作成
- [ ] [TDD][GREEN] {タスク名} の実装
- [ ] [TDD][REFACTOR] {タスク名} のリファクタリング

### E2Eタスク
- [ ] [E2E][IMPL] {タスク名} 実装
- [ ] [E2E][AUTO] {タスク名} agent-browser検証

### 共通
- [ ] [CHECK] lint/format/build

## フェーズ2: ...
```

## ラベル説明

| ラベル | 意味 |
|--------|------|
| [TASK][EXEC] | タスク実行（設定/セットアップ） |
| [TASK][VERIFY] | 検証（ファイル存在/ビルド確認） |
| [TDD][RED] | テスト作成（失敗するテスト） |
| [TDD][GREEN] | 実装（テストを通す最小実装） |
| [TDD][REFACTOR] | リファクタリング |
| [TDD][REVIEW] | セルフレビュー |
| [E2E][IMPL] | UI実装 |
| [E2E][AUTO] | agent-browser自動検証 |
| [CHECK] | 品質チェック（lint/format/build） |
```

## 注意事項

- TASKタスクは最初に実行（環境構築が必要なため）
- TASKタスクはEXEC→VERIFYの順序
- TDDタスクは必ずRED→GREEN→REFACTORの順序
- E2EタスクはIMPL→AUTOの順序
- 各フェーズの最後にCHECKを入れる
