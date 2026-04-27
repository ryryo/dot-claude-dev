import { describe, expect, it } from 'vitest';
import { computeSidebarStats } from '../lib/page-stats';
import type { PlanFile, PlanProgress } from '../lib/types';

function makePlan(
  status: PlanFile['status'],
  gatesTotal: number,
  gatesPassed: number,
  acTotal: number,
  acPassed: number,
): PlanFile {
  const progress: PlanProgress = {
    gatesPassed,
    gatesTotal,
    currentGate: gatesPassed < gatesTotal ? 'A' : null,
    currentGateAC: { passed: acPassed, total: acTotal },
  };
  return {
    filePath: 'docs/PLAN/demo/spec.md',
    fileName: 'spec.md',
    projectName: 'owner/repo',
    title: 'Demo',
    createdDate: '2026-04-27',
    reviewChecked: false,
    status,
    gates: [],
    progress,
    summary: '',
    rawMarkdown: '',
  };
}

describe('computeSidebarStats', () => {
  it('空配列のとき zero 値を返す', () => {
    const stats = computeSidebarStats([]);
    expect(stats).toEqual({
      totalGates: 0,
      passedGates: 0,
      totalCurrentAc: 0,
      passedCurrentAc: 0,
      inProgressCount: 0,
    });
  });

  it('全プラン in-progress のとき全プランの AC を集計する', () => {
    const plans = [
      makePlan('in-progress', 3, 1, 4, 2),
      makePlan('in-progress', 2, 0, 5, 3),
    ];
    const stats = computeSidebarStats(plans);
    expect(stats.totalGates).toBe(5);
    expect(stats.passedGates).toBe(1);
    expect(stats.totalCurrentAc).toBe(9);   // 4 + 5
    expect(stats.passedCurrentAc).toBe(5);  // 2 + 3
    expect(stats.inProgressCount).toBe(2);
  });

  it('全プラン completed のとき AC 集計は 0 になる（totalCurrentAc / passedCurrentAc は in-progress のみ）', () => {
    const plans = [
      makePlan('completed', 3, 3, 3, 3),
      makePlan('completed', 2, 2, 2, 2),
    ];
    const stats = computeSidebarStats(plans);
    expect(stats.totalGates).toBe(5);   // 全プラン Gate は集計
    expect(stats.passedGates).toBe(5);
    expect(stats.totalCurrentAc).toBe(0);   // in-progress なし
    expect(stats.passedCurrentAc).toBe(0);
    expect(stats.inProgressCount).toBe(0);
  });

  it('混在（in-progress + completed + not-started）のとき in-progress のみ AC 集計する', () => {
    const plans = [
      makePlan('in-progress', 3, 1, 6, 3),
      makePlan('completed', 4, 4, 2, 2),
      makePlan('not-started', 2, 0, 4, 0),
      makePlan('in-review', 3, 2, 3, 3),
    ];
    const stats = computeSidebarStats(plans);
    // Gate は全プラン
    expect(stats.totalGates).toBe(12);   // 3 + 4 + 2 + 3
    expect(stats.passedGates).toBe(7);   // 1 + 4 + 0 + 2
    // AC は in-progress (status === 'in-progress') のみ
    expect(stats.totalCurrentAc).toBe(6);
    expect(stats.passedCurrentAc).toBe(3);
    expect(stats.inProgressCount).toBe(1);
  });
});
