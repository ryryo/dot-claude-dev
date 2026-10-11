import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync, existsSync, chmodSync, realpathSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const audit = fileURLToPath(new URL('./worktree-audit.sh', import.meta.url));
test('audit preserves paths with spaces and holds untracked data without fetching', () => {
  const root = realpathSync(mkdtempSync(path.join(tmpdir(), 'pstack audit ')));
  const repo = path.join(root, 'repository');
  const bin = path.join(root, 'bin');
  mkdirSync(repo); mkdirSync(bin);
  const env = { ...process.env, GIT_CONFIG_GLOBAL: '/dev/null', GIT_CONFIG_NOSYSTEM: '1',
    PATH: bin + path.delimiter + process.env.PATH };
  const git = (...args) => execFileSync('git', ['-C', repo, '-c', 'core.hooksPath=/dev/null', ...args], { env, encoding: 'utf8' });
  try {
    writeFileSync(path.join(bin, 'gh'), '#!/bin/sh\nprintf "[]\\n"\n');
    chmodSync(path.join(bin, 'gh'), 0o755);
    git('init', '-b', 'main');
    git('config', 'user.name', 'Audit Test');
    git('config', 'user.email', 'audit@example.invalid');
    writeFileSync(path.join(repo, 'tracked'), 'baseline');
    git('add', 'tracked'); git('commit', '-m', 'baseline');
    git('update-ref', 'refs/remotes/origin/main', 'HEAD');
    const clean = path.join(root, 'clean tree with spaces');
    const dirty = path.join(root, 'untracked tree with spaces');
    git('worktree', 'add', '-b', 'clean', clean);
    git('worktree', 'add', '-b', 'dirty', dirty);
    writeFileSync(path.join(dirty, 'valuable untracked file'), 'preserve me');
    const refsBefore = git('show-ref');
    const output = execFileSync('bash', [audit, repo], { env, encoding: 'utf8' });
    const rows = output.trimEnd().split('\n').slice(1).map(row => row.split('\t'));
    assert.equal(rows.length, 2, output);
    assert.ok(rows.every(row => row.length === 9), output);
    assert.equal(rows.find(row => row[8] === clean)?.[7], 'verify-ancestry');
    assert.equal(rows.find(row => row[8] === dirty)?.[7], 'hold-wip');
    assert.ok(rows.every(row => row[6] === 'unknown'));
    assert.equal(git('show-ref'), refsBefore);
    assert.equal(existsSync(path.join(repo, '.git', 'FETCH_HEAD')), false);
    assert.equal(existsSync(path.join(dirty, 'valuable untracked file')), true);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
