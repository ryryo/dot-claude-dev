# design-e2e-qa: screenshot.js before-script 拡張 + VP 内蔵化

## Gate 0: 準備 **必須工程(スキップ不可)**

この仕様書の実行には `/dev:spec-run` スキルを使用すること。

**Gate 0 通過条件**: `/dev:spec-run` の実行プロトコルに従い、実行モードを選択済みであること。

---

## 概要

`design-e2e-qa` スキルの `screenshot.js` に `--before-script` フラグを追加し、認証・インタラクションが必要なステートフル UI のスクリーンショット撮影に対応する。同時に、VP（ビューポート）処理を `screenshot.js` 内に内蔵し、1 ブラウザセッション内で 3VP（desktop/tablet/mobile）を一括撮影できるようにする。

## 背景

現在の `screenshot.js` は URL を指定して静的ページを撮影する設計。新しい Puppeteer セッションを毎回起動するため：

1. **認証が必要なページ**を撮影できない（Cookie/セッションなし）
2. **インタラクション後の状態**（チャット完走後の全バルーン表示等）をキャプチャできない（React state は URL に永続化されない）
3. VP 変更のたびにブラウザを再起動するため、ステートフルな画面状態が失われる

`ai-codlnk.com` のタロットスキル QA で顕在化した問題だが、認証付き SaaS・チャット UI・フォーム完了状態の QA など汎用的なユースケースに適用可能。

## 設計決定事項

| # | トピック | 決定 | 根拠 |
|---|---------|------|------|
| 1 | 拡張方式 | `--before-script <path>` フラグ 1 本のみ追加 | Cookie 注入・wait-for 等を個別フラグにするより汎用的。スクリプト内で何でも書ける |
| 2 | before-script API | `export default async (page) => {}` | Puppeteer page オブジェクトを直接操作。認証もインタラクションも統一的に記述可能 |
| 3 | VP 処理 | デフォルトで 3VP 撮影。screenshot.js 内でリサイズ＋SS ループ | フラグ不要でシンプル。1 セッション内で完結するためステートが保持される |
| 4 | 後方互換 | `--width`/`--height` 指定時は単一 VP モード | 既存の呼び出し元が壊れない |
| 5 | 配置場所 | before-script はプロジェクト側 `.claude/e2e/` | スキルは汎用のまま、プロジェクト固有のシナリオを分離 |
| 6 | take-screenshots.sh | VP ループを削除。ページループのみに簡素化 | screenshot.js が VP を担当するため不要 |

## アーキテクチャ詳細

### 変更後のフロー

```
take-screenshots.sh
  │
  ├── for page in "$@"
  │     └── node screenshot.js $url [--before-script $script] -o $output
  │
  └── (VP ループなし — screenshot.js 側で処理)

screenshot.js main()
  │
  ├── getBrowser()
  ├── setupPage(browser, url, { width: VP[0].width, height: VP[0].height })
  │
  ├── [--before-script 指定時] dynamic import → beforeFn(page)
  │
  ├── for VP in [desktop, tablet, mobile]:
  │     ├── page.setViewport({ width, height })
  │     ├── waitForResize(page)    ← VP 変更後の再描画待ち（新規）
  │     ├── autoScroll(page, ...)
  │     ├── waitForAllMedia(page)
  │     ├── takeFullPageScreenshot(page)
  │     ├── writeFile(outputPath with VP suffix)
  │     └── [--split-sections] splitByDom(page, screenshot, outputPath)
  │
  └── browser.close()
```

### デフォルト VP 定義（screenshot.js 内）

```javascript
const DEFAULT_VIEWPORTS = [
  { name: 'desktop', width: 1440, height: 2560 },
  { name: 'tablet',  width: 768,  height: 1024 },
  { name: 'mobile',  width: 390,  height: 844 },
];
```

### before-script API

