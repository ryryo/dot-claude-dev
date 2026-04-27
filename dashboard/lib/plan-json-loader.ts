import path from 'node:path';
import type {
  AcceptanceCriteria,
  AffectedFile,
  Gate,
  GateReview,
  PlanFile,
  PlanProgress,
  TasksJsonV3,
  TasksJsonV3Gate,
  TasksJsonV3Todo,
  Todo,
} from './types';

export function loadPlanFromTasksJson(
  tasksJson: TasksJsonV3,
  filePath: string,
  projectName: string,
  rawMarkdown: string,
): PlanFile {
  const fileName = path.basename(filePath);

  const gates: Gate[] = tasksJson.gates.map((g) => convertGate(g));

  return {
    filePath,
    fileName,
    projectName,
    title: tasksJson.spec.title,
    createdDate: tasksJson.spec.createdDate || null,
    reviewChecked: tasksJson.reviewChecked,
    status: tasksJson.status,
    gates,
    progress: convertProgress(tasksJson.progress),
    summary: tasksJson.spec.summary,
    rawMarkdown,
  };
}

function convertGate(g: TasksJsonV3Gate): Gate {
  return {
    id: g.id,
    title: g.title,
    summary: g.summary,
    dependencies: g.dependencies,
    goal: { what: g.goal.what, why: g.goal.why },
    constraints: {
      must: [...g.constraints.must],
      mustNot: [...g.constraints.mustNot],
    },
    acceptanceCriteria: g.acceptanceCriteria.map(
      (ac): AcceptanceCriteria => ({
        id: ac.id,
        description: ac.description,
        checked: ac.checked,
      }),
    ),
    todos: g.todos.map((t) => convertTodo(t)),
    review: g.review
      ? ({
          result: g.review.result,
          fixCount: g.review.fixCount,
          summary: g.review.summary,
        } satisfies GateReview)
      : null,
    passed: g.passed,
  };
}

function convertTodo(t: TasksJsonV3Todo): Todo {
  return {
    id: t.id,
    gate: t.gate,
    title: t.title,
    tdd: t.tdd,
    dependencies: [...t.dependencies],
    affectedFiles: t.affectedFiles.map(
      (f): AffectedFile => ({
        path: f.path,
        operation: f.operation,
        summary: f.summary,
      }),
    ),
  };
}

function convertProgress(p: TasksJsonV3['progress']): PlanProgress {
  return {
    gatesPassed: p.gatesPassed,
    gatesTotal: p.gatesTotal,
    currentGate: p.currentGate ?? null,
    currentGateAC: { passed: p.currentGateAC.passed, total: p.currentGateAC.total },
  };
}
