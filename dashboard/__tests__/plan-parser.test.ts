import { describe, expect, it } from 'vitest';

import { parsePlanFile } from '../lib/plan-parser';

describe('parsePlanFile', () => {
  const filePath = 'projects/sample/PLAN.md';
  const projectName = 'sample-project';

  it('H1見出しをtitleとして抽出する', () => {
    const content = `
# テスト計画

本文です。
`;

    const result = parsePlanFile(content, filePath, projectName);

    expect(result.title).toBe('テスト計画');
    expect(result.filePath).toBe(filePath);
    expect(result.fileName).toBe('PLAN.md');
    expect(result.projectName).toBe(projectName);
  });

  it('Gate/Todo構造がない古いPLANはnot-startedになる', () => {
    const content = `
# 旧形式の計画

## 背景

手順だけが書かれた古いPLANです。
`;

    const result = parsePlanFile(content, filePath, projectName);

    expect(result.status).toBe('not-started');
    expect(result.gates).toEqual([]);
    expect(result.todos).toEqual([]);
    expect(result.progress).toEqual({
      total: 0,
      completed: 0,
      percentage: 0,
    });
  });

  it('すべて未チェックのPLANはnot-startedになる', () => {
    const content = `
# 未着手の計画

### Gate A: セットアップ

- [ ] **Todo A1**: 環境構築
  > **Review A1**:

- [ ] **Todo A2**: 設定ファイル
  > **Review A2**:
`;

    const result = parsePlanFile(content, filePath, projectName);

    expect(result.status).toBe('not-started');
  });

  it('チェック済みと未チェックが混在するPLANはin-progressになる', () => {
    const content = `
# テスト計画

### Gate A: セットアップ

- [x] **Todo A1**: 環境構築
  > **Review A1**: PASS

- [ ] **Todo A2**: 設定ファイル
  > **Review A2**:

### Gate B: 実装

- [ ] **Todo B1**: 機能実装
  > **Review B1**:
`;

    const result = parsePlanFile(content, filePath, projectName);

    expect(result.status).toBe('in-progress');
  });

  it('未チェックTodoにReview内容があればin-reviewになる', () => {
    const content = `
# レビュー中の計画

### Gate A: セットアップ

- [ ] **Todo A1**: 環境構築
  > **Review A1**: 軽微な修正待ち
`;

    const result = parsePlanFile(content, filePath, projectName);

    expect(result.status).toBe('in-review');
  });

  it('すべてチェック済みのPLANはcompletedになる', () => {
    const content = `
# 完了した計画

### Gate A: セットアップ

- [x] **Todo A1**: 環境構築
  > **Review A1**: PASS

- [x] **Todo A2**: 設定ファイル
  > **Review A2**: PASS
`;

    const result = parsePlanFile(content, filePath, projectName);

    expect(result.status).toBe('completed');
  });

  it('Gateタイトルと所属Todoを正しく抽出する', () => {
    const content = `
# テスト計画

### Gate A: セットアップ

- [x] **Todo A1**: 環境構築
  > **Review A1**: PASS

- [ ] **Todo A2**: 設定ファイル
  > **Review A2**:

### Gate B: 実装

- [ ] **Todo B1**: 機能実装
  > **Review B1**:
`;

    const result = parsePlanFile(content, filePath, projectName);

    expect(result.gates).toEqual([
      {
        id: 'Gate A',
        title: 'セットアップ',
        todos: [
          {
            title: 'Todo A1',
            checked: true,
            hasReview: true,
            reviewFilled: true,
          },
          {
            title: 'Todo A2',
            checked: false,
            hasReview: true,
            reviewFilled: false,
          },
        ],
      },
      {
        id: 'Gate B',
        title: '実装',
        todos: [
          {
            title: 'Todo B1',
            checked: false,
            hasReview: true,
            reviewFilled: false,
          },
        ],
      },
    ]);

    expect(result.todos).toEqual([
      {
        title: 'Todo A1',
        checked: true,
        hasReview: true,
        reviewFilled: true,
      },
      {
        title: 'Todo A2',
        checked: false,
        hasReview: true,
        reviewFilled: false,
      },
      {
        title: 'Todo B1',
        checked: false,
        hasReview: true,
        reviewFilled: false,
      },
    ]);
  });

  it('進捗率をtotal/completed/percentageで計算する', () => {
    const content = `
# テスト計画

### Gate A: セットアップ

- [x] **Todo A1**: 環境構築
  > **Review A1**: PASS

- [ ] **Todo A2**: 設定ファイル
  > **Review A2**:

### Gate B: 実装

- [x] **Todo B1**: 機能実装
  > **Review B1**: PASS

- [ ] **Todo B2**: テスト追加
  > **Review B2**:
`;

    const result = parsePlanFile(content, filePath, projectName);

    expect(result.progress).toEqual({
      total: 4,
      completed: 2,
      percentage: 50,
    });
  });
});
