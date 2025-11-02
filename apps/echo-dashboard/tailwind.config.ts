import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        echo: {
          night: '#0f172a',
          pulse: '#38bdf8',
          ember: '#f472b6',
        },
      },
    },
  },
  plugins: [],
};

export default config;
