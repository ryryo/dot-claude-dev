import { describe, it, expect } from 'vitest';
import { renderTemplateString, renderJsonTemplate } from '../src/template/renderer';
import { buildTemplateContext } from '../src/template/context';
import type { AgentType } from '../src/resolvers/agentLayout';

describe('template renderer', () => {
  const agent: AgentType = 'claude-code';
  const ctx = buildTemplateContext({ agent, lang: 'en' });

  it('renders placeholders in markdown-like text', () => {
    const input = '# Hello {{AGENT}} in {{AGENT_DIR}}\n- doc: {{AGENT_DOC}}\n- cmds: {{AGENT_COMMANDS_DIR}}';
    const out = renderTemplateString(input, agent, ctx);
    expect(out).toContain('Hello claude-code in .claude');
    expect(out).toContain('doc: CLAUDE.md');
    expect(out).toContain('cmds: .claude/commands/kiro');
  });

  it('renders placeholders in JSON and parses to object', () => {
    const input = '{"agent":"{{AGENT}}","doc":"{{AGENT_DOC}}"}';
    const out = renderJsonTemplate(input, agent, ctx) as any;
    expect(out.agent).toBe('claude-code');
    expect(out.doc).toBe('CLAUDE.md');
  });

  it('throws on invalid JSON after substitution', () => {
    const input = '{"x": {{AGENT}} }';
    expect(() => renderJsonTemplate(input, agent, ctx)).toThrowError();
  });
});
