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
