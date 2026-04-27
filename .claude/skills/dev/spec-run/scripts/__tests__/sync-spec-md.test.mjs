import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, mkdtempSync, symlinkSync, writeFileSync, rmSync, mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { generateTaskListSection, replaceGeneratedSection } from '../sync-spec-md.mjs';

const sampleTasksV3 = {
  schemaVersion: 3,
  spec: { slug: 'demo', title: 'Demo', summary: '', createdDate: '2026-04-27', specPath: 'spec.md' },
  status: 'in-progress',
  reviewChecked: false,
  progress: { gatesPassed: 1, gatesTotal: 2, currentGate: 'B', currentGateAC: { passed: 0, total: 1 } },
  preflight: [],
  gates: [
    {
      id: 'A',
      title: 'データ層',
      summary: 'スキーマ整備',
      dependencies: [],
      goal: { what: 'items を CRUD できるようにする', why: '後続の API 層がデータ操作を抽象化された関数経由で行えるようにするため' },
      constraints: { must: ['drizzle-orm を使う'], mustNot: ['既存テーブルを変更しない'] },
      acceptanceCriteria: [
        { id: 'A.AC1', description: 'bun run type-check が 0 errors', checked: true }
      ],
      todos: [
        { id: 'A1', gate: 'A', title: '[TDD] スキーマ定義', tdd: true, dependencies: [], affectedFiles: [{ path: 'db/schema/items.ts', operation: 'create', summary: '' }] }
      ],
      review: { result: 'PASSED', fixCount: 0, summary: 'OK' },
      passed: true
    },
    {
      id: 'B',
      title: 'API 層',
      summary: '',
      dependencies: ['A'],
      goal: { what: '/api/items エンドポイントを提供する', why: 'クライアントから items を操作できるようにするため' },
      constraints: { must: [], mustNot: [] },
      acceptanceCriteria: [
        { id: 'B.AC1', description: 'GET /api/items が 200 を返す', checked: false }
      ],
      todos: [
        { id: 'B1', gate: 'B', title: 'POST /api handler', tdd: false, dependencies: ['A1'], affectedFiles: [{ path: 'app/api/items/route.ts', operation: 'create', summary: '' }] }
      ],
      review: null,
      passed: false
    }
  ],
  metadata: { createdAt: '', totalGates: 2, totalTodos: 2 }
};

