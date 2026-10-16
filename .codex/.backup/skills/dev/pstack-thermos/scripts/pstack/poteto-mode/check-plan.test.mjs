import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const validator = fileURLToPath(new URL('./check-plan.mjs', import.meta.url));
const skeleton = fs.readFileSync(new URL('./fixtures/plan-upstream.md', import.meta.url), 'utf8');
assert.ok(skeleton, 'the shipped playbook contains its runnable plan skeleton');

function populatedPlan() {
  const fields = new Map([
    ['Program', 'Search accessibility'],
    ['swarm workers model', 'inherit-parent'],
    ['Task as a verb phrase', 'Expose search completion to screen readers'],
    ['plugin-root', '/opt/pstack'],
    ['execution playbook', 'autopilot-full'],
    ['control skill path', '.agents/skills/verify-search/SKILL.md'],
    ['each other leaf skill the program uses', 'interrogate/SKILL.md'],
    ['PR id', 'PR-1'], ['PR ids', 'PR-1'], ['PR id or class', 'PR-1'],
    ['PR id, or None.', 'None.'], ['pr-id', '1'],
    ['base-branch', 'main'], ['head-branch', 'search-accessibility'],
    ['head SHA', 'a'.repeat(40)], ['n', '1'],
    ['file path', 'src/search.ts'], ['glob', 'src/search*'],
    ['slug', 'search-complete'], ['media path', '/tmp/search-evidence'],
    ['command', 'npm test -- search'], ['value', '20 milliseconds'],
    ['The command or procedure, run at trunk and at the head, interleaved. Both sides must produce the metric.', 'node benchmark.mjs --interleaved'],
    ['predicate', 'the results and accessible status agree'],
    ['Scenario.', 'Submit a keyboard-only search and inspect the accessible status.'],
    ['the same load-bearing scenario', 'a keyboard-only search'],
    ['the behavior the diff adds plus the end state the user waits for', 'the accessible completion status'],
    ['One change. Name the symbol and the file.', 'Update announceResults in src/search.ts.'],
    ['One observable result, with the exact log line or screen state.', 'The accessible status reads Search complete.'],
    ['Test file and the case it gains.', 'search.test.ts gains a completion-announcement case.'],
  ]);
  // These fixtures exercise the published structural contract, not whether a
  // real implementation has satisfied the evidence described in its plan.
  let populated = skeleton;
  while (/<[^<>]+>/u.test(populated)) {
    populated = populated.replace(/<([^<>]+)>/gu, (_match, field) => fields.get(field) ?? 'The operator verifies the search completion evidence before merge.');
  }
  return populated
    .replace('  - [ ] PR-1 and PR-1 are independent and first. Both branch from `main`.\n  - [ ] PR-1 after PR-1.', '  - [ ] PR-1 is independent and branches from `main`.')
    .replace('PR-1 change an interaction.', 'PR-1 changes an interaction.');
}

function check(plan) {
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'pstack-plan-test-'));
  try {
    const file = path.join(temporary, 'plan with spaces.md');
    fs.writeFileSync(file, plan);
    const result = spawnSync(process.execPath, [validator, file], { encoding: 'utf8', timeout: 5000 });
    assert.ifError(result.error);
    assert.equal(result.signal, null);
    return result;
  } finally {
    fs.rmSync(temporary, { recursive: true, force: true });
  }
}

test('populated shipped plan skeleton satisfies its validator', () => {
  const plan = populatedPlan();
  assert.doesNotMatch(plan, /<[^<>]+>/u);
  const result = check(plan);
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /1 PR sections, 0 problems/u);
});

test('a populated plan with a missing review gate is rejected', () => {
  const plan = populatedPlan().replace(/\*\*Review gate\.\*\*[\s\S]*?(?=\*\*Merge\.\*\*)/u, '');
  const result = check(plan);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /expected \[.*Review gate\./u);
});

test('an interaction review gate without operator evidence is rejected', () => {
  const plan = populatedPlan().replace(/\*\*Review gate\.\*\*[\s\S]*?(?=\*\*Merge\.\*\*)/u, '**Review gate.** Review required.\n\n- [ ] Approve it.\n\n');
  const result = check(plan);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /Review gate lacks "operator"/u);
});

