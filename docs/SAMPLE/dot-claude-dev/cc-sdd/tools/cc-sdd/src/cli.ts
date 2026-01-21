#!/usr/bin/env node
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { runCli } from './index.js';

// Execute when run as a script
void (async () => {
  const here = fileURLToPath(new URL('.', import.meta.url));
  // dist -> package root
  const packageRoot = path.resolve(here, '..');
  const argv = process.argv.slice(2);

  const exitCode = await runCli(
    argv,
    { platform: process.platform, env: process.env },
    undefined,
    {},
    { templatesRoot: packageRoot },
  );
  if (Number.isInteger(exitCode)) process.exit(exitCode);
})();