test('generateTaskListSection: 依存関係図を含む', () => {
  const output = generateTaskListSection(sampleTasksV3);
  assert.match(output, /### 依存関係図/);
  assert.match(output, /Gate A/);
  assert.match(output, /Gate B/);
});

test('generateTaskListSection: Gate 見出しと summary を出力', () => {
  const output = generateTaskListSection(sampleTasksV3);
  assert.match(output, /### Gate A: データ層/);
  assert.match(output, /> スキーマ整備/);
  assert.match(output, /### Gate B: API 層/);
  // summary が空の gate は blockquote を出さない
  const gateBStart = output.indexOf('### Gate B');
  const gateBSection = output.slice(gateBStart, gateBStart + 80);
  assert.ok(!gateBSection.includes('> \n'), 'Empty summary should not produce blockquote');
});

test('generateTaskListSection: Goal の what と why を出力', () => {
  const output = generateTaskListSection(sampleTasksV3);
  assert.match(output, /\*\*Goal\*\*: items を CRUD できるようにする — 後続の API 層が/);
});

test('generateTaskListSection: Constraints の MUST / MUST NOT を出力', () => {
  const output = generateTaskListSection(sampleTasksV3);
  assert.match(output, /✅ MUST: drizzle-orm を使う/);
  assert.match(output, /❌ MUST NOT: 既存テーブルを変更しない/);
});

test('generateTaskListSection: Acceptance Criteria の checked / unchecked を出力', () => {
  const output = generateTaskListSection(sampleTasksV3);
  assert.match(output, /- \[x\] \*\*A\.AC1\*\*: bun run type-check/);
  assert.match(output, /- \[ \] \*\*B\.AC1\*\*: GET \/api\/items/);
});

test('generateTaskListSection: Todos リストとファイル参照を出力', () => {
  const output = generateTaskListSection(sampleTasksV3);
  assert.match(output, /\*\*Todos\*\* \(1\)/);
  assert.match(output, /- \*\*A1\*\*: \[TDD\] スキーマ定義 — `db\/schema\/items\.ts`/);
});

test('generateTaskListSection: Gate Review が PASSED として出力される', () => {
  const output = generateTaskListSection(sampleTasksV3);
  assert.match(output, /\*\*Review\*\*: ✅ PASSED — OK/);
});

test('generateTaskListSection: Review 未記入は _未記入_', () => {
  const output = generateTaskListSection(sampleTasksV3);
  assert.match(output, /\*\*Review\*\*: _未記入_/);
});

test('generateTaskListSection: FIX カウント 0 時は表示しない、1 以上で表示', () => {
  const data = structuredClone(sampleTasksV3);
  data.gates[0].review.fixCount = 2;
  const output = generateTaskListSection(data);
  assert.match(output, /\*\*Review\*\*: ✅ PASSED \(FIX 2回\) — OK/);
});

test('generateTaskListSection: FAILED / SKIPPED / IN_PROGRESS の表示', () => {
  const cases = [
    { result: 'FAILED',      summary: 'テスト失敗',  expected: /❌ FAILED — テスト失敗/ },
    { result: 'SKIPPED',     summary: 'docs only',   expected: /⏭️ SKIPPED — docs only/ },
    { result: 'IN_PROGRESS', summary: '',             expected: /⏳ IN_PROGRESS/ }
  ];
  for (const c of cases) {
    const data = structuredClone(sampleTasksV3);
    data.gates[0].review = { result: c.result, fixCount: 0, summary: c.summary };
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
  const callCount = (src.match(/writeFileSync\(/g) ?? []).length;
  assert.equal(callCount, 1, 'writeFileSync() 呼び出しは 1 箇所のみ (spec.md 向け)');
  assert.ok(!src.includes('writeFileSync(absPath'), 'tasks.json (absPath) への write がないこと');
});

test('schemaVersion < 3 は何もせず終了する（v1/v2 互換性なし）', () => {
  const tmpDir = mkdtempSync(join(tmpdir(), 'sync-spec-md-v2-'));
  try {
    const tasksPath = join(tmpDir, 'tasks.json');
    const specPath = join(tmpDir, 'spec.md');
    writeFileSync(tasksPath, JSON.stringify({ schemaVersion: 2, gates: [], todos: [] }));
    const originalSpec = '<!-- generated:begin -->\nold\n<!-- generated:end -->\n';
    writeFileSync(specPath, originalSpec);

    const script = resolve('.claude/skills/dev/spec-run/scripts/sync-spec-md.mjs');
    const result = spawnSync('node', [script, tasksPath], { encoding: 'utf-8' });
    assert.equal(result.status, 0);

    const after = readFileSync(specPath, 'utf-8');
    assert.equal(after, originalSpec, 'v2 では spec.md が変更されない');
  } finally {
    rmSync(tmpDir, { recursive: true, force: true });
  }
});

test('isDirectRun: symlink 経由で起動しても main() が実行されて spec.md が更新される', () => {
  const tmpDir = mkdtempSync(join(tmpdir(), 'sync-spec-md-symlink-'));
  try {
    const originalScript = resolve('.claude/skills/dev/spec-run/scripts/sync-spec-md.mjs');
    const symlinkedScript = join(tmpDir, 'sync-spec-md.mjs');
    symlinkSync(originalScript, symlinkedScript);

    const specDir = join(tmpDir, 'spec');
    mkdirSync(specDir);
    const tasksJson = { schemaVersion: 3, gates: [] };
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
