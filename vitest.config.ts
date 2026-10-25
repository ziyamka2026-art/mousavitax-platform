import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'node',
    include: ['tests/unit/**/*.test.ts', 'packages/**/tests/**/*.test.ts'],
    exclude: ['**/node_modules/**', '**/.next/**'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      exclude: [
        '**/*.config.*',
        '**/node_modules/**',
        '**/tests/**',
        '**/*.d.ts',
      ],
      thresholds: {
        statements: 70,
        branches: 70,
        functions: 70,
        lines: 70,
      },
    },
  },
  resolve: {
    alias: {
      '@mousavitax/auth': '/home/z/my-project/mousavitax-platform/packages/auth/src',
      '@mousavitax/audit': '/home/z/my-project/mousavitax-platform/packages/audit/src',
      '@mousavitax/observability': '/home/z/my-project/mousavitax-platform/packages/observability/src',
    },
  },
});
