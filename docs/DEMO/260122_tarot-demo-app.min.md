# タロット占いデモアプリ - ユーザーストーリー

## 実装順序（推奨）

以下の順序で実装することで、段階的に機能を追加しながら動作確認できます：

**実装時の注意**: 各ストーリーの実装は `/dev:developing` コマンドを使用してください。TODO.mdのタスクリストに従って、TDD/E2E/TASKワークフローで自動的に進行します。

### Phase 1: 環境構築
1. **Story 1: 環境構築** (init-project)
   - PHPバックエンド + Reactフロントエンドの開発環境
   - **実装**: `/dev:developing docs/features/tarot-demo/stories/init-project/TODO.md`

### Phase 2: バックエンドAPI構築
2. **Story 2: デッキ生成・シャッフルAPI** (deck-shuffle-api)
   - **実装**: `/dev:developing docs/features/tarot-demo/stories/deck-shuffle-api/TODO.md`
3. **Story 3: カード抽選API** (card-draw-api)
   - **実装**: `/dev:developing docs/features/tarot-demo/stories/card-draw-api/TODO.md`
4. **Story 4: 運勢メッセージ生成API** (reading-api)
   - **実装**: `/dev:developing docs/features/tarot-demo/stories/reading-api/TODO.md`

### Phase 3: フロントエンド基盤
5. **Story 5: APIクライアント** (frontend-api-integration)
   - **実装**: `/dev:developing docs/features/tarot-demo/stories/frontend-api-integration/TODO.md`
6. **Story 6: 占い状態管理** (state-management)
   - **実装**: `/dev:developing docs/features/tarot-demo/stories/state-management/TODO.md`

### Phase 4: UIコンポーネント
7. **Story 7: カード表示・フリップ演出** (card-flip-animation)
   - **実装**: `/dev:developing docs/features/tarot-demo/stories/card-flip-animation/TODO.md`
8. **Story 8: スプレッドレイアウト** (spread-layout)
   - **実装**: `/dev:developing docs/features/tarot-demo/stories/spread-layout/TODO.md`
9. **Story 9: 結果画面** (result-screen)
   - **実装**: `/dev:developing docs/features/tarot-demo/stories/result-screen/TODO.md`

### Phase 5: 画面統合
10. **Story 10: スタート画面** (start-screen)
   - **実装**: `/dev:developing docs/features/tarot-demo/stories/start-screen/TODO.md`
11. **Story 11: メインアプリ統合** (app-integration)
   - **実装**: `/dev:developing docs/features/tarot-demo/stories/app-integration/TODO.md`

---

## プロジェクト概要

タロット占いができるWebアプリを作りたい。
PHPでバックエンドAPI、ReactでフロントエンドUIを構築する。
demo/tarot/backend/
demo/tarot/frontend/
みたいな構造で。

## 技術スタック

- バックエンド: PHP 8.x + Pest
- フロントエンド: React + TypeScript + Vitest
- スタイリング: Tailwind CSS

---

## ストーリー詳細

### Story 1: 環境構築 (init-project)

**分類**: TASK主体

開発者として、PHPバックエンドとReactフロントエンドの開発環境を構築したい。
Tailwind CSSも導入して、フロントエンドからAPIを呼び出せるようにしたい。

**受入条件**:
- demo/tarot/backend/ でPHP開発サーバーが起動できる
- demo/tarot/backend/ でPestテストが実行できる
- demo/tarot/frontend/ でReact開発サーバーが起動できる
- demo/tarot/frontend/ でVitestテストが実行できる
- Tailwind CSS のクラスがフロントエンドで適用される
- フロントエンドからバックエンドのAPIエンドポイントを呼び出してレスポンスを受け取れる

---

### Story 2: デッキ生成・シャッフルAPI (deck-shuffle-api)

**分類**: TDD主体

バックエンドとして、占いを始めるときに78枚のタロットカード（大アルカナ22枚、小アルカナ56枚）がシャッフルされた状態でAPIから提供したい。
毎回異なる占い結果を得られるように。

