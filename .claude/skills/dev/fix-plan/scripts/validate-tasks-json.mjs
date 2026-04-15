#!/usr/bin/env node
// @ts-check
/**
 * tasks.json (v2) の構造チェック・整合性チェックを実行する。
 * 出力は全て JSON で、{ valid, checks: [{id, label, ok, detail}] } 形式。
 *
 * Usage:
 *   node validate-tasks-json.mjs <path-to-tasks.json>
 *   node validate-tasks-json.mjs docs/PLAN/260415_foo/tasks.json
 */
import { readFileSync, existsSync, realpathSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

// ─── helpers ────────────────────────────────────────────
function fail(id, label, detail) {
  return { id, label, ok: false, detail };
}
function pass(id, label, detail = '') {
  return { id, label, ok: true, detail };
}

const VALID_STATUSES = new Set(['not-started', 'in-progress', 'in-review', 'completed']);
const STATUS_TYPOS = {
  done: 'completed',
  finish: 'completed',
  finished: 'completed',
  complete: 'completed',
  started: 'in-progress',
  progress: 'in-progress',
  review: 'in-review',
  reviewing: 'in-review',
  todo: 'not-started',
  pending: 'not-started',
  new: 'not-started',
};
const VALID_KINDS = new Set(['impl', 'review']);
const KIND_TYPOS = {
  implementation: 'impl',
  implement: 'impl',
  build: 'impl',
  implementaton: 'impl', // よくあるタイポ
  reviews: 'review',
};
const VALID_OPERATIONS = new Set(['create', 'modify', 'delete', 'rename']);

// ─── structural checks ─────────────────────────────────
function checkStructure(tj) {
  const checks = [];

  // #1 schemaVersion
  if (typeof tj.schemaVersion !== 'number' || tj.schemaVersion < 2) {
    checks.push(fail(1, 'schemaVersion', `got ${JSON.stringify(tj.schemaVersion)}, expected number >= 2`));
  } else {
    checks.push(pass(1, 'schemaVersion', `${tj.schemaVersion}`));
  }

  // #2 top-level keys
  const required = ['spec', 'status', 'reviewChecked', 'progress', 'preflight', 'gates', 'todos', 'metadata'];
  const missing = required.filter((k) => !(k in tj));
  if (missing.length > 0) {
    checks.push(fail(2, 'top-level keys', `missing: ${missing.join(', ')}`));
  } else {
    checks.push(pass(2, 'top-level keys'));
  }

  // #3 progress type
  const p = tj.progress;
  if (typeof p !== 'object' || p === null || typeof p.completed !== 'number' || typeof p.total !== 'number') {
    checks.push(fail(3, 'progress type', `got ${JSON.stringify(p)}, expected {completed:number, total:number}`));
  } else {
    checks.push(pass(3, 'progress type', `{completed:${p.completed}, total:${p.total}}`));
  }

  // #4 status value
  if (!VALID_STATUSES.has(tj.status)) {
    const suggestion = STATUS_TYPOS[tj.status];
    const hint = suggestion ? ` (did you mean "${suggestion}"?)` : '';
    checks.push(fail(4, 'status value', `got ${JSON.stringify(tj.status)}, expected one of: ${[...VALID_STATUSES].join(', ')}${hint}`));
  } else {
    checks.push(pass(4, 'status value', `"${tj.status}"`));
  }

  // #5 reviewChecked type
  if (typeof tj.reviewChecked !== 'boolean') {
    checks.push(fail(5, 'reviewChecked type', `got ${JSON.stringify(tj.reviewChecked)}, expected boolean`));
  } else {
    checks.push(pass(5, 'reviewChecked type', `${tj.reviewChecked}`));
  }

  // #6 spec required fields
  const specFields = ['slug', 'title', 'summary', 'createdDate', 'specPath'];
  const specMissing = specFields.filter((k) => !tj.spec || typeof tj.spec[k] !== 'string' || tj.spec[k] === '');
  if (specMissing.length > 0) {
    checks.push(fail(6, 'spec required fields', `empty/missing: ${specMissing.join(', ')}`));
  } else {
    checks.push(pass(6, 'spec required fields'));
  }

  // #7 preflight type
  if (!Array.isArray(tj.preflight)) {
    checks.push(fail(7, 'preflight type', `got ${typeof tj.preflight}, expected array`));
  } else {
    checks.push(pass(7, 'preflight type', `${tj.preflight.length} items`));
  }

  // #8 gates structure
  const gateIds = new Set();
  let gateOk = true;
  let gateDetail = [];
  if (!Array.isArray(tj.gates)) {
    checks.push(fail(8, 'gates type', 'not an array'));
    gateOk = false;
  } else {
    for (const g of tj.gates) {
      gateIds.add(g.id);
      const gRequired = ['id', 'title', 'description', 'dependencies', 'passCondition'];
      const gMissing = gRequired.filter((k) => !(k in g));
      if (gMissing.length > 0) gateDetail.push(`gate ${g.id}: missing ${gMissing.join(',')}`);
      if (!Array.isArray(g.dependencies)) gateDetail.push(`gate ${g.id}: dependencies not array`);
    }
    if (gateDetail.length > 0) {
      checks.push(fail(8, 'gates structure', gateDetail.join('; ')));
    } else {
      checks.push(pass(8, 'gates structure', `${tj.gates.length} gates: ${[...gateIds].join(', ')}`));
    }
  }

  // #9 todos structure
  let todoOk = true;
  let todoDetail = [];
  const todoIds = new Set();
  if (!Array.isArray(tj.todos)) {
    checks.push(fail(9, 'todos type', 'not an array'));
    todoOk = false;
  } else {
    for (const t of tj.todos) {
      todoIds.add(t.id);
      const tRequired = ['id', 'gate', 'title', 'description', 'tdd', 'dependencies', 'affectedFiles', 'impl', 'steps'];
      const tMissing = tRequired.filter((k) => !(k in t));
      if (tMissing.length > 0) todoDetail.push(`todo ${t.id}: missing ${tMissing.join(',')}`);
      if (typeof t.tdd !== 'boolean') todoDetail.push(`todo ${t.id}: tdd is ${typeof t.tdd}, expected boolean`);
      if (!Array.isArray(t.steps) || t.steps.length === 0) todoDetail.push(`todo ${t.id}: steps empty or not array`);
    }
    if (todoDetail.length > 0) {
      checks.push(fail(9, 'todos structure', todoDetail.join('; ')));
    } else {
      checks.push(pass(9, 'todos structure', `${tj.todos.length} todos`));
    }
  }

  // #10 steps structure
  let stepsDetail = [];
  if (todoOk && Array.isArray(tj.todos)) {
    for (const t of tj.todos) {
      for (const s of (t.steps ?? [])) {
        if (!VALID_KINDS.has(s.kind)) {
          const kindSuggestion = KIND_TYPOS[s.kind];
          const kindHint = kindSuggestion ? ` (did you mean "${kindSuggestion}"?)` : '';
          stepsDetail.push(`${t.id} step "${s.title}": kind=${JSON.stringify(s.kind)}${kindHint}`);
        }
        if (typeof s.checked !== 'boolean') stepsDetail.push(`${t.id} step "${s.title}": checked not boolean`);
        if (typeof s.title !== 'string' || s.title === '') stepsDetail.push(`${t.id} step: title empty`);
      }
    }
  }
  if (stepsDetail.length > 0) {
    checks.push(fail(10, 'steps structure', stepsDetail.join('; ')));
  } else if (todoOk) {
    const total = tj.todos.reduce((s, t) => s + (t.steps?.length ?? 0), 0);
    checks.push(pass(10, 'steps structure', `${total} steps total`));
  } else {
    checks.push(fail(10, 'steps structure', 'skipped (todos broken)'));
  }

  // #11 metadata
  const md = tj.metadata;
  const mdRequired = ['createdAt', 'totalGates', 'totalTodos'];
  const mdMissing = mdRequired.filter((k) => !(md && k in md));
  if (mdMissing.length > 0) {
    checks.push(fail(11, 'metadata fields', `missing: ${mdMissing.join(', ')}`));
  } else {
    checks.push(pass(11, 'metadata fields', `createdAt=${md.createdAt}, totalGates=${md.totalGates}, totalTodos=${md.totalTodos}`));
  }

  return { checks, gateIds, todoIds };
}

// ─── consistency checks ────────────────────────────────
function checkConsistency(tj, gateIds, todoIds) {
  const checks = [];

  const allSteps = tj.todos?.flatMap((t) => t.steps ?? []) ?? [];
  const totalSteps = allSteps.length;
  const checkedSteps = allSteps.filter((s) => s.checked).length;

  // #12 progress.total
  if (tj.progress?.total !== totalSteps) {
    checks.push(fail(12, 'progress.total', `recorded ${tj.progress?.total}, actual ${totalSteps}`));
  } else {
    checks.push(pass(12, 'progress.total', `${totalSteps}`));
  }

  // #13 progress.completed
  if (tj.progress?.completed !== checkedSteps) {
    checks.push(fail(13, 'progress.completed', `recorded ${tj.progress?.completed}, actual ${checkedSteps}`));
  } else {
    checks.push(pass(13, 'progress.completed', `${checkedSteps}`));
  }

  // #14 metadata.totalGates
  if (tj.metadata?.totalGates !== tj.gates?.length) {
    checks.push(fail(14, 'metadata.totalGates', `recorded ${tj.metadata?.totalGates}, actual ${tj.gates?.length}`));
  } else {
    checks.push(pass(14, 'metadata.totalGates', `${tj.gates?.length}`));
  }

  // #15 metadata.totalTodos
  if (tj.metadata?.totalTodos !== tj.todos?.length) {
    checks.push(fail(15, 'metadata.totalTodos', `recorded ${tj.metadata?.totalTodos}, actual ${tj.todos?.length}`));
  } else {
    checks.push(pass(15, 'metadata.totalTodos', `${tj.todos?.length}`));
  }

  // #16 status consistency
  const derived = deriveStatus(allSteps, tj.reviewChecked);
  if (tj.status !== derived) {
    checks.push(fail(16, 'status consistency', `recorded "${tj.status}", derived "${derived}"`));
  } else {
    checks.push(pass(16, 'status consistency', `"${tj.status}"`));
  }

  // #17 reviewChecked consistency (only flag if status is completed but reviewChecked is false)
  if (derived === 'completed' && !tj.reviewChecked) {
    checks.push(fail(17, 'reviewChecked vs status', 'all steps completed + review done but reviewChecked=false'));
  } else if (derived !== 'completed' && tj.reviewChecked) {
    checks.push(fail(17, 'reviewChecked vs status', `reviewChecked=true but status="${derived}" (not all steps done)`));
  } else {
    checks.push(pass(17, 'reviewChecked consistency', `${tj.reviewChecked}`));
  }

  // #18 orphaned gate references in todos
  const orphans = (tj.todos ?? []).filter((t) => !gateIds.has(t.gate));
  if (orphans.length > 0) {
    checks.push(fail(18, 'gate references', `todos reference missing gates: ${orphans.map((t) => `${t.id}→${t.gate}`).join(', ')}`));
  } else {
    checks.push(pass(18, 'gate references', 'all todos reference valid gates'));
  }

  // #19 unresolved dependencies
  const unresolved = (tj.todos ?? []).flatMap((t) =>
    (t.dependencies ?? []).filter((dep) => !todoIds.has(dep)).map((dep) => `${t.id}→${dep}`)
  );
  if (unresolved.length > 0) {
    checks.push(fail(19, 'dependency references', `unresolved: ${unresolved.join(', ')}`));
  } else {
    checks.push(pass(19, 'dependency references', 'all resolved'));
  }

  // #20 empty gates (gates with zero todos)
  const emptyGates = (tj.gates ?? []).filter((g) => !(tj.todos ?? []).some((t) => t.gate === g.id));
  if (emptyGates.length > 0) {
    checks.push(fail(20, 'empty gates', `no todos for: ${emptyGates.map((g) => g.id).join(', ')}`));
  } else {
    checks.push(pass(20, 'empty gates', 'all gates have todos'));
  }

  return checks;
}

function deriveStatus(allSteps, reviewChecked) {
  if (allSteps.length === 0) return 'not-started';
  const allDone = allSteps.every((s) => s.checked);
  const anyDone = allSteps.some((s) => s.checked);
  const anyReviewFilled = allSteps.some((s) => s.kind === 'review' && s.checked);

  if (allDone) {
    // If all steps are checked, check if review section exists
    // When all done and there are review steps, it's either in-review or completed
    if (reviewChecked) return 'completed';
    // Check if there are review steps — if so, need reviewChecked
    const hasReviewSteps = allSteps.some((s) => s.kind === 'review');
    if (hasReviewSteps) return 'in-review';
    return 'completed';
  }
  if (anyReviewFilled && !allDone) return 'in-review';
  if (anyDone) return 'in-progress';
  return 'not-started';
}

// ─── main ───────────────────────────────────────────────
export function validate(tasksJson) {
  const { checks: structChecks, gateIds, todoIds } = checkStructure(tasksJson);
  const consChecks = checkConsistency(tasksJson, gateIds, todoIds);
  const all = [...structChecks, ...consChecks];
  return {
    valid: all.every((c) => c.ok),
    checks: all,
    summary: {
      total: all.length,
      passed: all.filter((c) => c.ok).length,
      failed: all.filter((c) => !c.ok).length,
    },
  };
}

function main() {
  const tasksPath = process.argv[2];
  if (!tasksPath) {
    console.error('Usage: validate-tasks-json.mjs <path-to-tasks.json>');
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
    const result = {
      valid: false,
      checks: [fail(0, 'JSON parse', err.message)],
      summary: { total: 1, passed: 0, failed: 1 },
    };
    console.log(JSON.stringify(result, null, 2));
    process.exit(1);
  }

  const result = validate(tj);
  console.log(JSON.stringify(result, null, 2));
  process.exit(result.valid ? 0 : 1);
}

const isDirectRun = import.meta.main ?? (
  process.argv[1] &&
  import.meta.url === pathToFileURL(realpathSync(process.argv[1])).href
);
if (isDirectRun) main();
