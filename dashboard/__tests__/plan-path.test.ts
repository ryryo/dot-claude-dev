import { describe, expect, it } from 'vitest';

import { getPlanDirectoryPath } from '../lib/plan-path';

describe('getPlanDirectoryPath', () => {
  it('v2 形式 (末尾 /spec.md) はディレクトリパスに変換する', () => {
    expect(
      getPlanDirectoryPath('docs/PLAN/260412_spec-dashboard-format-v2/spec.md')
    ).toBe('docs/PLAN/260412_spec-dashboard-format-v2');
  });

  it('v2 形式 (末尾 /tasks.json) はディレクトリパスに変換する', () => {
    expect(
      getPlanDirectoryPath('docs/PLAN/260412_foo/tasks.json')
    ).toBe('docs/PLAN/260412_foo');
  });

  it('レガシー単独 .md は拡張子を除去する', () => {
    expect(
      getPlanDirectoryPath('docs/PLAN/260411_dashboard-auth-hardening.md')
    ).toBe('docs/PLAN/260411_dashboard-auth-hardening');
  });

  it('既にディレクトリパスならそのまま返す', () => {
    expect(
      getPlanDirectoryPath('docs/PLAN/260410_foo')
    ).toBe('docs/PLAN/260410_foo');
  });
});