**追加要件**:
- 各カードにダミー画像パス（`/images/cards/dummy-{id}.png`）を含める
- 後で実際の画像ファイルに差し替え可能な構造にする

**受入条件**:
- 78枚のカードデータが正しく定義されている（大アルカナ22枚、小アルカナ56枚）
- APIからシャッフルされたデッキが取得できる
- 毎回異なる順序でカードが返される
- すべてのカードが重複なく含まれる
- 各カードに画像パスが含まれている

---

### Story 3: カード抽選API (card-draw-api)

**分類**: TDD主体

バックエンドとして、「3枚引き」リクエストを受けて、過去・現在・未来のポジションに異なるカードを配置して返したい。
各カードには正位置/逆位置もランダムに設定される。

**受入条件**:
- 3枚引きエンドポイントが正常に動作する
- 3枚のカードが重複なく抽選される
- 各カードにポジション（past/present/future）が割り当てられる
- 各カードに正位置/逆位置がランダムに設定される
- APIレスポンスが適切な形式で返される

---

### Story 4: 運勢メッセージ生成API (reading-api)

**分類**: TDD主体

バックエンドとして、引いたカードに応じた意味と総合的なアドバイスをAPIで返したい。
ポジションに応じた解釈も付ける。

**受入条件**:
- カードIDと引いた順番（ポジション）を受け取り、各カードの意味を返すことができる
- ポジションに応じた解釈（過去・現在・未来など）を付与できる
- 複数カードの組み合わせから総合的なアドバイスメッセージを生成できる
- 不正なカードIDやポジションに対して適切なエラーを返す
- APIレスポンスが構造化されたJSON形式である
- タロットカード78枚（大アルカナ22枚 + 小アルカナ56枚）のデータが定義されている

---

### Story 5: APIクライアント (frontend-api-integration)

**分類**: TDD + E2E

フロントエンドとして、バックエンドAPIを呼び出して占い結果を取得・管理したい。
エラーハンドリングとローディング状態も管理できるように。

**追加要件**:
- ローディングスピナーコンポーネント実装
- エラーメッセージコンポーネント実装（リトライボタン付き）

**受入条件**:
- 占い結果取得APIを呼び出せる
- エラーレスポンスを適切にハンドリングできる
- ローディング状態を管理できる
- 型安全なAPIクライアントである
- Zodスキーマでバリデーションできる
- ローディングスピナーが表示される
- エラー時にエラーメッセージとリトライボタンが表示される

---

### Story 6: 占い状態管理 (state-management)

**分類**: TDD主体

フロントエンドとして、占いの進行状態（初期/抽選中/結果表示）を管理したい。
「もう一度占う」で状態をリセットできるように。

**受入条件**:
- 初期状態がidleで「占う」ボタンが表示される
- 「占う」クリックでdrawing状態に遷移する
- 抽選完了後result状態に遷移する
- 「もう一度占う」で状態がリセットされる
- 状態遷移が単方向である（idle→drawing→result→idle）

---

### Story 7: カード表示・フリップ演出 (card-flip-animation)

**分類**: E2E主体

ユーザーとして、カードをタップすると裏から表にめくれるアニメーションを見たい。
占いの神秘的な雰囲気を楽しめるように。

**受入条件**:
- カードをタップすると裏から表にめくれるアニメーションが再生される
- アニメーションは3D回転で自然な「めくれ」を表現する
- アニメーション中はカードをタップできない（二重実行防止）
- アニメーション完了後はカードが表面のまま固定される
- レスポンシブデザインで各デバイスサイズに対応

---

### Story 8: スプレッドレイアウト (spread-layout)

**分類**: E2E主体

ユーザーとして、3枚引きのカードが「過去 - 現在 - 未来」の位置に横並びで表示されてほしい。
モバイルでも見やすいレイアウトで。

**受入条件**:
- デスクトップで3枚のカードが横並びで表示される
- 各カードの下に位置ラベル（過去・現在・未来）が表示される
- モバイル（375px）でカードが縦並びまたは適切なサイズで表示される
- タブレット（768px）で適切なレイアウトで表示される
- カード間のスペーシングが適切である
- スクリーンリーダーで各カードの位置が識別できる

