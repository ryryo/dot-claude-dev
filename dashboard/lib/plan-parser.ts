import path from 'node:path';

import type { Gate, PlanFile, PlanStatus, TodoItem } from './types';

const TITLE_PATTERN = /^# (.+)$/m;
const GATE_PATTERN = /^### (Gate \w+): (.+)$/gm;
const TODO_PATTERN = /^- \[([ x])\] \*\*(.+?)\*\*/gm;
const REVIEW_PATTERN = /^\s*> \*\*Review.+?\*\*:(.*)$/m;
const REVIEW_STATUS_PATTERN = /^## レビューステータス\s*\n[\s\S]*?- \[([ x])\] \*\*レビュー完了\*\*/m;

function parseDateFromFileName(name: string): string | null {
  const match = name.match(/^(\d{6})/);
  if (!match) return null;
  const s = match[1];
  const year = 2000 + parseInt(s.slice(0, 2), 10);
  const month = parseInt(s.slice(2, 4), 10);
  const day = parseInt(s.slice(4, 6), 10);
  if (isNaN(year) || isNaN(month) || isNaN(day)) return null;
  const d = new Date(year, month - 1, day);
  if (d.getFullYear() !== year || d.getMonth() + 1 !== month || d.getDate() !== day) return null;
  return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}

export function parsePlanFile(content: string, filePath: string, projectName: string): PlanFile {
  const fileName = path.basename(filePath);
  const createdDate = fileName.endsWith('.md')
    ? parseDateFromFileName(fileName)
    : parseDateFromFileName(path.basename(path.dirname(filePath)));
  const reviewMatch = REVIEW_STATUS_PATTERN.exec(content);
  const hasReviewSection = reviewMatch !== null;
  const reviewChecked = hasReviewSection && reviewMatch![1] === 'x';
  const title = content.match(TITLE_PATTERN)?.[1] ?? '';
  const gates = parseGates(content);
  const todos = gates.length > 0 ? gates.flatMap((gate) => gate.todos) : parseTodos(content);
  const progress = calculateProgress(todos);

  return {
    filePath,
    fileName,
    projectName,
    title,
    createdDate,
    reviewChecked,
    status: determineStatus(todos, hasReviewSection, reviewChecked),
    gates,
    todos,
    progress,
  };
}

function parseGates(content: string): Gate[] {
  const matches = [...content.matchAll(GATE_PATTERN)];

  return matches.map((match, index) => {
    const section = sliceBlock(content, match.index ?? 0, matches[index + 1]?.index ?? content.length);

    return {
      id: match[1],
      title: match[2],
      todos: parseTodos(section),
    };
  });
}

function parseTodos(content: string): TodoItem[] {
  const matches = [...content.matchAll(TODO_PATTERN)];

  return matches.map((match, index) => {
    const todoBlock = sliceBlock(content, match.index ?? 0, matches[index + 1]?.index ?? content.length);
    const reviewMatch = todoBlock.match(REVIEW_PATTERN);

    return {
      title: match[2],
      checked: match[1] === 'x',
      hasReview: reviewMatch !== null,
      reviewFilled: reviewMatch !== null && reviewMatch[1].trim().length > 0,
    };
  });
}

function calculateProgress(todos: TodoItem[]): PlanFile['progress'] {
  const completed = todos.filter((todo) => todo.checked).length;
  const total = todos.length;

  return {
    total,
    completed,
    percentage: total === 0 ? 0 : Math.round((completed / total) * 100),
  };
}

function determineStatus(
  todos: TodoItem[],
  hasReviewSection: boolean,
  reviewChecked: boolean
): PlanStatus {
  if (todos.length === 0) return 'not-started';
  if (todos.every((todo) => todo.checked)) {
    if (hasReviewSection && !reviewChecked) return 'in-review';
    return 'completed';
  }
  if (todos.some((todo) => !todo.checked && todo.reviewFilled)) return 'in-review';
  if (todos.some((todo) => todo.checked)) return 'in-progress';
  return 'not-started';
}

function sliceBlock(content: string, start: number, end: number): string {
  return content.slice(start, end);
}
