export type OSType = 'mac' | 'windows' | 'linux';

type EnvLike = {
  platform?: string;
  env?: Record<string, string | undefined>;
};

export const resolveOs = (input: 'auto' | OSType, runtime: EnvLike = {}): OSType => {
  if (input !== 'auto') return input;

  const platform = runtime.platform ?? process.platform;

  if (platform === 'darwin') return 'mac';
  if (platform === 'win32') return 'windows';
  if (platform === 'linux') {
    // WSL は最終的に linux として扱う
    return 'linux';
  }

  // 不明なプラットフォームは linux にフォールバック
  return 'linux';
};
