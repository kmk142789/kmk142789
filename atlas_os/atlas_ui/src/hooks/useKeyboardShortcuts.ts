import { useEffect } from 'react';

type ShortcutMap = Record<string, () => void>;

const normalise = (event: KeyboardEvent): string => {
  const keys = [] as string[];
  if (event.ctrlKey || event.metaKey) keys.push('mod');
  if (event.shiftKey) keys.push('shift');
  if (event.altKey) keys.push('alt');
  keys.push(event.key.toLowerCase());
  return keys.join('+');
};

export const useKeyboardShortcuts = (shortcuts: ShortcutMap): void => {
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      const key = normalise(event);
      const action = shortcuts[key];
      if (action) {
        event.preventDefault();
        action();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [shortcuts]);
};
