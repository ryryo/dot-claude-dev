#!/usr/bin/env node
// @ts-check
/**
 * ダッシュボードと全く同じ v2 パース処理をローカルで再現する。
 * plan-json-loader.ts (loadPlanFromTasksJson) を tsx 経由で直接 import し、
 * GitHub API 経由ではなくローカルファイルを読み込む。
 *
 * これにより「ダッシュボードで表示されない」原因を特定できる。
 * v1 (spec.md マークダウンパース) は対象外。
 *
 * Usage:
 *   node --import tsx simulate-dashboard-parse.mjs <plan-dir>
 *   node --import tsx simulate-dashboard-parse.mjs docs/PLAN/260415_dashboard-claude-web-trigger
 *   node --import tsx simulate-dashboard-parse.mjs docs/PLAN  (全 v2 プラン)
 *
 * NOTE: tsx が必要です (npx tsx --version で確認)
 */
import { readFileSync, existsSync, readdirSync, statSync } from 'node:fs';
import { resolve, basename, join } from 'node:path';

// ─── tsx による TS import ──────────────────────────────

async function loadParser() {
  // CWD をプロジェクトルートとして解決
  const base = process.cwd();
  const dashboardLib = join(base, 'dashboard/lib');

  const [{ loadPlanFromTasksJson }] = await Promise.all([
    import(join(dashboardLib, 'plan-json-loader.ts')),
  ]);

  return { loadPlanFromTasksJson };
}

// ─── isV2TasksJson (github.ts と同じロジック) ─────────
function isV2TasksJson(value) {
  if (typeof value !== 'object' || value === null) return false;
  const v = value;
  return typeof v.schemaVersion === 'number' && v.schemaVersion >= 2;
}

// ─── PlanFile をダッシュボードと同じ形式で表示 ──────────
function displayPlanFile(pf) {
  console.log('  ┌─────────────────────────────────────────');
  console.log(`  │ filePath:      ${pf.filePath}`);
  console.log(`  │ fileName:      ${pf.fileName}`);
  console.log(`  │ projectName:   ${pf.projectName}`);
  console.log(`  │ title:         ${pf.title}`);
  console.log(`  │ createdDate:   ${pf.createdDate}`);
  console.log(`  │ status:        ${pf.status}`);
  console.log(`  │ reviewChecked: ${pf.reviewChecked}`);
  console.log(`  │ hasV2Tasks:    ${pf.hasV2Tasks}`);
  console.log(`  │ progress:      ${pf.progress.completed}/${pf.progress.total} (${pf.progress.percentage}%)`);
  console.log(`  │ gates[${pf.gates.length}]:`);

  for (const g of pf.gates) {
    console.log(`  │   ${g.id}: ${g.title} (${g.todos.length} todos)`);
    for (const todo of g.todos) {
      const checked = todo.steps.filter((s) => s.checked).length;
      console.log(`  │     - ${todo.title} [${checked}/${todo.steps.length}]`);
      for (const step of todo.steps) {
        const mark = step.checked ? 'x' : ' ';
        console.log(`  │       [${mark}] ${step.kind}: ${step.title}`);
      }
    }
  }

  console.log(`  │ todos[${pf.todos.length}]:`);
  for (const todo of pf.todos) {
    const checked = todo.steps.filter((s) => s.checked).length;
    console.log(`  │   - ${todo.title} [${checked}/${todo.steps.length}]`);
  }

  const summaryPreview = pf.summary.length > 120 ? pf.summary.slice(0, 120) + '...' : pf.summary;
  console.log(`  │ summary:       ${summaryPreview}`);
  console.log('  └─────────────────────────────────────────');
}

// ─── main ───────────────────────────────────────────────
async function main() {
  const inputPath = process.argv[2];
  if (!inputPath) {
    console.error('Usage: simulate-dashboard-parse.mjs <plan-dir-or-plans-dir>');
    console.error('  node --import tsx simulate-dashboard-parse.mjs docs/PLAN/260415_foo');
    console.error('  node --import tsx simulate-dashboard-parse.mjs docs/PLAN');
    process.exit(1);
  }

  const absPath = resolve(inputPath);
  if (!existsSync(absPath)) {
    console.error(`Not found: ${absPath}`);
    process.exit(1);
  }

  const { loadPlanFromTasksJson } = await loadParser();

  // 単一プランディレクトリ or 親ディレクトリか判定
  const isPlanDir = existsSync(join(absPath, 'tasks.json'));
  const dirs = isPlanDir
    ? [absPath]
    : readdirSync(absPath)
        .map((name) => join(absPath, name))
        .filter((p) => statSync(p).isDirectory() && existsSync(join(p, 'tasks.json')));

  if (dirs.length === 0) {
    console.error('No v2 plan directories (with tasks.json) found.');
    process.exit(1);
  }

  console.log(`\n=== Simulating dashboard v2 parse for ${dirs.length} plan(s) ===\n`);

  let errors = 0;
  let success = 0;
  let skipped = 0;

  for (const dir of dirs) {
    const name = basename(dir);
    const tasksJsonPath = join(dir, 'tasks.json');
    console.log(`📋 ${name}`);

    // tasks.json を読み込んで v2 か確認
    let raw;
    let parsed;
    try {
      raw = readFileSync(tasksJsonPath, 'utf-8');
      parsed = JSON.parse(raw);
    } catch (err) {
      console.log(`  ❌ JSON parse error: ${err.message}`);
      errors++;
      console.log('');
      continue;
    }

    if (!isV2TasksJson(parsed)) {
      console.log(`  ⏭️  Not v2 (schemaVersion=${JSON.stringify(parsed.schemaVersion)}), skipping`);
      skipped++;
      console.log('');
      continue;
    }

    try {
      const specContent = existsSync(join(dir, 'spec.md'))
        ? readFileSync(join(dir, 'spec.md'), 'utf-8')
        : '';

      // ここがダッシュボードと全く同じ呼び出し
      const planFile = loadPlanFromTasksJson(parsed, tasksJsonPath, 'local/test', specContent);

      displayPlanFile(planFile);
      success++;
    } catch (err) {
      console.log(`  ❌ PARSE ERROR: ${err.message}`);
      console.log(`     Stack: ${err.stack?.split('\n').slice(0, 3).map((l) => '     ' + l.trim()).join('\n')}`);
      errors++;
    }

    console.log('');
  }

  console.log(`=== Results: ${success} ok, ${errors} errors, ${skipped} skipped (non-v2) ===`);
  process.exit(errors > 0 ? 1 : 0);
}

main().catch((err) => {
  console.error('Fatal:', err);
  process.exit(1);
});
