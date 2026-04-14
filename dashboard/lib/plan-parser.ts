import path from 'node:path';

import type { Gate, PlanFile, PlanStatus, ReviewResult, Step, StepKind, Todo } from './types';

const TITLE_PATTERN = /^# (.+)$/m;
const GATE_PATTERN = /^### (Gate \w+): (.+)$/gm;
const STEP_BULLET_PATTERN = /^- \[([ x])\] \*\*(.+?)\*\*/gm;
const H4_TODO_PATTERN = /^####\s+(?:Todo\s+\d+:?\s*)?(.+)$/gm;
const STEP_REVIEW_PATTERN = /^Step\s+\d+\s*[—–-]\s*Review\b/;
const REVIEW_STATUS_PATTERN = /^## レビューステータス\s*\n[\s\S]*?- \[([ x])\] \*\*レビュー完了\*\*/m;
const SUMMARY_HEADING_PATTERN = /^## 概要\s*$/m;
const H2_HEADING_PATTERN = /^##\s+/m;
const CODE_FENCE_PATTERN = /```[\s\S]*?```/g;

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
  const todos = gates.length > 0 ? gates.flatMap((gate) => gate.todos) : parseGateTodos(content);
  const progress = calculateProgress(todos);
  const summary = parseSummary(content);

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
    summary,
    rawMarkdown: content,
    hasV2Tasks: false,
  };
}

function parseSummary(content: string): string {
  const scanTarget = maskCodeFences(content);
  const summaryHeadingMatch = SUMMARY_HEADING_PATTERN.exec(scanTarget);

  if (summaryHeadingMatch && summaryHeadingMatch.index !== undefined) {
    const sectionStart = summaryHeadingMatch.index + summaryHeadingMatch[0].length;
    const remainingContent = content.slice(sectionStart);
    const remainingScanTarget = scanTarget.slice(sectionStart);
    const nextHeadingMatch = H2_HEADING_PATTERN.exec(remainingScanTarget);
    const summaryMarkdown = nextHeadingMatch
      ? remainingContent.slice(0, nextHeadingMatch.index)
      : remainingContent;
    const strippedSummary = stripMarkdown(summaryMarkdown);

    if (strippedSummary) {
      return strippedSummary;
    }
  }

  const titleMatch = TITLE_PATTERN.exec(scanTarget);

  if (!titleMatch || titleMatch.index === undefined) {
    return '';
  }

  const introStart = titleMatch.index + titleMatch[0].length;
  const remainingContent = content.slice(introStart);
  const remainingScanTarget = scanTarget.slice(introStart);
  const nextHeadingMatch = H2_HEADING_PATTERN.exec(remainingScanTarget);

  if (!nextHeadingMatch || nextHeadingMatch.index === undefined) {
    return '';
  }

  const introMarkdown = remainingContent.slice(0, nextHeadingMatch.index);

  return stripMarkdown(introMarkdown);
}

function maskCodeFences(content: string): string {
  return content.replace(CODE_FENCE_PATTERN, (match) => match.replace(/[^\n]/g, ' '));
}

export function extractStepDescription(stepBlock: string): string {
  const contentMatch = stepBlock.match(/^\s*-\s*\*\*内容\*\*[:：]\s*(.+)$/m);
  if (contentMatch) return stripMarkdown(contentMatch[1]).trim();

  const implMatch = stepBlock.match(/^\s*-\s*\*\*実装詳細\*\*[:：]\s*(.+)$/m);
  if (implMatch) return firstSentence(stripMarkdown(implMatch[1]));

  const targetMatch = stepBlock.match(/^\s*-\s*\*\*対象\*\*[:：]\s*(.+)$/m);
  if (targetMatch) return stripMarkdown(targetMatch[1]).trim();

  const firstBulletMatch = stepBlock.match(
    /^\s*-\s+(?!\[[ xX]\]|\*\*(?:内容|実装詳細|対象|依存|\[TDD\])\*\*)(.+)$/m
  );
  if (firstBulletMatch) return stripMarkdown(firstBulletMatch[1]).trim();

  return '';
}

function firstSentence(text: string): string {
  const match = text.match(/^(.*?[。.!?！？])/);
  return (match ? match[1] : text).trim();
}

const REVIEW_FIRST_LINE_PATTERN = /^\s*>\s*\*\*Review\s+[\w\d]+\*\*[:：][^\S\n]*(.*)$/m;
const REVIEW_RESULT_PATTERN = /(PASSED|FAILED|SKIPPED|IN[_\s-]?PROGRESS)/i;
const REVIEW_FIX_COUNT_PATTERN = /FIX\s*(\d+)\s*回/;
const COMMIT_HASH_PATTERN = /\b(?:commit|commits)\s+[0-9a-f,\s]+/gi;

