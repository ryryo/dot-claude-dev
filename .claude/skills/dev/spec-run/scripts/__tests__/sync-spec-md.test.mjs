import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, mkdtempSync, symlinkSync, writeFileSync, rmSync, mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { generateTaskListSection, replaceGeneratedSection } from '../sync-spec-md.mjs';

const sampleTasksV2 = {
  schemaVersion: 2,
  spec: { slug: 'demo', title: 'Demo', summary: '', createdDate: '2026-04-12', specPath: 'spec.md' },
  status: 'in-progress',
  reviewChecked: false,
  progress: { completed: 2, total: 4 },
  preflight: [],
  gates: [
    { id: 'A', title: 'データ層', description: 'スキーマ整備', dependencies: [], passCondition: '全 Review 結果記入欄が埋まり、総合判定が PASS であること' },
    { id: 'B', title: 'API 層', description: '', dependencies: ['A'], passCondition: '全 Review 結果記入欄が埋まり、総合判定が PASS であること' }
  ],
  todos: [
    {
      id: 'A1', gate: 'A', title: '[TDD] スキーマ定義', description: '',
      tdd: true, dependencies: [], affectedFiles: [], impl: '', relatedIssues: [],
      steps: [
        { kind: 'impl',   title: 'Step 1 — IMPL',   checked: true },
        { kind: 'review', title: 'Step 2 — Review', checked: true, review: { result: 'PASSED', fixCount: 0, summary: 'OK' } }
      ]
    },
    {
      id: 'B1', gate: 'B', title: 'POST /api handler', description: '',
      tdd: false, dependencies: ['A1'], affectedFiles: [], impl: '', relatedIssues: [],
      steps: [
        { kind: 'impl',   title: 'Step 1 — IMPL',   checked: false },
        { kind: 'review', title: 'Step 2 — Review', checked: false, review: null }
      ]
    }
  ],
  metadata: { createdAt: '', totalGates: 2, totalTodos: 2 }
};

