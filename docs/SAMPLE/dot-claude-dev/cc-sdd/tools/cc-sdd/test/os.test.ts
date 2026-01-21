import { describe, it, expect } from 'vitest';
import { resolveOs, type OSType } from '../src/resolvers/os';

describe('resolveOs', () => {
  it('returns explicit input when not auto', () => {
    expect(resolveOs('mac')).toBe('mac');
    expect(resolveOs('windows')).toBe('windows');
    expect(resolveOs('linux')).toBe('linux');
  });

  it('maps auto + darwin to mac', () => {
    expect(resolveOs('auto', { platform: 'darwin' })).toBe('mac');
  });

  it('maps auto + win32 to windows', () => {
    expect(resolveOs('auto', { platform: 'win32' })).toBe('windows');
  });

  it('maps auto + linux to linux', () => {
    expect(resolveOs('auto', { platform: 'linux' })).toBe('linux');
  });

  it('maps auto + linux with WSL env to linux (still linux)', () => {
    expect(resolveOs('auto', { platform: 'linux', env: { WSL_DISTRO_NAME: 'Ubuntu' } })).toBe('linux');
  });

  it('falls back to linux for unknown platforms', () => {
    expect(resolveOs('auto', { platform: 'sunos' as any })).toBe('linux');
  });
});