---

### Story 9: 結果画面 (result-screen)

**分類**: E2E主体

ユーザーとして、占い結果として各カードの名前・画像・意味が表示されてほしい。
正位置/逆位置も明示して、総合運勢のまとめと「もう一度占う」ボタンも欲しい。

**受入条件**:
- 3枚のカードそれぞれについて、カード名・画像・正位置または逆位置・意味が表示されること
- 総合運勢のまとめテキストが表示されること
- 「もう一度占う」ボタンがあり、クリックでカード選択画面に戻れること
- モバイル・タブレット・デスクトップで適切に表示されること
- スクリーンリーダーでカード情報と総合運勢が読み上げられること
- キーボード操作で「もう一度占う」ボタンにフォーカスし、Enterで実行できること

---

### Story 10: スタート画面 (start-screen)

**分類**: E2E主体

ユーザーとして、アプリを開いたときに最初に表示されるスタート画面がほしい。
タイトル、説明文、「占う」ボタンがあり、ボタンをクリックすると占いが始まるようにしたい。

**受入条件**:
- idle状態でスタート画面が表示される
- アプリタイトルと説明文が表示される
- 「占う」ボタンが表示される
- 「占う」ボタンをクリックするとdrawing状態に遷移する
- レスポンシブデザイン対応（モバイル・タブレット・デスクトップ）
- キーボード操作でボタンにフォーカスしEnterで実行できる

---

### Story 11: メインアプリ統合 (app-integration)

**分類**: TDD + E2E

開発者として、すべてのコンポーネントとロジックを統合したメインアプリケーションを実装したい。
状態に応じて適切な画面（スタート画面、カード表示、結果画面）を表示し、ユーザーが占いを楽しめるようにしたい。

**統合対象**:
- Story 10: StartScreen（スタート画面）
- Story 7: CardFlipAnimation（カードフリップ）
- Story 8: SpreadLayout（3枚レイアウト）
- Story 9: ResultScreen（結果画面）
- Story 6: useTarotState（状態管理）
- Story 5: useTarotReading（API呼び出し）

**受入条件**:
- idle状態でStartScreenが表示される
- 「占う」クリックでdrawing状態に遷移し、API呼び出しが開始される
- カード抽選完了後、SpreadLayoutでカードが表示される
- 各カードをクリックするとフリップアニメーションが再生される
- すべてのカードがフリップ完了後、運勢メッセージAPIを呼び出す
- 運勢メッセージ取得後、ResultScreenが表示される
- 「もう一度占う」クリックでidle状態に戻る
- エラー発生時にエラー画面が表示され、リトライできる

---

## 完成後のユーザー体験フロー

1. **スタート画面** → 「占う」ボタンをクリック
2. **ローディング表示** → カード抽選API呼び出し中
3. **3枚のカード表示** → 「過去・現在・未来」の位置に配置
4. **カードタップ** → フリップアニメーションで表になる
5. **ローディング表示** → 運勢メッセージAPI呼び出し中
6. **結果画面表示** → 各カードの意味と総合運勢
7. **「もう一度占う」** → スタート画面に戻る

---

## プロジェクト構造

```
demo/tarot/
├── backend/                  # PHPバックエンド
│   ├── src/
│   │   ├── Controllers/     # APIコントローラー
│   │   ├── Services/        # ビジネスロジック
│   │   └── Models/          # データモデル
│   ├── tests/               # Pestテスト
│   ├── public/
│   │   └── index.php        # エントリーポイント
│   └── composer.json
│
└── frontend/                 # Reactフロントエンド
    ├── src/
    │   ├── components/      # UIコンポーネント
    │   ├── hooks/           # カスタムHooks
    │   ├── lib/             # APIクライアント
    │   ├── types/           # TypeScript型定義
    │   └── App.tsx          # メインアプリ
    ├── public/
    │   └── images/cards/    # カード画像（ダミー）
    ├── package.json
    └── vite.config.ts
```
