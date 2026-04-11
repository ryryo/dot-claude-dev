import type { PlanFile } from './types';

export interface PlanSize {
  gateCount: number;
  todoCount: number;
  total: number;
}

/**
 * Plan の全体規模を返す。完了状態は考慮しない。
 * total = gates.length + todos.length
 */
export function getPlanSize(plan: PlanFile): PlanSize {
  const gateCount = plan.gates.length;
  const todoCount = plan.todos.length;
  return {
    gateCount,
    todoCount,
    total: gateCount + todoCount,
  };
}

export type SizeBin = 'S' | 'M' | 'L' | 'XL';

export const SIZE_BIN_LABEL: Record<SizeBin, string> = {
  S: 'S (1-3)',
  M: 'M (4-7)',
  L: 'L (8-15)',
  XL: 'XL (16+)',
};

/**
 * 規模 total を S/M/L/XL のビンに分類する。
 * total <= 3  → 'S'
 * total <= 7  → 'M'
 * total <= 15 → 'L'
 * total >= 16 → 'XL'
 * total <= 0 の場合も S とする（仕様簡略化）。
 */
export function getSizeBin(total: number): SizeBin {
  if (total <= 3) return 'S';
  if (total <= 7) return 'M';
  if (total <= 15) return 'L';
  return 'XL';
}
