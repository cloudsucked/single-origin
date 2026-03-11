import { apiBaseUrl } from '$lib/config';

export async function fetchApi<T>(fetchFn: typeof fetch, path: string): Promise<T> {
  const response = await fetchFn(`${apiBaseUrl}${path}`);
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${path}`);
  }
  return (await response.json()) as T;
}
