#!/usr/bin/env node
// @ts-check
/**
 * tasks.json (v2) の整合性フィールドを自動修復する。
 * 修復対象: progress, status, reviewChecked, metadata (totalGates, totalTodos)
 *
 * --dry-run を付けると修正内容を表示のみ（ファイルは更新しない）。
 *
 * Usage:
 *   node fix-tasks-json.mjs <path-to-tasks.json> [--dry-run]
 */
import { readFileSync, writeFileSync, existsSync, realpathSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

function deriveStatus(allSteps, reviewChecked) {
  if (allSteps.length === 0) return 'not-started';
  const allDone = allSteps.every((s) => s.checked);
  const anyDone = allSteps.some((s) => s.checked);
  const hasReviewSteps = allSteps.some((s) => s.kind === 'review');

  if (allDone) {
    if (hasReviewSteps && !reviewChecked) return 'in-review';
    return 'completed';
  }
  const anyReviewFilled = allSteps.some((s) => s.kind === 'review' && s.checked);
  if (anyReviewFilled && !allDone) return 'in-review';
  if (anyDone) return 'in-progress';
  return 'not-started';
}

export function computeFixes(tj) {
  const fixes = [];
  const allSteps = (tj.todos ?? []).flatMap((t) => t.steps ?? []);
  const totalSteps = allSteps.length;
  const checkedSteps = allSteps.filter((s) => s.checked).length;
  const totalGates = (tj.gates ?? []).length;
  const totalTodos = (tj.todos ?? []).length;

  // progress.total
  if (tj.progress?.total !== totalSteps) {
    fixes.push({
      path: 'progress.total',
      old: tj.progress?.total,
      new: totalSteps,
    });
  }

  // progress.completed
  if (tj.progress?.completed !== checkedSteps) {
    fixes.push({
      path: 'progress.completed',
      old: tj.progress?.completed,
      new: checkedSteps,
    });
  }

  // status
  const derived = deriveStatus(allSteps, tj.reviewChecked);
  if (tj.status !== derived) {
    fixes.push({
      path: 'status',
      old: tj.status,
      new: derived,
    });
  }

  // metadata.totalGates
  if (tj.metadata?.totalGates !== totalGates) {
    fixes.push({
      path: 'metadata.totalGates',
      old: tj.metadata?.totalGates,
      new: totalGates,
    });
  }

  // metadata.totalTodos
  if (tj.metadata?.totalTodos !== totalTodos) {
    fixes.push({
      path: 'metadata.totalTodos',
      old: tj.metadata?.totalTodos,
      new: totalTodos,
    });
  }

  return fixes;
}

export function applyFixes(tj, fixes) {
  const clone = JSON.parse(JSON.stringify(tj));
  for (const fix of fixes) {
    switch (fix.path) {
      case 'progress.total':
        clone.progress.total = fix.new;
        break;
      case 'progress.completed':
        clone.progress.completed = fix.new;
        break;
      case 'status':
        clone.status = fix.new;
        break;
      case 'metadata.totalGates':
        clone.metadata.totalGates = fix.new;
        break;
      case 'metadata.totalTodos':
        clone.metadata.totalTodos = fix.new;
        break;
    }
  }
  return clone;
}

function main() {
  const args = process.argv.slice(2);
  const dryRun = args.includes('--dry-run');
  const tasksPath = args.find((a) => !a.startsWith('--'));

  if (!tasksPath) {
    console.error('Usage: fix-tasks-json.mjs <path-to-tasks.json> [--dry-run]');
    process.exit(1);
  }

  const absPath = resolve(tasksPath);
  if (!existsSync(absPath)) {
    console.error(`File not found: ${absPath}`);
    process.exit(1);
  }

  let tj;
  try {
    tj = JSON.parse(readFileSync(absPath, 'utf-8'));
  } catch (err) {
    console.error(`JSON parse error: ${err.message}`);
    process.exit(1);
  }

  const fixes = computeFixes(tj);

  if (fixes.length === 0) {
    console.log('✅ No fixes needed.');
    process.exit(0);
  }

  console.log(`Found ${fixes.length} fix(es):\n`);
  for (const fix of fixes) {
    console.log(`  ${fix.path}: ${JSON.stringify(fix.old)} → ${JSON.stringify(fix.new)}`);
  }

  if (dryRun) {
    console.log('\n(dry-run: file not updated)');
    process.exit(0);
  }

  const fixed = applyFixes(tj, fixes);
  writeFileSync(absPath, JSON.stringify(fixed, null, 2) + '\n', 'utf-8');
  console.log(`\n✅ Applied fixes to ${absPath}`);
}

const isDirectRun = import.meta.main ?? (
  process.argv[1] &&
  import.meta.url === pathToFileURL(realpathSync(process.argv[1])).href
);
if (isDirectRun) main();
