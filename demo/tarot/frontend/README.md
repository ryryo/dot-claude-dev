# Tarot Frontend

React + TypeScript + Vite で構築された占いアプリケーションのフロントエンド。

## 開発環境セットアップ

### 初回セットアップ

```bash
npm install
```

### 開発サーバー起動

```bash
npm run dev
```

開発サーバーが起動したら、ブラウザで以下のURLにアクセスしてください:

```
http://localhost:5173
```

## コマンド一覧

| コマンド | 説明 |
|---------|------|
| `npm run dev` | 開発サーバー起動（ホットリロード対応） |
| `npm run build` | 本番用ビルド |
| `npm run preview` | ビルド結果をプレビュー |
| `npm run lint` | ESLintでコード品質をチェック |
| `npm test` | テスト実行（ウォッチモード） |
| `npm run test:ui` | テストをUIで実行 |
| `npm run test:run` | テストを単発実行 |

## テスト

### テストの実行

```bash
# ウォッチモード（推奨、開発時に使用）
npm test

# UIモードで実行
npm run test:ui

# 単発実行
npm run test:run
```

### テストファイル

テストファイルは対象ファイルと同じディレクトリに配置します。

```
src/
├── components/
│   ├── Button.tsx
│   └── Button.test.tsx    ← テスト
├── hooks/
│   ├── useUser.ts
│   └── useUser.test.ts    ← テスト
```

## 技術スタック

- **React**: 19.2.0
- **TypeScript**: 5.9.3
- **Vite**: 7.2.4
- **Tailwind CSS**: 4.1.18
- **Vitest**: 4.0.18
- **React Testing Library**: 16.3.2
- **ESLint**: 9.39.1
