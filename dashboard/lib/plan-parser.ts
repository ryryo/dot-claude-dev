import { basename } from 'node:path';

import type { Gate, PlanFile, PlanStatus, TodoItem } from './types';

const TITLE_PATTERN = /^# (.+)$/m;
const GATE_PATTERN = /^### (Gate \w+): (.+)$/gm;
const TODO_PATTERN = /^- \[([ x])\] \*\*(.+?)\*\*/gm;
const REVIEW_PATTERN = /^\s*> \*\*Review.+?\*\*:(.*)$/m;

export function parsePlanFile(content: string, filePath: string, projectName: string): PlanFile {
  const title = content.match(TITLE_PATTERN)?.[1] ?? '';
  const gates = parseGates(content);
  const todos = gates.length > 0 ? gates.flatMap((gate) => gate.todos) : parseTodos(content);
  const progress = calculateProgress(todos);

  return {
    filePath,
    fileName: basename(filePath),
    projectName,
    title,
    status: determineStatus(todos),
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

function determineStatus(todos: TodoItem[]): PlanStatus {
  if (todos.length === 0) {
    return 'not-started';
  }

  if (todos.every((todo) => todo.checked)) {
    return 'completed';
  }

  if (todos.some((todo) => !todo.checked && todo.reviewFilled)) {
    return 'in-review';
  }

  if (todos.some((todo) => todo.checked) && todos.some((todo) => !todo.checked)) {
    return 'in-progress';
  }

  return 'not-started';
}

function sliceBlock(content: string, start: number, end: number): string {
  return content.slice(start, end);
}