for (const configured of ['live-verified-model', 'inherit-parent']) {
  test(`configured worker choice ${configured} is accepted`, () => {
    const plan = populatedPlan().replaceAll('`inherit-parent`', `\`${configured}\``);
    assert.match(plan, new RegExp('Ten lanes on `' + configured + '` at the PR head'));
    const result = check(plan);
    assert.equal(result.status, 0, result.stderr);
  });
}

test('an unfilled worker model placeholder is rejected', () => {
  const result = check(populatedPlan().replace(/Ten lanes on `[^`]+`/u, 'Ten lanes on `<swarm workers model>`'));
  assert.equal(result.status, 1);
  assert.match(result.stderr, /Verify, live lacks/);
});

test('a plan without the 30-minute audit cadence is rejected', () => {
  const result = check(populatedPlan().replace('30-minute audit tick', 'audit tick when remembered'));
  assert.equal(result.status, 1);
  assert.match(result.stderr, /Program checklist lacks .*30/u);
});

test('an unfilled perf probe command is rejected', () => {
  const plan = populatedPlan();
  assert.match(plan, /Probe\. node benchmark\.mjs --interleaved/u);
  const result = check(plan.replace('node benchmark.mjs --interleaved', '<command>'));
  assert.equal(result.status, 1);
  assert.match(result.stderr, /unfilled placeholder/u);
});

for (const [name, content] of [
  ['inline type generics', '`Promise<Result>` and `Map<string, Array<Result>>` are concrete types.'],
  ['HTML markup', '<span>Concrete output</span>'],
  ['Markdown autolinks', '<https://example.test/evidence>'],
]) {
  test(`a populated plan accepts ${name}`, () => {
    const plan = populatedPlan().replace('# Search accessibility plan',
      '# Search accessibility plan\n\n' + content);
    assert.ok(plan.includes(content));
    const result = check(plan);
    assert.equal(result.status, 0, result.stderr);
  });
}

for (const content of ['<svg><path></path></svg>', '`<path>` names an SVG element.']) {
  test(`a populated plan accepts SVG markup ${content}`, () => {
    const plan = populatedPlan().replace('# Search accessibility plan',
      '# Search accessibility plan\n\n' + content);
    assert.ok(plan.includes(content));
    const result = check(plan);
    assert.equal(result.status, 0, result.stderr);
  });
}

test('an unfilled scaffold file path is rejected', () => {
  const plan = populatedPlan();
  assert.ok(plan.includes('Edit `src/search.ts`'));
  const result = check(plan.replace('Edit `src/search.ts`', 'Edit `<file path>`'));
  assert.equal(result.status, 1);
  assert.match(result.stderr, /unfilled placeholder/u);
});

function japanesePlan() {
  const ja = fs.readFileSync(new URL('../../../references/pstack/poteto-mode/playbooks/multi-phase-plan.md', import.meta.url), 'utf8');
  let plan = ja.match(/````markdown\n([\s\S]*?)\n````/u)[1];
  while (/<[^<>]+>/u.test(plan)) plan = plan.replace(/<([^<>]+)>/gu, (_m, field) => ({
    'swarm workers model': 'inherit-parent', 'skill-root': '/opt/pstack-thermos', 'execution playbook': 'autopilot-full',
    'slug': 'search', 'pr-id': '1', 'head SHA': 'a'.repeat(40), 'command': 'npm test',
  }[field] ?? '検索の結果と証拠を確認する'));
  return plan;
}
test('Japanese shipped plan passes with all evidence lanes populated', () => {
  const result = check(japanesePlan());
  assert.equal(result.status, 0, result.stderr);
});
test('Japanese plan rejects a missing live lane and a missing operator gate', () => {
  const result = check(japanesePlan().replace(/^- \[ \] 組10。.*\n/mu, '').replace(/画像と動画を会話で示す。.*承認を待つ。/u, '確認する。'));
  assert.equal(result.status, 1);
  assert.match(result.stderr, /expected 1 to 10/u);
  assert.match(result.stderr, /Review gate lacks "operator"/u);
});
