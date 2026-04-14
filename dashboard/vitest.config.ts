import { defineConfig } from 'vitest/config';
import path from 'node:path';

export default defineConfig({
  test: {
    environment: 'node',
    include: ['__tests__/**/*.test.ts', '__tests__/**/*.test.tsx'],
  },
  resolve: {
    alias: {
      '@testing-library/react': path.resolve(
        __dirname,
        './test-support/testing-library-react.ts',
      ),
      '@': path.resolve(__dirname, '.'),
    },
  },
});
