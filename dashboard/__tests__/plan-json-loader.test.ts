import { describe, expect, it } from 'vitest';
import { loadPlanFromTasksJson } from '../lib/plan-json-loader';
import type { TasksJsonV2 } from '../lib/types';

function makeSample(): TasksJsonV2 {
  return {
    schemaVersion: 2,
    spec: {
      slug: 'demo',
      title: 'デモ仕様書',
      summary: 'デモ機能の実装',
      createdDate: '2026-04-12',
      specPath: 'spec.md',
    },
    status: 'in-progress',
    reviewChecked: false,
    progress: { completed: 2, total: 4 },
    preflight: [],
    gates: [
      {
        id: 'A',
        title: 'データ層',
        description: 'スキーマ整備',
        dependencies: [],
        passCondition: '全 Review PASS',
      },
      {
        id: 'B',
        title: 'API 層',
        description: '',
        dependencies: ['A'],
        passCondition: '全 Review PASS',
      },
    ],
    todos: [
      {
        id: 'A1',
        gate: 'A',
        title: '[TDD] スキーマ定義',
        description: 'items テーブルを作成',
        tdd: true,
        dependencies: [],
        affectedFiles: [],
        impl: '...',
        relatedIssues: [],
        steps: [
          { kind: 'impl', title: 'Step 1 — IMPL', checked: true },
          { kind: 'review', title: 'Step 2 — Review', checked: true, review: { result: 'PASSED', fixCount: 0, summary: 'OK' } },
        ],
      },
      {
        id: 'B1',
        gate: 'B',
        title: 'POST /api',
        description: 'ハンドラ実装',
        tdd: false,
        dependencies: ['A1'],
        affectedFiles: [],
        impl: '...',
        relatedIssues: [],
        steps: [
          { kind: 'impl', title: 'Step 1 — IMPL', checked: false },
          { kind: 'review', title: 'Step 2 — Review', checked: false, review: null },
        ],
      },
    ],
    metadata: { createdAt: '', totalGates: 2, totalTodos: 2 },
  };
}

describe('loadPlanFromTasksJson', () => {
  it('spec メタデータを PlanFile にマッピングする', () => {
    const plan = loadPlanFromTasksJson(makeSample(), 'docs/PLAN/demo/spec.md', 'owner/repo');
    expect(plan.title).toBe('デモ仕様書');
    expect(plan.summary).toBe('デモ機能の実装');
    expect(plan.createdDate).toBe('2026-04-12');
    expect(plan.projectName).toBe('owner/repo');
    expect(plan.filePath).toBe('docs/PLAN/demo/spec.md');
    expect(plan.fileName).toBe('spec.md');
  });

  it('status / reviewChecked をそのまま引き継ぐ', () => {
    const plan = loadPlanFromTasksJson(makeSample(), 'docs/PLAN/demo/spec.md', 'owner/repo');
    expect(plan.status).toBe('in-progress');
    expect(plan.reviewChecked).toBe(false);
  });

  it('progress を percentage 付きで計算する', () => {
    const plan = loadPlanFromTasksJson(makeSample(), 'docs/PLAN/demo/spec.md', 'owner/repo');
    expect(plan.progress).toEqual({ completed: 2, total: 4, percentage: 50 });
  });

  it('Gate ごとに Todo を紐付ける', () => {
    const plan = loadPlanFromTasksJson(makeSample(), 'docs/PLAN/demo/spec.md', 'owner/repo');
    expect(plan.gates).toHaveLength(2);
    expect(plan.gates[0].id).toBe('A');
    expect(plan.gates[0].todos).toHaveLength(1);
    expect(plan.gates[0].todos[0].title).toBe('[TDD] スキーマ定義');
    expect(plan.gates[1].todos[0].title).toBe('POST /api');
  });

  it('各 Todo に impl step と review step を生成する', () => {
    const plan = loadPlanFromTasksJson(makeSample(), 'docs/PLAN/demo/spec.md', 'owner/repo');
    const todoA = plan.gates[0].todos[0];
    expect(todoA.steps).toHaveLength(2);
    expect(todoA.steps[0].kind).toBe('impl');
    expect(todoA.steps[0].checked).toBe(true);
    expect(todoA.steps[1].kind).toBe('review');
    expect(todoA.steps[1].checked).toBe(true);
    expect(todoA.steps[1].hasReview).toBe(true);
    expect(todoA.steps[1].reviewFilled).toBe(true);
    expect(todoA.steps[1].reviewResult).toBe('PASSED');
    expect(todoA.steps[1].reviewFixCount).toBe(0);
  });

  it('Review 未記入のとき reviewFilled: false', () => {
    const plan = loadPlanFromTasksJson(makeSample(), 'docs/PLAN/demo/spec.md', 'owner/repo');
    const todoB = plan.gates[1].todos[0];
    expect(todoB.steps[1].hasReview).toBe(true);
    expect(todoB.steps[1].reviewFilled).toBe(false);
    expect(todoB.steps[1].reviewResult).toBeNull();
  });

  it('description は Todo レベルの description を Step に展開', () => {
    const plan = loadPlanFromTasksJson(makeSample(), 'docs/PLAN/demo/spec.md', 'owner/repo');
    const todoA = plan.gates[0].todos[0];
    expect(todoA.steps[0].description).toBe('items テーブルを作成');
  });

  it('todos (flat list) も Gate と同じ順序で取得できる', () => {
    const plan = loadPlanFromTasksJson(makeSample(), 'docs/PLAN/demo/spec.md', 'owner/repo');
    expect(plan.todos).toHaveLength(2);
    expect(plan.todos[0].title).toBe('[TDD] スキーマ定義');
    expect(plan.todos[1].title).toBe('POST /api');
  });

  it('completed 状態の場合 percentage: 100', () => {
    const data = makeSample();
    data.status = 'completed';
    data.progress = { completed: 4, total: 4 };
    data.todos[1].steps[0].checked = true;
    data.todos[1].steps[1].checked = true;
    data.todos[1].steps[1].review = { result: 'PASSED', fixCount: 1, summary: '修正後 OK' };
    const plan = loadPlanFromTasksJson(data, 'docs/PLAN/demo/spec.md', 'owner/repo');
    expect(plan.progress.percentage).toBe(100);
    expect(plan.status).toBe('completed');
  });

  it('total 0 のとき percentage: 0', () => {
    const data = makeSample();
    data.progress = { completed: 0, total: 0 };
    data.todos = [];
    data.gates = [];
    const plan = loadPlanFromTasksJson(data, 'docs/PLAN/demo/spec.md', 'owner/repo');
    expect(plan.progress.percentage).toBe(0);
  });

  it('rawMarkdown は空文字（v2 は JSON 起点）', () => {
    const plan = loadPlanFromTasksJson(makeSample(), 'docs/PLAN/demo/spec.md', 'owner/repo');
    expect(plan.rawMarkdown).toBe('');
  });
});
