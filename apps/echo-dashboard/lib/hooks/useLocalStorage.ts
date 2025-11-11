'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

const isBrowser = typeof window !== 'undefined';

export interface UseLocalStorageOptions<T> {
  /**
   * Serialize the value before persisting it to localStorage.
   */
  serializer?: (value: T) => string;
  /**
   * Deserialize the stored value that is read from localStorage.
   */
  deserializer?: (value: string) => T;
  /**
   * Opt-out of synchronising updates between tabs and React trees.
   */
  sync?: boolean;
}

const defaultSerializer = <T,>(value: T) => JSON.stringify(value);
const defaultDeserializer = <T,>(value: string) => JSON.parse(value) as T;

/**
 * A resilient localStorage hook with graceful SSR fallbacks, optional
 * serialization, and cross-tab synchronisation.
 */
export function useLocalStorage<T>(
  key: string,
  initialValue: T,
  options?: UseLocalStorageOptions<T>,
) {
  const serializer = options?.serializer ?? defaultSerializer<T>;
  const deserializer = options?.deserializer ?? defaultDeserializer<T>;
  const shouldSync = options?.sync ?? true;

  const initialRef = useRef(initialValue);

  useEffect(() => {
    initialRef.current = initialValue;
  }, [initialValue]);

  const readValue = useCallback((): T => {
    if (!isBrowser) {
      return initialRef.current;
    }

    try {
      const raw = window.localStorage.getItem(key);
      if (raw === null) {
        return initialRef.current;
      }

      return deserializer(raw);
    } catch (error) {
      console.error(`useLocalStorage: failed reading key "${key}"`, error);
      return initialRef.current;
    }
  }, [deserializer, key]);

  const [storedValue, setStoredValue] = useState<T>(() => readValue());

  const customEventName = useMemo(() => `use-local-storage:${key}`, [key]);

  useEffect(() => {
    setStoredValue(readValue());
  }, [readValue]);

  useEffect(() => {
    if (!isBrowser || !shouldSync) {
      return undefined;
    }

    const handleStorage = (event: StorageEvent) => {
      if (event.storageArea !== window.localStorage || event.key !== key) {
        return;
      }

      if (event.newValue === null) {
        setStoredValue(initialRef.current);
        return;
      }

      try {
        setStoredValue(deserializer(event.newValue));
      } catch (error) {
        console.error(`useLocalStorage: failed parsing key "${key}" from storage`, error);
      }
    };

    const handleCustom = (event: Event) => {
      const { detail } = event as CustomEvent<T>;
      setStoredValue(detail ?? initialRef.current);
    };

    window.addEventListener('storage', handleStorage);
    window.addEventListener(customEventName, handleCustom as EventListener);

    return () => {
      window.removeEventListener('storage', handleStorage);
      window.removeEventListener(customEventName, handleCustom as EventListener);
    };
  }, [customEventName, deserializer, key, shouldSync]);

  const setValue = useCallback(
    (value: T | ((previous: T) => T)) => {
      setStoredValue((previous) => {
        const valueToStore = value instanceof Function ? value(previous) : value;

        if (!isBrowser) {
          return valueToStore;
        }

        try {
          const payload = serializer(valueToStore);
          if (payload === undefined) {
            window.localStorage.removeItem(key);
            window.dispatchEvent(new CustomEvent(customEventName, { detail: initialRef.current }));
          } else {
            window.localStorage.setItem(key, payload);
            window.dispatchEvent(new CustomEvent(customEventName, { detail: valueToStore }));
          }
        } catch (error) {
          console.error(`useLocalStorage: failed setting key "${key}"`, error);
        }

        return valueToStore;
      });
    },
    [customEventName, key, serializer],
  );

  const remove = useCallback(() => {
    setStoredValue(() => {
      const fallback = initialRef.current;

      if (!isBrowser) {
        return fallback;
      }

      try {
        window.localStorage.removeItem(key);
        window.dispatchEvent(new CustomEvent(customEventName, { detail: fallback }));
      } catch (error) {
        console.error(`useLocalStorage: failed removing key "${key}"`, error);
      }

      return fallback;
    });
  }, [customEventName, key]);

  return [storedValue, setValue, remove] as const;
}
