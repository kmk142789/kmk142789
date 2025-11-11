import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./vitest.setup.ts'],
    exclude: ['backend/**', 'node_modules/**'],
    coverage: {
      reporter: ['text', 'lcov'],
      exclude: ['next.config.js', 'tailwind.config.ts', 'postcss.config.js', 'node_modules/**'],
    },
  },
});
