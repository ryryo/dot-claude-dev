import { describe, expect, it } from 'vitest';

import { parsePlanFile } from '../lib/plan-parser';

describe('parsePlanFile - summary extraction', () => {
  const filePath = 'projects/sample/PLAN.md';
  const projectName = 'sample-project';

  it('`## 概要` セクションがある場合はテキストを抽出する', () => {
    const content = '# タイトル\n\n## 概要\n\nこれは概要テキスト。\n\n## 背景\n\n背景情報';

    const result = parsePlanFile(content, filePath, projectName);

    expect(result.summary).toBe('これは概要テキスト。');
  });

  it('`## 概要` が無い場合は冒頭テキストへフォールバックする', () => {
    const content = '# タイトル\n\nこれは冒頭テキスト。\n\n## 背景\n\n背景情報';

    const result = parsePlanFile(content, filePath, projectName);

    expect(result.summary).toBe('これは冒頭テキスト。');
  });

  it('`## 概要` も冒頭テキストも無い場合は空文字を返す', () => {
    const content = '# タイトル\n\n## 背景\n\n背景情報';

    const result = parsePlanFile(content, filePath, projectName);

    expect(result.summary).toBe('');
  });

  it('`## 概要` が空の場合は冒頭テキストへフォールバックする', () => {
    const content = '# タイトル\n\n冒頭テキスト\n\n## 概要\n\n## 背景';

    const result = parsePlanFile(content, filePath, projectName);

    expect(result.summary).toBe('冒頭テキスト');
  });

  it('summary ではマークダウン記法が除去される', () => {
    const content =
      '# タイトル\n\n## 概要\n\n**太字** と *斜体* と `コード` と [リンク](https://example.com)\n\n- リスト\n\n## 次';

    const result = parsePlanFile(content, filePath, projectName);

    expect(result.summary).toContain('太字');
    expect(result.summary).toContain('斜体');
    expect(result.summary).toContain('コード');
    expect(result.summary).toContain('リンク');
    expect(result.summary).toContain('リスト');
    expect(result.summary).not.toContain('**');
    expect(result.summary).not.toContain('*');
    expect(result.summary).not.toContain('`');
    expect(result.summary).not.toContain('[');
    expect(result.summary).not.toContain(']');
    expect(result.summary).not.toMatch(/^-\s/m);
  });

  it('コードブロック内の `## 概要` を誤検出しない', () => {
    const content =
      '# タイトル\n\n本物の概要テキスト\n\n## 背景\n\n```markdown\n## 概要\nこれは偽物\n```';

    const result = parsePlanFile(content, filePath, projectName);

    expect(result.summary).toBe('本物の概要テキスト');
  });
});

describe('parsePlanFile - rawMarkdown', () => {
  const filePath = 'projects/sample/PLAN.md';
  const projectName = 'sample-project';

  it('rawMarkdown は入力 content をそのまま返す', () => {
    const content = '# タイトル\n\n## 概要\n\n**そのまま** `保持` する';

    const result = parsePlanFile(content, filePath, projectName);

    expect(result.rawMarkdown).toBe(content);
  });
});
