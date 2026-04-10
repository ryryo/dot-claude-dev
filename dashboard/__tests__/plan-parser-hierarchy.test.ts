import { describe, expect, it } from 'vitest';

import { extractStepDescription, parseReviewBlockquote } from '../lib/plan-parser';

describe('extractStepDescription', () => {
  it('`- **内容**:` があれば内容フィールドの値を返す', () => {
    const block = `- [ ] **Step 1 — IMPL**
  - **内容**: ステップ説明文
  - **実装詳細**: 別の説明
`;

    expect(extractStepDescription(block)).toBe('ステップ説明文');
  });

  it('`内容` が無く `実装詳細` があれば第一文だけを返す', () => {
    const block = `- [ ] **Step 1 — IMPL**
  - **実装詳細**: 最初の文。次の文。
`;

    expect(extractStepDescription(block)).toBe('最初の文。');
  });

  it('`内容`/`実装詳細` が無く `対象` があればその値を返す', () => {
    const block = `- [ ] **Step 1 — IMPL**
  - **対象**: dashboard/lib/plan-parser.ts
`;

    expect(extractStepDescription(block)).toBe('dashboard/lib/plan-parser.ts');
  });

  it('フィールド系が無く最初の bullet テキストがあればそれを返す', () => {
    const block = `- [ ] **Step 1 — IMPL**
  - これは任意のテキスト
`;

    expect(extractStepDescription(block)).toBe('これは任意のテキスト');
  });

  it('`- **依存**: なし` bullet しかない場合は空文字を返す', () => {
    const block = `- [ ] **Step 1 — IMPL**
  - **依存**: なし
`;

    expect(extractStepDescription(block)).toBe('');
  });

  it('`- **[TDD]**` bullet しかない場合は空文字を返す', () => {
    const block = `- [ ] **Step 1 — IMPL**
  - **[TDD]**: テスト先行で進める
`;

    expect(extractStepDescription(block)).toBe('');
  });

  it('マークダウン記法（太字・コード・リンク）が除去される', () => {
    const block = `- [ ] **Step 1 — IMPL**
  - **内容**: **太字** と \`コード\` と [リンク](https://example.com)
`;

    const result = extractStepDescription(block);

    expect(result).toContain('太字');
    expect(result).toContain('コード');
    expect(result).toContain('リンク');
    expect(result).not.toContain('**');
    expect(result).not.toContain('`');
    expect(result).not.toContain('[');
    expect(result).not.toContain('](');
  });
});

describe('parseReviewBlockquote', () => {
  it('PASSED + FIX 回数 + commit hash を含む blockquote から結果を抽出する', () => {
    const block = `- [x] **Step 2 — Review A2**

  > **Review A2**: ✅ PASSED (FIX 1回) — commits a05e43f, d57675a
  > - 初回レビューで [P2] コードブロック内 \`##\` 誤検出を指摘 → \`maskCodeFences\` 追加で修正
  > - 再レビュー: regression なし
`;

    const result = parseReviewBlockquote(block);

    expect(result.hasReview).toBe(true);
    expect(result.reviewFilled).toBe(true);
    expect(result.reviewResult).toBe('PASSED');
    expect(result.reviewFixCount).toBe(1);
    expect(result.summary).not.toContain('commits a05e43f');
    expect(result.summary).not.toContain('d57675a');
  });

  it('SKIPPED + 括弧付きの補足 + commit hash を処理する', () => {
    const block = `- [x] **Step 2 — Review A1**

  > **Review A1**: ⏭️ SKIPPED (型定義のみ、ロジック変更なし) — commit a05e43f
`;

    const result = parseReviewBlockquote(block);

    expect(result.hasReview).toBe(true);
    expect(result.reviewFilled).toBe(true);
    expect(result.reviewResult).toBe('SKIPPED');
    expect(result.reviewFixCount).toBeNull();
    expect(result.summary).not.toContain('commit a05e43f');
  });

  it('PASSED + 1行要約（FIX 回数なし）を抽出する', () => {
    const block = `- [x] **Step 2 — Review B1**

  > **Review B1**: ✅ PASSED — react-markdown を追加
`;

    const result = parseReviewBlockquote(block);

    expect(result.reviewResult).toBe('PASSED');
    expect(result.reviewFixCount).toBeNull();
    expect(result.summary).toContain('react-markdown');
  });

  it('空の Review blockquote は hasReview=true / reviewFilled=false を返す', () => {
    const block = `- [ ] **Step 2 — Review A1**

  > **Review A1**:
`;

    const result = parseReviewBlockquote(block);

    expect(result.hasReview).toBe(true);
    expect(result.reviewFilled).toBe(false);
    expect(result.reviewResult).toBeNull();
    expect(result.summary).toBe('');
  });

  it('Review blockquote が存在しない Step は hasReview=false を返す', () => {
    const block = `- [ ] **Step 1 — IMPL**
  - **内容**: 実装のみ
`;

    const result = parseReviewBlockquote(block);

    expect(result.hasReview).toBe(false);
    expect(result.reviewFilled).toBe(false);
    expect(result.reviewResult).toBeNull();
  });

  it('FAILED ラベルを抽出できる', () => {
    const block = `- [x] **Step 2 — Review C1**

  > **Review C1**: ❌ FAILED — テスト実行エラーが残存
`;

    const result = parseReviewBlockquote(block);

    expect(result.reviewResult).toBe('FAILED');
    expect(result.summary).toContain('テスト実行エラー');
  });

  it('commit hash が summary から除去される', () => {
    const block = `- [x] **Step 2 — Review B2**

  > **Review B2**: ✅ PASSED — commits abc123, def456 を参照
`;

    const result = parseReviewBlockquote(block);

    expect(result.summary).not.toContain('commits abc123');
    expect(result.summary).not.toContain('def456');
  });
});
