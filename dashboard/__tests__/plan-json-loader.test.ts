import { describe, expect, it } from 'vitest';
import { computeProgress, loadPlanFromTasksJson } from '../lib/plan-json-loader';
import type { Gate, TasksJsonV3 } from '../lib/types';

function makeSample(): TasksJsonV3 {
  return {
    schemaVersion: 3,
    spec: {
      slug: 'demo',
      title: 'デモ仕様書',
      summary: 'デモ機能の実装',
      createdDate: '2026-04-12',
      specPath: 'spec.md',
    },
    status: 'in-progress',
    reviewChecked: false,
    progress: {
      gatesPassed: 1,
      gatesTotal: 2,
      currentGate: 'B',
      currentGateAC: { passed: 1, total: 3 },
    },
    preflight: [],
    gates: [
      {
        id: 'A',
        title: 'データ層',
        summary: 'スキーマ整備',
        dependencies: [],
        goal: { what: 'items を CRUD できる', why: '後続 API の前提' },
        constraints: { must: ['drizzle-orm を使う'], mustNot: ['既存テーブルを変更しない'] },
        acceptanceCriteria: [
          { id: 'A.AC1', description: 'type-check 0 errors', checked: true },
          { id: 'A.AC2', description: 'unit test GREEN', checked: true },
        ],
        todos: [
          {
            id: 'A1',
            gate: 'A',
            title: '[TDD] items スキーマ',
            tdd: true,
            dependencies: [],
            affectedFiles: [{ path: 'db/schema/items.ts', operation: 'create', summary: 'items テーブル' }],
          },
        ],
        review: { result: 'PASSED', fixCount: 0, summary: 'OK' },
        passed: true,
      },
      {
        id: 'B',
        title: 'API 層',
        summary: 'POST /api',
        dependencies: ['A'],
        goal: { what: 'API ハンドラ', why: 'クライアント連携' },
        constraints: { must: [], mustNot: [] },
        acceptanceCriteria: [
          { id: 'B.AC1', description: 'POST 200 を返す', checked: true },
          { id: 'B.AC2', description: 'バリデーション動作', checked: false },
          { id: 'B.AC3', description: 'E2E test', checked: false },
        ],
        todos: [
          {
            id: 'B1',
            gate: 'B',
            title: 'POST /api ハンドラ',
            tdd: false,
            dependencies: ['A1'],
            affectedFiles: [{ path: 'app/api/items/route.ts', operation: 'create', summary: 'POST ハンドラ' }],
          },
        ],
        review: null,
        passed: false,
      },
    ],
    metadata: { createdAt: '2026-04-27T00:00:00Z', totalGates: 2, totalTodos: 2 },
  };
}