export function parseReviewBlockquote(stepBlock: string): {
  hasReview: boolean;
  reviewFilled: boolean;
  reviewResult: ReviewResult | null;
  reviewFixCount: number | null;
  summary: string;
} {
  const firstLineMatch = stepBlock.match(REVIEW_FIRST_LINE_PATTERN);
  if (!firstLineMatch) {
    return {
      hasReview: false,
      reviewFilled: false,
      reviewResult: null,
      reviewFixCount: null,
      summary: '',
    };
  }

  const firstLineBody = firstLineMatch[1];
  if (firstLineBody.trim() === '') {
    return {
      hasReview: true,
      reviewFilled: false,
      reviewResult: null,
      reviewFixCount: null,
      summary: '',
    };
  }

  const statusMatch = firstLineBody.match(REVIEW_RESULT_PATTERN);
  const reviewResult = statusMatch
    ? (statusMatch[1].toUpperCase().replace(/[\s-]/g, '_') as ReviewResult)
    : null;

  const fixMatch = firstLineBody.match(REVIEW_FIX_COUNT_PATTERN);
  const reviewFixCount = fixMatch ? parseInt(fixMatch[1], 10) : null;

  let summary = '';
  const emdashIdx = firstLineBody.search(/\s[—–-]\s/);
  if (emdashIdx >= 0) {
    summary = firstLineBody.slice(emdashIdx + 2).trim();
  }
  if (!summary) {
    const secondLineBullet = stepBlock.match(/^\s*>\s*-\s+(.+)$/m);
    if (secondLineBullet) summary = secondLineBullet[1].trim();
  }

  summary = summary
    .replace(COMMIT_HASH_PATTERN, '')
    .replace(/\s{2,}/g, ' ')
    .replace(/[\s—–-]+$/, '')
    .trim();
  summary = stripMarkdown(summary);

  return {
    hasReview: true,
    reviewFilled: true,
    reviewResult,
    reviewFixCount,
    summary,
  };
}

function stripMarkdown(content: string): string {
  return content
    .replace(/```[\s\S]*?```/g, (block) =>
      block
        .replace(/^```[\w-]*\n?/, '')
        .replace(/\n?```$/, '')
    )
    .replace(/!\[([^\]]*)\]\([^)]+\)/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/(\*\*|__)(.*?)\1/g, '$2')
    .replace(/(\*|_)(.*?)\1/g, '$2')
    .replace(/^>\s?/gm, '')
    .replace(/^[-*+]\s+/gm, '')
    .replace(/^\d+\.\s+/gm, '')
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/\r/g, '')
    .split('\n')
    .map((line) => line.trim())
    .join('\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

function parseGates(content: string): Gate[] {
  const matches = [...content.matchAll(GATE_PATTERN)];

  return matches.map((match, index) => {
    const section = sliceBlock(content, match.index ?? 0, matches[index + 1]?.index ?? content.length);

    return {
      id: match[1],
      title: match[2],
      todos: parseGateTodos(section),
    };
  });
}

function parseGateTodos(gateContent: string): Todo[] {
  const masked = maskCodeFences(gateContent);
  const h4Matches = [...masked.matchAll(H4_TODO_PATTERN)];

  if (h4Matches.length === 0) {
    const steps = parseSteps(gateContent);
    return steps.map((step) => ({ title: step.title, steps: [step] }));
  }

  return h4Matches.map((match, index) => {
    const sectionStart = match.index ?? 0;
    const sectionEnd = h4Matches[index + 1]?.index ?? gateContent.length;
    const sectionContent = gateContent.slice(sectionStart, sectionEnd);

    return {
      title: match[1].trim(),
      steps: parseSteps(sectionContent),
    };
  });
}

const REVIEW_COMPLETION_TITLE = 'レビュー完了';

function parseSteps(content: string): Step[] {
  const matches = [...content.matchAll(STEP_BULLET_PATTERN)];

  return matches
    .filter((match) => {
      const title = match[2];
      return !title.startsWith(REVIEW_COMPLETION_TITLE);
    })
    .map((match, index, filteredMatches) => {
      const stepBlock = sliceBlock(content, match.index ?? 0, filteredMatches[index + 1]?.index ?? content.length);
      const title = match[2];
      const kind: StepKind = STEP_REVIEW_PATTERN.test(title) ? 'review' : 'impl';
      const description = extractStepDescription(stepBlock);
      const review = parseReviewBlockquote(stepBlock);

      return {
        title,
        checked: match[1] === 'x',
        kind,
        description,
        hasReview: review.hasReview,
        reviewFilled: review.reviewFilled,
        reviewResult: review.reviewResult,
        reviewFixCount: review.reviewFixCount,
      };
    });
}

function calculateProgress(todos: Todo[]): PlanFile['progress'] {
  const allSteps = todos.flatMap((todo) => todo.steps);
  const completed = allSteps.filter((step) => step.checked).length;
  const total = allSteps.length;

  return {
    total,
    completed,
    percentage: total === 0 ? 0 : Math.round((completed / total) * 100),
  };
}

function determineStatus(
  todos: Todo[],
  hasReviewSection: boolean,
  reviewChecked: boolean
): PlanStatus {
  const allSteps = todos.flatMap((todo) => todo.steps);
  if (allSteps.length === 0) return 'not-started';
  if (allSteps.every((step) => step.checked)) {
    if (hasReviewSection && !reviewChecked) return 'in-review';
    return 'completed';
  }
  if (allSteps.some((step) => !step.checked && step.reviewFilled)) return 'in-review';
  if (allSteps.some((step) => step.checked)) return 'in-progress';
  return 'not-started';
}

function sliceBlock(content: string, start: number, end: number): string {
  return content.slice(start, end);
}
