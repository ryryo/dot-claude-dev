import path from 'node:path';
import type {
  Gate,
  PlanFile,
  ReviewResult,
  Step,
  TasksJsonV2,
  TasksJsonV2Step,
  Todo,
} from './types';

export function loadPlanFromTasksJson(
  tasksJson: TasksJsonV2,
  filePath: string,
  projectName: string
): PlanFile {
  const fileName = path.basename(filePath);

  const gates: Gate[] = tasksJson.gates.map((g) => ({
    id: g.id,
    title: g.title,
    todos: tasksJson.todos
      .filter((t) => t.gate === g.id)
      .map((t) => convertTodo(t)),
  }));

  const todos: Todo[] = tasksJson.todos.map((t) => convertTodo(t));

  const total = tasksJson.progress.total;
  const completed = tasksJson.progress.completed;
  const percentage = total === 0 ? 0 : Math.round((completed / total) * 100);

  return {
    filePath,
    fileName,
    projectName,
    title: tasksJson.spec.title,
    createdDate: tasksJson.spec.createdDate || null,
    reviewChecked: tasksJson.reviewChecked,
    status: tasksJson.status,
    gates,
    todos,
    progress: { total, completed, percentage },
    summary: tasksJson.spec.summary,
    rawMarkdown: '',
  };
}

function convertTodo(t: TasksJsonV2['todos'][number]): Todo {
  return {
    title: t.title,
    steps: t.steps.map((s) => convertStep(s, t.description)),
  };
}

function convertStep(s: TasksJsonV2Step, todoDescription: string): Step {
  const base: Step = {
    title: s.title,
    checked: s.checked,
    kind: s.kind,
    description: todoDescription,
    hasReview: s.kind === 'review',
    reviewFilled: false,
    reviewResult: null,
    reviewFixCount: null,
  };

  if (s.kind === 'review' && s.review) {
    base.reviewFilled = true;
    base.reviewResult = s.review.result as ReviewResult;
    base.reviewFixCount = s.review.fixCount;
  }

  return base;
}
