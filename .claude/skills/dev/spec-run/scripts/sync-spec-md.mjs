#!/usr/bin/env node
// @ts-check
import { readFileSync, writeFileSync, existsSync, realpathSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const BEGIN_MARKER = '<!-- generated:begin -->';
const END_MARKER = '<!-- generated:end -->';

/**
 * tasks.json (v2) から spec.md の generated 領域の文字列を生成する pure 関数
 * @param {any} tasksJson
 * @returns {string}
 */
export function generateTaskListSection(tasksJson) {
  const lines = [];
  lines.push('<!-- このセクションは sync-spec-md が tasks.json から自動生成します。-->');
  lines.push('<!-- 手動編集は反映されません。変更は tasks.json に対して行ってください。-->');
  lines.push('');
  lines.push('### 依存関係図');
  lines.push('');
  lines.push('```');
  for (const gate of tasksJson.gates ?? []) {
    const deps = (gate.dependencies ?? []).join(', ');
    const suffix = deps ? `（Gate ${deps} 完了後）` : '';
    lines.push(`Gate ${gate.id}: ${gate.title}${suffix}`);
  }
  lines.push('```');
  lines.push('');

  for (const gate of tasksJson.gates ?? []) {
    lines.push(`### Gate ${gate.id}: ${gate.title}`);
    lines.push('');
    if (gate.description && gate.description.trim() !== '') {
      lines.push(`> ${gate.description}`);
      lines.push('');
    }
    const gateTodos = (tasksJson.todos ?? []).filter((t) => t.gate === gate.id);
    for (const todo of gateTodos) {
      const allChecked = (todo.steps ?? []).every((s) => s.checked === true);
      const box = allChecked ? 'x' : ' ';
      lines.push(`- [${box}] **${todo.id}**: ${todo.title}`);
      const reviewStep = (todo.steps ?? []).find((s) => s.kind === 'review');
      const reviewLine = formatReviewLine(todo.id, reviewStep?.review ?? null);
      lines.push(`  ${reviewLine}`);
    }
    lines.push('');
    lines.push(`**Gate ${gate.id} 通過条件**: ${gate.passCondition}`);
    lines.push('');
  }

  // 末尾の余分な改行を除去
  while (lines.length > 0 && lines[lines.length - 1] === '') {
    lines.pop();
  }
  lines.push('');

  return lines.join('\n');
}

/**
 * @param {string} todoId
 * @param {any} review
 * @returns {string}
 */
function formatReviewLine(todoId, review) {
  if (!review) {
    return `> **Review ${todoId}**: _未記入_`;
  }
  const { result, fixCount, summary } = review;
  const fixStr = fixCount > 0 ? ` (FIX ${fixCount}回)` : '';
  const summaryStr = summary ? ` — ${summary}` : '';
  switch (result) {
    case 'PASSED':      return `> **Review ${todoId}**: ✅ PASSED${fixStr}${summaryStr}`;
    case 'FAILED':      return `> **Review ${todoId}**: ❌ FAILED${summaryStr}`;
    case 'SKIPPED':     return `> **Review ${todoId}**: ⏭️ SKIPPED${summaryStr}`;
    case 'IN_PROGRESS': return `> **Review ${todoId}**: ⏳ IN_PROGRESS${summaryStr}`;
    default:            return `> **Review ${todoId}**: ${result}${summaryStr}`;
  }
}

/**
 * spec.md の generated 領域を置換する pure 関数
 * @param {string} specContent
 * @param {string} generatedSection
 * @returns {{ content: string, replaced: boolean }}
 */
export function replaceGeneratedSection(specContent, generatedSection) {
  const beginIdx = specContent.indexOf(BEGIN_MARKER);
  const endIdx = specContent.indexOf(END_MARKER);
  if (beginIdx < 0 || endIdx < 0 || endIdx < beginIdx) {
    return { content: specContent, replaced: false };
  }
  const before = specContent.slice(0, beginIdx + BEGIN_MARKER.length);
  const after = specContent.slice(endIdx);
  const next = `${before}\n${generatedSection}\n${after}`;
  return { content: next, replaced: true };
}

/**
 * CLI エントリポイント
 */
function main() {
  const tasksJsonPath = process.argv[2];
  if (!tasksJsonPath) {
    console.error('Usage: sync-spec-md.mjs <tasks-json-path>');
    process.exit(1);
  }

  const absPath = resolve(tasksJsonPath);
  if (!existsSync(absPath)) {
    console.error(`sync-spec-md: tasks.json not found at ${absPath}`);
    process.exit(0);
  }

  let tasksJson;
  try {
    tasksJson = JSON.parse(readFileSync(absPath, 'utf-8'));
  } catch (err) {
    console.error(`sync-spec-md: failed to parse tasks.json: ${err.message}`);
    process.exit(0);
  }

  if (typeof tasksJson?.schemaVersion !== 'number' || tasksJson.schemaVersion < 2) {
    process.exit(0);
  }

  const specPath = resolve(dirname(absPath), 'spec.md');
  if (!existsSync(specPath)) {
    console.error(`sync-spec-md: spec.md not found at ${specPath}, skipping`);
    process.exit(0);
  }

  const specContent = readFileSync(specPath, 'utf-8');
  const generatedSection = generateTaskListSection(tasksJson);
  const { content: newContent, replaced } = replaceGeneratedSection(specContent, generatedSection);

  if (!replaced) {
    console.error(`sync-spec-md: generated markers not found in ${specPath}, skipping`);
    process.exit(0);
  }

  if (newContent !== specContent) {
    writeFileSync(specPath, newContent, 'utf-8');
    console.error(`sync-spec-md: updated ${specPath}`);
  }
}

// 直接実行時のみ main を呼ぶ
const isDirectRun = import.meta.main ?? (
  process.argv[1] &&
  import.meta.url === pathToFileURL(realpathSync(process.argv[1])).href
);
if (isDirectRun) {
  main();
}
