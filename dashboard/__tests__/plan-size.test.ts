import { describe, expect, it } from 'vitest';
import { getPlanSize, getSizeBin, getSizeHistogram } from '../lib/plan-size';
import type { Gate, PlanFile, Todo } from '../lib/types';

function makeTodo(id: string, gate: string): Todo {
  return {
    id,
    gate,
    title: id,
    tdd: false,
    dependencies: [],
    affectedFiles: [],
  };
}

function makeGate(id: string, todos: Todo[]): Gate {
  return {
    id,
    title: id,
    summary: '',
    dependencies: [],
    goal: { what: '', why: '' },
    constraints: { must: [], mustNot: [] },
    acceptanceCriteria: [],
    todos,
    review: null,
    passed: false,
  };
}

function makePlan(overrides: Partial<PlanFile> = {}): PlanFile {
  return {
    filePath: 'p.md',
    fileName: 'p.md',
    projectName: 'proj',
    title: 't',
    createdDate: null,
    reviewChecked: false,
    status: 'not-started',
    gates: [],
    progress: {
      gatesPassed: 0,
      gatesTotal: 0,
      currentGate: null,
      currentGateAC: { passed: 0, total: 0 },
    },
    summary: '',
    rawMarkdown: '',
    ...overrides,
  };
}

describe('getPlanSize', () => {
  it('Gate も Todo もない場合は total=0', () => {
    expect(getPlanSize(makePlan())).toEqual({ gateCount: 0, todoCount: 0, total: 0 });
  });

  it('Gate と Todo の合計を返す', () => {
    const plan = makePlan({
      gates: [
        makeGate('A', [makeTodo('A1', 'A'), makeTodo('A2', 'A')]),
        makeGate('B', [makeTodo('B1', 'B')]),
      ],
    });
    expect(getPlanSize(plan)).toEqual({ gateCount: 2, todoCount: 3, total: 5 });
  });

  it('完了状態に関わらず全 Todo を数える', () => {
    const plan = makePlan({
      gates: [
        { ...makeGate('A', [makeTodo('A1', 'A'), makeTodo('A2', 'A')]), passed: true },
      ],
    });
    expect(getPlanSize(plan).total).toBe(3);
  });
});

describe('getSizeBin', () => {
  it('境界値', () => {
    expect(getSizeBin(0)).toBe('S');
    expect(getSizeBin(1)).toBe('S');
    expect(getSizeBin(3)).toBe('S');
    expect(getSizeBin(4)).toBe('M');
    expect(getSizeBin(7)).toBe('M');
    expect(getSizeBin(8)).toBe('L');
    expect(getSizeBin(15)).toBe('L');
    expect(getSizeBin(16)).toBe('XL');
    expect(getSizeBin(100)).toBe('XL');
  });
});

describe('getSizeHistogram', () => {
  it('空配列はすべて 0', () => {
    expect(getSizeHistogram([])).toEqual({ S: 0, M: 0, L: 0, XL: 0 });
  });

  it('複数 Plan を正しく集計', () => {
    const small = makePlan({
      gates: [makeGate('A', [makeTodo('A1', 'A')])],
    }); // total=2 → S
    const mid = makePlan({
      gates: [
        makeGate('A', [makeTodo('A1', 'A'), makeTodo('A2', 'A')]),
        makeGate('B', [makeTodo('B1', 'B'), makeTodo('B2', 'B')]),
      ],
    }); // total=6 → M
    const big = makePlan({
      gates: Array.from({ length: 4 }, (_, i) =>
        makeGate(`G${i}`, Array.from({ length: 3 }, (_, j) => makeTodo(`G${i}-${j}`, `G${i}`))),
      ),
    }); // total=16 → XL
    expect(getSizeHistogram([small, mid, big])).toEqual({ S: 1, M: 1, L: 0, XL: 1 });
  });
});
