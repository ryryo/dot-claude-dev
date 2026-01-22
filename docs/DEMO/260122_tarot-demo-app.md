# タロット占いデモアプリ計画書

## 概要

dev:story / dev:developing / dev:feedback スキルの統合テスト用デモプロジェクト。
TASK / PHP TDD / TypeScript TDD / E2E の全ワークフローを検証できる構成。

## 目的

- **スキル検証**: dev:story によるTDD/E2E/TASK分岐の自動判定
- **ワークフロー検証**:
  - TASK（EXEC→VERIFY→COMMIT）
  - PHP TDD（Pest: RED→GREEN→REFACTOR）
  - TypeScript TDD（Vitest: RED→GREEN→REFACTOR）
  - E2E（agent-browser検証）
- **フィードバック検証**: dev:feedback によるDESIGN.md蓄積と改善提案
- **言語別ルール検証**: PHP/TypeScript/Reactルールの自動適用

## 技術スタック（想定）

### フロントエンド
- TypeScript
- React
- Vitest（テスト）
- CSS Modules / Tailwind

### バックエンド
- PHP 8.x
- Pest（テスト）
- JSON API（RESTful）

---

## ストーリー一覧

### TASKストーリー（環境構築）

#### Story 0-1: PHPバックエンド環境構築

```
開発者として、PHPバックエンドの開発環境を構築したい
それによって、APIの実装を開始できる
```

**完了条件**:
- [ ] backend/ ディレクトリ作成
- [ ] composer.json 作成（autoload設定含む）
- [ ] Pest インストール・設定（pest.php）
- [ ] ディレクトリ構造作成（app/Services, app/Models, tests/Unit）
- [ ] APIエントリーポイント（public/index.php）作成
- [ ] `composer test` でPestが実行できる

---

#### Story 0-2: Reactフロントエンド環境構築

```
開発者として、Reactフロントエンドの開発環境を構築したい
それによって、UIの実装を開始できる
```

**完了条件**:
- [ ] Vite + React + TypeScript でプロジェクト作成
- [ ] Vitest インストール・設定（vitest.config.ts）
- [ ] React Testing Library インストール
- [ ] `npm test` でVitestが実行できる
- [ ] `npm run dev` で開発サーバーが起動できる

---

#### Story 0-3: Tailwind CSS導入

```
開発者として、Tailwind CSSを導入したい
それによって、効率的にUIスタイリングができる
```

**完了条件**:
- [ ] Tailwind CSS インストール
- [ ] tailwind.config.js 作成
- [ ] postcss.config.js 作成
- [ ] src/index.css にTailwindディレクティブ追加
- [ ] サンプルコンポーネントでTailwindクラスが適用される

---

#### Story 0-4: API連携設定

```
開発者として、フロントエンドからバックエンドAPIを呼び出せるようにしたい
それによって、フルスタック開発ができる
```

**完了条件**:
- [ ] Vite proxy設定（vite.config.ts）
- [ ] 環境変数設定（.env, .env.example）
- [ ] CORS設定（PHP側）
- [ ] APIベースURL設定（フロントエンド側）

---

### PHP TDDストーリー（バックエンドAPI）

#### Story 1: デッキ生成・シャッフルAPI

```
バックエンドとして、占い開始時に
78枚のタロットカードをシャッフルしてAPIで提供したい
それによって、フロントエンドに占いデータを供給できる
```

**受け入れ条件**:
- [ ] 大アルカナ22枚が含まれる（愚者〜世界）
- [ ] 小アルカナ56枚が含まれる（4スート × 14枚）
- [ ] シャッフル後、重複するカードがない
- [ ] GET /api/deck でシャッフル済みデッキを取得

**TDD（Pest）で検証するロジック**:
- `DeckService::createDeck()`: 78枚のカード配列を生成
- `DeckService::shuffle(array $deck)`: Fisher-Yatesシャッフル
- `Card` クラス（id, name, suit, number, arcana）