```javascript
// .claude/e2e/tarot-complete.js の例
export default async function (page) {
  // 1. テストユーザーでログイン
  await page.waitForSelector('button');
  const buttons = await page.$$('button');
  for (const btn of buttons) {
    const text = await btn.evaluate(el => el.textContent);
    if (text.includes('テストユーザー')) {
      await btn.click();
      break;
    }
  }
  await page.waitForNavigation({ waitUntil: 'networkidle2' });

  // 2. タロットページへ遷移
  await page.goto('http://localhost:3000/skills/tarot', {
    waitUntil: 'networkidle2',
  });

  // 3. メッセージ送信
  await page.type('textarea', '仕事の転機について教えてください');
  await page.click('button[aria-label="送信"]');

  // 4. ヒアリング回答（AskUserQuestion）
  await page.waitForSelector('[role="option"]', { timeout: 60000 });
  await page.click('[role="option"]:first-child');
  await page.waitForSelector('[role="option"]', { timeout: 60000 });
  await page.click('[role="option"]:first-child');

  // 5. リーディング完了待ち
  await page.waitForFunction(
    () => document.body.innerText.includes('リーディング完了'),
    { timeout: 120000 }
  );
}
```

### 出力ファイル命名規則

| モード | 入力 `-o` | 出力ファイル |
|--------|-----------|-------------|
| デフォルト（3VP） | `-o dir/page-full.jpg` | `dir/page-desktop-full.jpg`, `dir/page-tablet-full.jpg`, `dir/page-mobile-full.jpg` |
| 単一VP（`--width`/`--height` 指定） | `-o dir/page-full.jpg` | `dir/page-full.jpg`（従来通り） |
| セクション分割付き | 上記 + `--split-sections` | `dir/page-desktop-full-section-01-header.jpg` 等 |

ファイル名の VP suffix 挿入ロジック:
```javascript
// "-full.jpg" → "-desktop-full.jpg"
function insertVpSuffix(outputPath, vpName) {
  const dir = dirname(outputPath);
  const ext = extname(outputPath);           // ".jpg"
  const base = basename(outputPath, ext);     // "page-full"
  return join(dir, `${base.replace(/-full$/, '')}-${vpName}-full${ext}`);
}
```

### waitForResize ヘルパー（新規）

VP 変更後に CSS メディアクエリの再評価とレイアウト再計算を待つ:

```javascript
async function waitForResize(page, timeout = 3000) {
  await page.evaluate(() => new Promise(resolve => {
    requestAnimationFrame(() => requestAnimationFrame(resolve));
  }));
  await new Promise(resolve => setTimeout(resolve, 500));
}
```

## 変更対象ファイルと影響範囲

### 変更するファイル

| ファイル | 変更内容 | 影響 |
|---------|---------|------|
| `scripts/screenshot.js` | `--before-script` フラグ追加、VP ループ内蔵、出力ファイル名にVP suffix | メイン変更。既存の単一VP動作は `--width`/`--height` 指定時に維持 |
| `scripts/take-screenshots.sh` | VP ループ削除、`--before-script` 引数パース＋転送 | 簡素化。出力パスも変更 |
| `agents/screenshot.md` | before-script の使い方追記 | Haiku エージェントへの指示更新 |
| `SKILL.md` | Phase 2 にステートフルUI向けフロー分岐を追記 | 新しいオプションの文書化 |

### 変更しないファイル

| ファイル | 理由 |
|---------|------|
| `scripts/lib/browser.js` | Puppeteer 起動設定は変更不要。ページセットアップも既存のまま |
| `scripts/lib/autoScroll.js` | スクロール処理は変更不要。VP 毎に呼ばれるだけ |
| `scripts/lib/largeScreenshot.js` | SS 撮影ロジックは変更不要 |
| `scripts/lib/splitSections.js` | セクション分割は変更不要 |
| `scripts/lib/waitForMedia.js` | メディア待機は変更不要 |

## 作業ディレクトリ

**すべてのファイルパスは `~/.claude/skills/dev/design-e2e-qa/` からの相対パス**で記載している。
実際の絶対パスは `~/dev/dot-claude-dev/.claude/skills/dev/design-e2e-qa/` である。

## 参照すべきファイル

### コードベース内

| ファイル | 目的 |
|---------|------|
| `scripts/screenshot.js` | 変更元。parseArgs、main() のフロー把握 |
| `scripts/take-screenshots.sh` | VP ループと screenshot.js 呼び出しの現状把握 |
| `scripts/lib/browser.js` | getBrowser/setupPage の API 確認 |
| `scripts/lib/autoScroll.js` | autoScroll のシグネチャ確認 |
| `scripts/lib/largeScreenshot.js` | takeFullPageScreenshot のシグネチャ確認 |
| `scripts/lib/splitSections.js` | splitByDom のシグネチャ確認 |
| `scripts/lib/waitForMedia.js` | waitForAllMedia のシグネチャ確認 |
| `SKILL.md` | Phase 2 の既存記述確認 |
| `agents/screenshot.md` | エージェント指示の現状確認 |