test('generateTaskListSection: 依存関係図を含む', () => {
  const output = generateTaskListSection(sampleTasksV2);
  assert.match(output, /### 依存関係図/);
  assert.match(output, /Gate A/);
  assert.match(output, /Gate B/);
});

test('generateTaskListSection: Gate 見出しと description を出力', () => {
  const output = generateTaskListSection(sampleTasksV2);
  assert.match(output, /### Gate A: データ層/);
  assert.match(output, /> スキーマ整備/);
  assert.match(output, /### Gate B: API 層/);
  // description が空の gate は blockquote を出さない
  const gateBStart = output.indexOf('### Gate B');
  const gateBSection = output.slice(gateBStart, gateBStart + 80);
  assert.ok(!gateBSection.includes('> \n'), 'Empty description should not produce blockquote');
});

test('generateTaskListSection: 完了 Todo は [x]、未完了は [ ]', () => {
  const output = generateTaskListSection(sampleTasksV2);
  assert.match(output, /- \[x\] \*\*A1\*\*:/);
  assert.match(output, /- \[ \] \*\*B1\*\*:/);
});

test('generateTaskListSection: Review 結果を PASSED として出力', () => {
  const output = generateTaskListSection(sampleTasksV2);
  assert.match(output, /> \*\*Review A1\*\*: ✅ PASSED — OK/);
});

test('generateTaskListSection: Review 未記入は _未記入_', () => {
  const output = generateTaskListSection(sampleTasksV2);
  assert.match(output, /> \*\*Review B1\*\*: _未記入_/);
});

test('generateTaskListSection: Gate 通過条件を出力', () => {
  const output = generateTaskListSection(sampleTasksV2);
  const matches = output.match(/\*\*Gate [AB] 通過条件\*\*/g);
  assert.equal(matches?.length, 2);
});

test('generateTaskListSection: FIX カウント 0 時は表示しない、1 以上で表示', () => {
  const withFix = structuredClone(sampleTasksV2);
  withFix.todos[0].steps[1].review.fixCount = 2;
  const output = generateTaskListSection(withFix);
  assert.match(output, /Review A1\*\*: ✅ PASSED \(FIX 2回\) — OK/);
});

test('generateTaskListSection: FAILED / SKIPPED / IN_PROGRESS の表示', () => {
  const cases = [
    { result: 'FAILED',      summary: 'テスト失敗',  expected: /❌ FAILED — テスト失敗/ },
    { result: 'SKIPPED',     summary: 'docs only',   expected: /⏭️ SKIPPED — docs only/ },
    { result: 'SKIPPED',     summary: '[SIMPLE]',    expected: /⏭️ SKIPPED — \[SIMPLE\]/ },
    { result: 'IN_PROGRESS', summary: '',             expected: /⏳ IN_PROGRESS/ }
  ];
  for (const c of cases) {
    const data = structuredClone(sampleTasksV2);
    data.todos[0].steps[1].review = { result: c.result, fixCount: 0, summary: c.summary };
    const output = generateTaskListSection(data);
    assert.match(output, c.expected);
  }
});

test('replaceGeneratedSection: マーカーがなければ replaced: false', () => {
  const input = '# Title\n\n## タスクリスト\n\nno markers\n';
  const { content, replaced } = replaceGeneratedSection(input, 'NEW');
  assert.equal(replaced, false);
  assert.equal(content, input);
});

test('replaceGeneratedSection: マーカー間を正しく置換する', () => {
  const input = 'before\n<!-- generated:begin -->\nold content\n<!-- generated:end -->\nafter';
  const { content, replaced } = replaceGeneratedSection(input, 'NEW CONTENT\n');
  assert.equal(replaced, true);
  assert.ok(content.includes('<!-- generated:begin -->\nNEW CONTENT\n\n<!-- generated:end -->'));
  assert.ok(content.includes('before'));
  assert.ok(content.includes('after'));
});

test('sync が tasks.json を改変しない（無限ループ防止）', () => {
  const src = readFileSync(new URL('../sync-spec-md.mjs', import.meta.url), 'utf-8');
  // import 文を除いた writeFileSync の呼び出し箇所をカウント
  const callCount = (src.match(/writeFileSync\(/g) ?? []).length;
  assert.equal(callCount, 1, 'writeFileSync() 呼び出しは 1 箇所のみ (spec.md 向け)');
  assert.ok(!src.includes('writeFileSync(absPath'), 'tasks.json (absPath) への write がないこと');
});

test('isDirectRun: symlink 経由で起動しても main() が実行されて spec.md が更新される', () => {
  const tmpDir = mkdtempSync(join(tmpdir(), 'sync-spec-md-symlink-'));
  try {
    const originalScript = resolve('.claude/skills/dev/spec-run/scripts/sync-spec-md.mjs');
    const symlinkedScript = join(tmpDir, 'sync-spec-md.mjs');
    symlinkSync(originalScript, symlinkedScript);

    const specDir = join(tmpDir, 'spec');
    mkdirSync(specDir);
    const tasksJson = { schemaVersion: 2, gates: [], todos: [] };
    writeFileSync(join(specDir, 'tasks.json'), JSON.stringify(tasksJson));
    writeFileSync(join(specDir, 'spec.md'), '<!-- generated:begin -->\nold\n<!-- generated:end -->\n');

    const tasksPath = join(specDir, 'tasks.json');
    const result = spawnSync('node', [symlinkedScript, tasksPath], { encoding: 'utf-8' });
    assert.equal(result.status, 0, `node exited with status ${result.status}: ${result.stderr}`);

    const specContent = readFileSync(join(specDir, 'spec.md'), 'utf-8');
    assert.ok(!specContent.includes('old'), 'spec.md の古い内容が置換されていること');
    assert.ok(specContent.includes('<!-- generated:begin -->'), 'generated:begin マーカーが残っていること');
    assert.ok(specContent.includes('<!-- generated:end -->'), 'generated:end マーカーが残っていること');
  } finally {
    rmSync(tmpDir, { recursive: true, force: true });
  }
});