---

#### Story 2: カード抽選API

```
バックエンドとして、「3枚引き」リクエストを受けて
過去・現在・未来のポジションにカードを配置して返したい
それによって、フロントエンドで占い結果を表示できる
```

**受け入れ条件**:
- [ ] POST /api/draw で指定枚数のカードを抽選
- [ ] 同じカードが複数回選ばれない
- [ ] 各カードに正位置/逆位置がランダムに設定される
- [ ] 各カードにポジション（過去/現在/未来）が割り当てられる

**TDD（Pest）で検証するロジック**:
- `DrawService::draw(array $deck, int $count)`: N枚のカードを抽選
- `DrawService::determineOrientation()`: 正位置/逆位置判定
- `DrawService::assignPositions(array $cards, string $spread)`: ポジション割り当て

---

#### Story 3: 運勢メッセージ生成API

```
バックエンドとして、引いたカードに応じた
意味と総合アドバイスをAPIで返したい
それによって、フロントエンドで結果を表示できる
```

**受け入れ条件**:
- [ ] POST /api/reading で運勢メッセージを生成
- [ ] カード×正逆の組み合わせで意味テキストを返す
- [ ] ポジションに応じた解釈が付与される
- [ ] 総合メッセージが含まれる

**TDD（Pest）で検証するロジック**:
- `ReadingService::getCardMeaning(Card $card, bool $reversed)`: カードの意味を取得
- `ReadingService::interpretPosition(Card $card, string $position)`: ポジション別解釈
- `ReadingService::generateSummary(array $readings)`: 総合運勢生成

---

### TypeScript TDDストーリー（フロントエンドロジック）

#### Story 4: APIクライアント

```
フロントエンドとして、バックエンドAPIを呼び出して
占い結果を取得・管理したい
それによって、UIにデータを供給できる
```

**受け入れ条件**:
- [ ] API呼び出しが成功した場合、データを返す
- [ ] API呼び出しが失敗した場合、エラーを返す
- [ ] ローディング状態を管理できる

**TDD（Vitest）で検証するロジック**:
- `tarotApi.getDeck()`: デッキ取得（モック）
- `tarotApi.drawCards(count)`: カード抽選（モック）
- `tarotApi.getReading(cards)`: 運勢取得（モック）
- エラーハンドリング

---

#### Story 5: 占い状態管理

```
フロントエンドとして、占いの進行状態を管理したい
それによって、UIの表示を適切に制御できる
```

**受け入れ条件**:
- [ ] 占いの状態（初期/抽選中/結果表示）を管理
- [ ] 抽選結果のカードを保持
- [ ] 「もう一度占う」で状態をリセット

**TDD（Vitest）で検証するロジック**:
- `useTarot()` カスタムHook
- 状態遷移ロジック
- リセット処理

---

### E2Eストーリー（UI検証）

#### Story 6: カード表示・フリップ演出

```
ユーザーとして、カードをタップすると
裏から表にめくれるアニメーションを見たい
それによって、占いの神秘的な雰囲気を楽しめる
```

**受け入れ条件**:
- [ ] カードが裏面の状態で表示される
- [ ] タップ/クリックで表面にフリップする
- [ ] フリップアニメーションが滑らかに動作する
- [ ] フリップ後、カード名と画像が表示される

**agent-browserで検証する項目**:
- カード要素の存在確認
- クリック操作でフリップが発生するか
- アニメーション完了後の表示状態

---

#### Story 7: スプレッドレイアウト

```
ユーザーとして、3枚引きのカードが
「過去 - 現在 - 未来」の位置に並んで表示されてほしい
それによって、時間の流れを視覚的に理解できる
```

**受け入れ条件**:
- [ ] 3枚のカードが横並びで表示される
- [ ] 各カードの下にポジション名が表示される
- [ ] モバイル（375px）でも見やすいレイアウト
- [ ] カード間の余白が適切