describe('loadPlanFromTasksJson (v3)', () => {
  it('spec メタデータを PlanFile にマッピングする', () => {
    const plan = loadPlanFromTasksJson(makeSample(), 'docs/PLAN/demo/spec.md', 'owner/repo', '');
    expect(plan.title).toBe('デモ仕様書');
    expect(plan.summary).toBe('デモ機能の実装');
    expect(plan.createdDate).toBe('2026-04-12');
    expect(plan.projectName).toBe('owner/repo');
    expect(plan.filePath).toBe('docs/PLAN/demo/spec.md');
    expect(plan.fileName).toBe('spec.md');
  });

  it('status / reviewChecked をそのまま引き継ぐ', () => {
    const plan = loadPlanFromTasksJson(makeSample(), 'docs/PLAN/demo/spec.md', 'owner/repo', '');
    expect(plan.status).toBe('in-progress');
    expect(plan.reviewChecked).toBe(false);
  });

  it('progress を v3 シェイプ (gatesPassed/gatesTotal/currentGate/currentGateAC) で展開する', () => {
    const plan = loadPlanFromTasksJson(makeSample(), 'docs/PLAN/demo/spec.md', 'owner/repo', '');
    expect(plan.progress).toEqual({
      gatesPassed: 1,
      gatesTotal: 2,
      currentGate: 'B',
      currentGateAC: { passed: 1, total: 3 },
    });
  });

  it('Gate ごとに goal/constraints/acceptanceCriteria/review/passed/todos を保持する', () => {
    const plan = loadPlanFromTasksJson(makeSample(), 'docs/PLAN/demo/spec.md', 'owner/repo', '');
    expect(plan.gates).toHaveLength(2);

    const a = plan.gates[0];
    expect(a.id).toBe('A');
    expect(a.goal).toEqual({ what: 'items を CRUD できる', why: '後続 API の前提' });
    expect(a.constraints.must).toEqual(['drizzle-orm を使う']);
    expect(a.constraints.mustNot).toEqual(['既存テーブルを変更しない']);
    expect(a.acceptanceCriteria).toHaveLength(2);
    expect(a.acceptanceCriteria[0]).toEqual({ id: 'A.AC1', description: 'type-check 0 errors', checked: true });
    expect(a.review).toEqual({ result: 'PASSED', fixCount: 0, summary: 'OK' });
    expect(a.passed).toBe(true);
    expect(a.todos).toHaveLength(1);
    expect(a.todos[0].title).toBe('[TDD] items スキーマ');
  });

  it('review が null の Gate はそのまま null を保持する', () => {
    const plan = loadPlanFromTasksJson(makeSample(), 'docs/PLAN/demo/spec.md', 'owner/repo', '');
    expect(plan.gates[1].review).toBeNull();
    expect(plan.gates[1].passed).toBe(false);
  });

  it('Todo は軽量シェイプ (id/gate/title/tdd/dependencies/affectedFiles) を保持する', () => {
    const plan = loadPlanFromTasksJson(makeSample(), 'docs/PLAN/demo/spec.md', 'owner/repo', '');
    const todo = plan.gates[0].todos[0];
    expect(todo).toEqual({
      id: 'A1',
      gate: 'A',
      title: '[TDD] items スキーマ',
      tdd: true,
      dependencies: [],
      affectedFiles: [{ path: 'db/schema/items.ts', operation: 'create', summary: 'items テーブル' }],
    });
  });

  it('rawMarkdown に渡した spec.md 内容がそのまま格納される', () => {
    const specContent = '# Demo Spec\n\nThis is the spec.';
    const plan = loadPlanFromTasksJson(makeSample(), 'docs/PLAN/demo/spec.md', 'owner/repo', specContent);
    expect(plan.rawMarkdown).toBe(specContent);
  });
});

function makeGate(id: string, passed: boolean, acChecked: number, acTotal: number): Gate {
  const acceptanceCriteria = Array.from({ length: acTotal }, (_, i) => ({
    id: `${id}.AC${i + 1}`,
    description: `AC ${i + 1}`,
    checked: i < acChecked,
  }));
  return {
    id,
    title: `Gate ${id}`,
    summary: '',
    dependencies: [],
    goal: { what: '', why: '' },
    constraints: { must: [], mustNot: [] },
    acceptanceCriteria,
    todos: [],
    review: null,
    passed,
  };
}

describe('computeProgress', () => {
  it('gates が空のとき zero 値を返す', () => {
    expect(computeProgress([])).toEqual({
      gatesPassed: 0,
      gatesTotal: 0,
      currentGate: null,
      currentGateAC: { passed: 0, total: 0 },
    });
  });

  it('全 Gate が passed === false のとき最初の Gate を currentGate にする', () => {
    const gates = [makeGate('A', false, 1, 3), makeGate('B', false, 0, 2)];
    expect(computeProgress(gates)).toEqual({
      gatesPassed: 0,
      gatesTotal: 2,
      currentGate: 'A',
      currentGateAC: { passed: 1, total: 3 },
    });
  });

  it('一部 passed のとき最初の passed === false の Gate を currentGate にする', () => {
    const gates = [makeGate('A', true, 2, 2), makeGate('B', false, 1, 3)];
    expect(computeProgress(gates)).toEqual({
      gatesPassed: 1,
      gatesTotal: 2,
      currentGate: 'B',
      currentGateAC: { passed: 1, total: 3 },
    });
  });

  it('全 Gate が passed === true のとき currentGate: null で最後の Gate の AC を返す', () => {
    const gates = [makeGate('A', true, 2, 2), makeGate('B', true, 5, 5)];
    expect(computeProgress(gates)).toEqual({
      gatesPassed: 2,
      gatesTotal: 2,
      currentGate: null,
      currentGateAC: { passed: 5, total: 5 },
    });
  });
});
