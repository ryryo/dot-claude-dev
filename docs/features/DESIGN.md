# 総合DESIGN.md - プロジェクト横断的な設計判断

このファイルには、プロジェクト全体に適用される重要な設計判断、技術選定、ベストプラクティスを記録します。

---

## 更新履歴

### 2026-01-23: tarot-demo Phase 1 完了

**実装**: PHP Backend 環境構築
**詳細**: `docs/features/tarot-demo/stories/init-project/DESIGN.md`

---

## 1. テスト戦略

### TDDサイクルの厳格な適用

**原則**: RED → GREEN → REFACTOR → REVIEW → CHECK

**重要な判断**:
- テストを**必ず先に書く**（実装と同時・後付け禁止）
- GREENフェーズでは**最小実装**に留める（将来の要件を先取りしない）
- REFACTORフェーズで「変更不要」も正当な結果として認める
- REVIEWフェーズでテストへの過剰適合をチェック

**効果** (tarot-demo Phase 1):
- 仕様の明確化
- 過剰設計の防止
- コード品質の向上

**適用判断基準**:
- ✅ TDD適用: ロジック層（入出力が明確、ビジネスロジック、バリデーション）
- ❌ TDD不要: インフラ層（設定ファイル、エントリーポイント）

---

### テストフレームワーク選択基準

**PHP**: Pest を標準採用

**理由**:
- describe/it構文でJavaScript系テスト（Vitest/Jest）と統一されたDX
- モダンなAPIでコードの可読性が高い
- PHPUnitベースで信頼性を確保

**注意点**:
- PHP 8.3未満の環境ではPest v3系を使用（v4はPHP 8.3+要求）
- Composer plugin許可が必要: `composer config allow-plugins.pestphp/pest-plugin true`

**JavaScript/TypeScript**: Vitest を標準採用

**理由**:
- 高速、ESM/TypeScriptネイティブ対応
- Vite統合でビルドツールと統一

---

## 2. コーディング規約

### declare(strict_types=1) の徹底

**適用範囲**: すべてのPHPファイル（テスト含む）

```php
<?php

declare(strict_types=1);
```

**効果**:
- 型の厳密チェック有効化
- 意図しない型変換の防止
- PSR-12準拠

**重要性**: プロジェクト全体で一貫して適用することで型安全性を担保

---

### PSR-12準拠の徹底

**適用基準**: すべてのPHPコード

**主要ポイント**:
- `declare(strict_types=1);` を全ファイルに記述
- namespace宣言
- 型ヒントの明示
- 適切なインデント・命名規則

---

## 3. アーキテクチャパターン

### シンプル実装優先の原則

**判断基準**: 機能の複雑さと要件に応じて段階的に導入

**例**: Router実装（tarot-demo）
- ❌ フレームワーク依存（Laravel, Symfonyなど）
- ✅ 自作Routerクラス（軽量、学習コスト低）

**理由**:
- デモ/小規模アプリケーションでは軽量実装が適切
- エンドポイント数が少ない場合はフレームワーク不要
- 将来の拡張性は必要になってから追加

**原則**: YAGNI（You Aren't Gonna Need It）を重視

---

### Controller層の責務分離

**パターン**: Controllerはビジネスロジックを持たず、レスポンス生成に専念

**例**: HealthCheckController
```php
class HealthCheckController
{
    public function handle(): array
    {
        return ['status' => 'ok'];
    }
}
```

**原則**:
- Controllerは薄く保つ
- 複雑なロジックはService層に委譲（今回は不要）
- テスト容易性を優先

---

## 4. API設計

### CORS設定のベストプラクティス

**開発環境**: 全許可で開発効率優先
```php
header('Access-Control-Allow-Origin: *');
```

**本番環境**: 特定ドメインに限定
```php
header('Access-Control-Allow-Origin: https://example.com');
```

**プリフライトリクエスト対応**:
```php
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}
```

**重要**: セキュリティとDXのバランスを環境ごとに調整

---

### RESTful API規約