**agent-browserで検証する項目**:
- デスクトップでの横並び表示
- モバイルサイズでのレスポンシブ対応
- ポジションラベルの表示

---

#### Story 8: 結果画面

```
ユーザーとして、占い結果として
各カードの意味と総合運勢を読みやすく見たい
それによって、占い結果を理解し活用できる
```

**受け入れ条件**:
- [ ] 各カードの名前・画像・意味が表示される
- [ ] 正位置/逆位置が明示される
- [ ] 総合運勢のまとめが表示される
- [ ] 「もう一度占う」ボタンがある

**agent-browserで検証する項目**:
- 結果テキストの表示確認
- 全体のレイアウト・読みやすさ
- 再占いボタンの動作

---

## ディレクトリ構成（想定）

```
tarot-demo/
├── backend/                      # PHP バックエンド
│   ├── app/
│   │   ├── Services/
│   │   │   ├── DeckService.php   # デッキ生成・シャッフル
│   │   │   ├── DrawService.php   # カード抽選
│   │   │   └── ReadingService.php # 運勢メッセージ
│   │   ├── Models/
│   │   │   └── Card.php          # カードモデル
│   │   └── Data/
│   │       └── CardMeanings.php  # カードの意味データ
│   ├── public/
│   │   └── index.php             # APIエントリーポイント
│   ├── tests/
│   │   └── Unit/
│   │       ├── Services/
│   │       │   ├── DeckServiceTest.php
│   │       │   ├── DrawServiceTest.php
│   │       │   └── ReadingServiceTest.php
│   │       └── Models/
│   │           └── CardTest.php
│   ├── composer.json
│   └── phpunit.xml / pest.php
│
├── frontend/                     # React フロントエンド
│   ├── src/
│   │   ├── api/
│   │   │   ├── tarotApi.ts       # APIクライアント
│   │   │   └── tarotApi.test.ts  # APIクライアントテスト
│   │   ├── hooks/
│   │   │   ├── useTarot.ts       # 状態管理Hook
│   │   │   └── useTarot.test.ts  # Hookテスト
│   │   ├── components/
│   │   │   ├── Card/             # カード表示
│   │   │   ├── Spread/           # スプレッドレイアウト
│   │   │   └── Result/           # 結果画面
│   │   └── App.tsx
│   ├── package.json
│   └── vitest.config.ts
│
└── DESIGN.md                     # 実装で得た知見
```

---

## 実行順序

1. **Story 0-1〜0-4（TASK）**: 環境構築・セットアップ
2. **Story 1-3（PHP TDD）**: バックエンドAPIをPestでTDD実装
3. **Story 4-5（TypeScript TDD）**: フロントエンドロジックをVitestでTDD実装
4. **Story 6-8（E2E）**: UI層をagent-browserで検証しながら実装
5. **dev:feedback**: 実装完了後、DESIGN.mdに知見を蓄積

---

## 検証ポイント

| スキル | 検証内容 |
|--------|----------|
| dev:story | ストーリーからTDD/E2E/TASKラベル付きタスクが正しく生成されるか |
| dev:developing (TASK) | EXEC→VERIFY→COMMITサイクルで環境構築が完了するか |
| dev:developing (PHP TDD) | Pest で RED→GREEN→REFACTORサイクルが回るか |
| dev:developing (TS TDD) | Vitest で RED→GREEN→REFACTORサイクルが回るか |
| dev:developing (E2E) | agent-browser検証が正しく動作するか |
| dev:feedback | DESIGN.md更新と改善提案が生成されるか |
| ルール自動適用 | PHP/TypeScript/React の言語別ルールが適用されるか |

---

## 備考

- カード画像はプレースホルダー（色+テキスト）で代用可
- 78枚全ての意味データは最小限（大アルカナのみでも可）
- スプレッドは「3枚引き」のみで十分
