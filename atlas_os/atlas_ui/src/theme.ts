export type ThemeVariant = 'light' | 'dark';

export type ThemePalette = {
  background: string;
  foreground: string;
  accent: string;
  danger: string;
};

export const themePalettes: Record<ThemeVariant, ThemePalette> = {
  light: {
    background: '#f5f7fa',
    foreground: '#1c1f23',
    accent: '#0070f3',
    danger: '#d7263d',
  },
  dark: {
    background: '#0f172a',
    foreground: '#f8fafc',
    accent: '#38bdf8',
    danger: '#f87171',
  },
};

export const resolveSeverityColor = (palette: ThemePalette, severity: 'info' | 'warn' | 'error'): string => {
  if (severity === 'error') {
    return palette.danger;
  }
  if (severity === 'warn') {
    return palette.accent;
  }
  return palette.foreground;
};
