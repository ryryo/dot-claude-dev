import { describe, expect, it } from 'vitest';
import { getPlanSize, getSizeBin, getSizeHistogram } from '../lib/plan-size';
import type { PlanFile } from '../lib/types';

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
    todos: [],
    progress: { total: 0, completed: 0, percentage: 0 },
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
        { id: 'A', title: 'a', todos: [] },
        { id: 'B', title: 'b', todos: [] },
      ],
      todos: [
        { title: 't1', steps: [] },
        { title: 't2', steps: [] },
        { title: 't3', steps: [] },
      ],
    });
    expect(getPlanSize(plan)).toEqual({ gateCount: 2, todoCount: 3, total: 5 });
  });

  it('完了状態に関わらず全 Todo を数える', () => {
    const plan = makePlan({
      gates: [{ id: 'A', title: 'a', todos: [] }],
      todos: [
        { title: 't1', steps: [{ title: 's', checked: true, kind: 'impl', description: '', hasReview: false, reviewFilled: false, reviewResult: null, reviewFixCount: null }] },
        { title: 't2', steps: [{ title: 's', checked: false, kind: 'impl', description: '', hasReview: false, reviewFilled: false, reviewResult: null, reviewFixCount: null }] },
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
    const small = makePlan({ todos: [{ title: 't', steps: [] }] }); // total=1 → S
    const mid = makePlan({
      gates: [
        { id: 'A', title: 'a', todos: [] },
        { id: 'B', title: 'b', todos: [] },
      ],
      todos: Array.from({ length: 4 }, () => ({ title: 't', steps: [] })),
    }); // total=6 → M
    const big = makePlan({
      gates: Array.from({ length: 4 }, (_, i) => ({ id: `G${i}`, title: 'g', todos: [] })),
      todos: Array.from({ length: 12 }, () => ({ title: 't', steps: [] })),
    }); // total=16 → XL
    expect(getSizeHistogram([small, mid, big])).toEqual({ S: 1, M: 1, L: 0, XL: 1 });
  });
});