## タスクリスト

### 依存関係図

```
Gate A: screenshot.js 拡張
├── Todo 1: --before-script フラグ + VP 内蔵ループ追加
└── Todo 2: waitForResize ヘルパー追加

Gate B: take-screenshots.sh 簡素化（Gate A 完了後）
└── Todo 3: VP ループ削除 + --before-script 転送

Gate C: ドキュメント更新（Gate A 完了後）
├── Todo 4: agents/screenshot.md 更新
└── Todo 5: SKILL.md Phase 2 更新
```

### Gate A: screenshot.js 拡張

#### Todo 1: `--before-script` フラグ + VP 内蔵ループ追加

- [x] **Step 1 — IMPL**
  - **対象**: `scripts/screenshot.js`
  - **内容**:
    1. `node:path` のインポートに `extname`, `basename`, `join` を追加（`insertVpSuffix` で使用）
    2. `parseArgs` に `--before-script` オプションを追加（`options.beforeScript = ''`）
    3. `parseArgs` に `--width`/`--height` が明示的に指定されたかを追跡するフラグを追加:
       ```javascript
       options.singleViewport = false;  // デフォルト
       // --width / --height case 内で:
       options.singleViewport = true;
       ```
    4. `DEFAULT_VIEWPORTS` 定数を定義（desktop/tablet/mobile）
    5. `main()` を以下のフローに変更:
       - `options.singleViewport === true` → 従来通り単一 VP（後方互換）
       - `options.singleViewport === false` → `DEFAULT_VIEWPORTS` を使って VP ループ
    6. before-script 実行（`process.cwd()` 起点で解決）:
       ```javascript
       if (options.beforeScript) {
         console.log(`[Main] Running before-script: ${options.beforeScript}`);
         try {
           const scriptPath = resolve(process.cwd(), options.beforeScript);
           const { default: beforeFn } = await import(scriptPath);
           await beforeFn(page);
         } catch (err) {
           console.error(`[Main] before-script failed: ${err.message}`);
           process.exit(1);
         }
       }
       ```
    7. VP ループ内: `page.setViewport({ width, height })` → `waitForResize()` → `autoScroll(page, { step: height })` → `waitForAllMedia()` → `takeFullPageScreenshot()` → `writeFile()`
       - **autoScroll の step は VP の height に合わせる**（デスクトップ 2560 / モバイル 844 で自動調整）
    8. 出力ファイル名: `insertVpSuffix(outputPath, vpName)` でVP名を挿入
  - **実装詳細**: 「アーキテクチャ詳細」セクションの `screenshot.js main()` フローと `insertVpSuffix` 関数を参照
  - **依存**: なし

- [x] **Step 2 — Review A1**
  > **Review A1**: ✅ PASSED — quality(P1: Gate Bスコープ/設計判断), correctness(P2: macOS限定でスコープ外), conventions(P2: 仕様設計通り)。全指摘がスコープ外または設計判断に基づく。

#### Todo 2: waitForResize ヘルパー追加

- [x] **Step 1 — IMPL**
  - **対象**: `scripts/screenshot.js`（main 関数の近くにヘルパーとして定義）
  - **内容**: VP 変更後のレイアウト再描画を待つヘルパー関数を追加
  - **実装詳細**: 「アーキテクチャ詳細」セクションの `waitForResize` コードを参照。`requestAnimationFrame` 2 回 + 500ms 待機
  - **依存**: なし（Todo 1 と同時実装可）

- [x] **Step 2 — Review A2**
  > **Review A2**: ✅ PASSED — Todo 1 と同時実装・同時レビュー。waitForResize は rAF 2回 + 500ms で仕様通り。

**Gate A 通過条件**: 全 Review 結果記入欄が埋まり、以下を確認:
- `--before-script` なし + `--width 1440 --height 2560` 指定 → 従来通り単一 VP で SS 1 枚（ファイル名: `{page}-full.jpg`）
- `--before-script` なし + VP 指定なし → 3VP で SS 3 枚（ファイル名: `{page}-desktop-full.jpg`, `{page}-tablet-full.jpg`, `{page}-mobile-full.jpg`）
- `--before-script` あり → スクリプト実行後に 3VP で SS 3 枚

### Gate B: take-screenshots.sh 簡素化

