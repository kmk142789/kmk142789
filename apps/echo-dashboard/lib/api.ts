export const API_BASE = process.env.NEXT_PUBLIC_ECHO_API_BASE_URL || 'http://localhost:5050';

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!response.ok) {
    throw new Error(`GET ${path} failed with ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    const message = errorBody?.error || `POST ${path} failed with ${response.status}`;
    throw new Error(message);
  }
  return (await response.json()) as T;
}

export async function apiPut<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    const message = errorBody?.error || `PUT ${path} failed with ${response.status}`;
    const error = new Error(message) as Error & { fields?: unknown };
    if (errorBody?.fields) {
      error.fields = errorBody.fields;
    }
    throw error;
  }
  return (await response.json()) as T;
}

export async function apiDelete(path: string): Promise<void> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'DELETE',
  });
  if (!response.ok && response.status !== 204) {
    const errorBody = await response.json().catch(() => ({}));
    const message = errorBody?.error || `DELETE ${path} failed with ${response.status}`;
    throw new Error(message);
  }
}