**エンドポイント命名**:
- `/api/{resource}` 形式
- 複数形を使用（例: `/api/users`）
- ヘルスチェックは `/api/health`

**HTTPメソッド**:
- GET: 取得
- POST: 作成
- PUT/PATCH: 更新
- DELETE: 削除

**レスポンス形式**: JSON統一
```json
{
  "status": "ok",
  "data": { ... },
  "error": null
}
```

---

## 5. プロジェクト構造

### ディレクトリ構造の標準化

**PHP Backend**:
```
backend/
├── public/          # 公開ディレクトリ（Webサーバーのドキュメントルート）
├── src/             # アプリケーションコード
│   └── Controllers/ # コントローラー層
├── tests/           # テストコード
│   ├── Feature/     # 機能テスト（統合テスト）
│   └── Unit/        # ユニットテスト
└── vendor/          # Composer依存パッケージ
```

**重要**:
- `public/` をドキュメントルートに設定（セキュリティ）
- `vendor/` や `.env` をWeb公開しない

---

### .gitignore の必須エントリ

**PHP**:
```
/vendor/
.env
.phpunit.cache
/.phpunit.result.cache
```

**JavaScript/TypeScript**:
```
/node_modules/
/dist/
.env
.env.local
```

**共通**:
```
.DS_Store
.idea/
.vscode/
```

---

## 6. 開発ワークフロー

### コミット戦略

**TDDサイクル**:
1. テストコミット（REDフェーズ完了時）
2. 実装コミット（GREEN + REFACTOR + REVIEW + CHECK完了時）

**コミットメッセージ規約**:
- `test:` - テスト追加（REDフェーズ）
- `feat:` - 機能実装（GREENフェーズ以降）
- `chore:` - TDDサイクル完了、環境構築など
- `docs:` - ドキュメント更新

**Co-Authored-By**: すべてのコミットに付与
```
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

---

### README作成の原則

**必須セクション**:
1. プロジェクト概要
2. 環境要件
3. セットアップ手順
4. 開発サーバー起動方法
5. テスト実行方法
6. プロジェクト構造

**タイミング**: 実装と並行して作成（後回しにしない）

---

## 7. 技術的発見・Tips

### Composer autoload

**設定**:
```json
"autoload": {
    "psr-4": {
        "Namespace\\": "src/"
    }
}
```

**Tips**:
- `composer install` 後、自動的にautoloadファイル生成
- 新規クラス追加時も自動更新（`dump-autoload` 不要）

---

### PHP開発サーバー起動

**正しいコマンド**:
```bash
php -S localhost:8000 -t public
```

**重要**: `-t public` でドキュメントルート指定必須

---

### 対話的コマンドの自動化

**例**: Pest初期化
```bash
echo "no" | vendor/bin/pest --init
```

**学び**: CI/CD環境では対話的プロンプトがブロック要因になる

---

## 8. メトリクス・ベンチマーク

### tarot-demo Phase 1

| 項目 | 値 |
|------|-----|
| 実装時間 | 約30分 |
| コミット数 | 6回 |
| テスト成功率 | 100% (4 passed, 6 assertions) |
| LOC | 約150行（テスト含む） |

---

## 9. 次回への引き継ぎ事項

### Phase 2（React Frontend）での注意点

1. **CORS確認**: PHP APIサーバーのCORS設定が正しく動作するか検証
2. **ポート管理**:
   - PHP: localhost:8000
   - React: localhost:5173（Vite default）
3. **APIクライアント**: TDD適用（入出力明確）
4. **E2E検証**: agent-browserでUI確認

---

## 10. 改善提案（継続的改善）

### 今後検討すべき項目

1. **composer.lock管理**: アプリケーションとして含めるべきか再検討
2. **Routerエラーハンドリング**: 現状404のみ、500系エラーも対応
3. **環境変数管理**: .env ファイル導入を検討

---

## 参照

- プロジェクト規約: `/CLAUDE.md`
- PHP規約: `.claude/rules/languages/php/`
- TDDワークフロー: `.claude/rules/workflow/tdd-workflow.md`