#### Todo 3: VP ループ削除 + `--before-script` 転送

- [x] **Step 1 — IMPL**
  - **対象**: `scripts/take-screenshots.sh`
  - **内容**:
    1. `VIEWPORTS` 配列定義を削除
    2. 新規引数パース: `--before-script <path>` を検出して変数に保存
    3. 内側の `for vp in "${VIEWPORTS[@]}"` ループを削除
    4. ページループ内で `screenshot.js` を 1 回呼び出し:
       ```bash
       node "$SCREENSHOT_JS" "$url" \
         ${BEFORE_SCRIPT:+--before-script "$BEFORE_SCRIPT"} \
         --split-sections \
         -o "$OUTPUT_DIR/${page}-full.jpg"
       ```
    5. Usage メッセージを更新（`--before-script` オプション追記）
  - **実装詳細**: VP suffix（desktop/tablet/mobile）は screenshot.js 側が出力ファイル名に付与するため、take-screenshots.sh 側では base name のみ指定
  - **依存**: Gate A（screenshot.js が VP ループを内蔵していること）

- [x] **Step 2 — Review B3**
  > **Review B3**: ✅ PASSED — 指摘なし。引数パース・--before-script転送・VPループ削除が仕様通り。

**Gate B 通過条件**: 全 Review 結果記入欄が埋まり、以下を確認:
- `take-screenshots.sh http://localhost:3000 top:/` → 3VP の SS が生成される
- `take-screenshots.sh --before-script .claude/e2e/login.js http://localhost:3000 tarot:/skills/tarot` → before-script 実行後に 3VP の SS

### Gate C: ドキュメント更新

#### Todo 4: agents/screenshot.md 更新

- [x] **Step 1 — IMPL**
  - **対象**: `agents/screenshot.md`
  - **内容**:
    1. 「静的ページ」と「ステートフル UI（認証/インタラクション必要）」の 2 パターンを説明
    2. before-script 使用時のコマンド例を追記
    3. VP ループが screenshot.js 側に移動したことを反映（`--width`/`--height` は不要になった旨）
  - **依存**: Gate A

- [x] **Step 2 — Review C4**
  > **Review C4**: ✅ PASSED (FIX 1回) — P1(.mjs推奨)とP2(VPスコープ明確化)を修正後PASS

#### Todo 5: SKILL.md Phase 2 更新

- [x] **Step 1 — IMPL**
  - **対象**: `SKILL.md`
  - **内容**:
    1. Phase 2 の説明に「ステートフル UI 向けフロー分岐」を追記:
       - 判定基準: 認証が必要 / インタラクション後の状態を撮影したい → `--before-script` を使用
       - before-script の配置場所: プロジェクト側 `.claude/e2e/`
       - Phase 2 と Phase 3 の実行順序: ステートフル UI の場合は Phase 3（インタラクション設計）→ Phase 2（SS 撮影）の順に変更可
    2. `.tmp/design-e2e-qa/` ディレクトリ構造セクションに `.claude/e2e/` の説明を追加
  - **依存**: Gate A

- [x] **Step 2 — Review C5**
  > **Review C5**: ✅ PASSED — Todo 4 と同時レビュー・同時修正。

**Gate C 通過条件**: 全 Review 結果記入欄が埋まり、ドキュメントの整合性を確認

## 残存リスク

| リスク | 影響 | 緩和策 |
|--------|------|--------|
| before-script のインタラクションが LLM 応答に依存しタイミング不安定 | タロット等の LLM フローで SS 撮影タイミングがずれる可能性 | `page.waitForFunction()` で完了状態のテキスト出現を待つ。タイムアウトを十分長く設定（120s） |
| VP resize 後に CSS メディアクエリが再評価されない | モバイル用スタイルが反映されない SS になる可能性 | `waitForResize()` で rAF 2 回 + 500ms 待機。問題が残る場合は page 再作成（setViewport だけでなく新 page 作成）にフォールバック |
| before-script 内の page.goto() で URL が変わると autoScroll の対象が変わる | 初期 URL と異なるページの SS になる | before-script は「最終状態のページに留まる」ことを想定。SKILL.md に注記 |
| before-script の dynamic import 失敗（ファイル不在/構文エラー） | screenshot.js がクラッシュ | try/catch で明確なエラーメッセージを出力し `process.exit(1)` で終了（Todo 1 の実装詳細に記載済み） |
