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
