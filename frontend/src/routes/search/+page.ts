import type { PageLoad } from './$types';
import { fetchApi } from '$lib/api';

export const load: PageLoad = async ({ fetch, url }) => {
  const q = url.searchParams.get('q') || '';
  if (!q) {
    return { query: q, results: [] };
  }
  const encoded = encodeURIComponent(q);
  const payload = await fetchApi<{ query: string; results: Array<{ type: string; id: number; name: string; slug?: string }> }>(
    fetch,
    `/api/v1/search?q=${encoded}`
  );
  return { query: q, results: payload.results };
};
