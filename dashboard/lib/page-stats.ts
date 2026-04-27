import type { PlanFile } from './types';

export interface SidebarStats {
  totalGates: number;
  passedGates: number;
  totalCurrentAc: number;
  passedCurrentAc: number;
  inProgressCount: number;
}

/**
 * Computes sidebar statistics from a list of plans.
 *
 * - totalGates / passedGates: aggregated across ALL plans (overall Gate progress)
 * - totalCurrentAc / passedCurrentAc: aggregated only from plans with status === 'in-progress'
 *   (sidebar "current Gate AC progress" reflects active workload, not completed/not-started plans)
 * - inProgressCount: number of plans with status === 'in-progress'
 *
 * Percent calculations (overallProgress / acProgress) are intentionally NOT included here;
 * callers should derive them from the raw fields: Math.round((passed / total) * 100)
 */
export function computeSidebarStats(plans: PlanFile[]): SidebarStats {
  let totalGates = 0;
  let passedGates = 0;
  let totalCurrentAc = 0;
  let passedCurrentAc = 0;
  let inProgressCount = 0;

  for (const plan of plans) {
    totalGates += plan.progress.gatesTotal;
    passedGates += plan.progress.gatesPassed;

    if (plan.status === 'in-progress') {
      totalCurrentAc += plan.progress.currentGateAC.total;
      passedCurrentAc += plan.progress.currentGateAC.passed;
      inProgressCount += 1;
    }
  }

  return { totalGates, passedGates, totalCurrentAc, passedCurrentAc, inProgressCount };
}
