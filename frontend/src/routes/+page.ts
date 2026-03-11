import type { PageLoad } from './$types';
import { fetchApi } from '$lib/api';

type Product = { id: number; name: string; slug: string; price: number };

export const load: PageLoad = async ({ fetch }) => {
  const [health, products] = await Promise.all([
    fetchApi<{ status: string; version: string }>(fetch, '/health'),
    fetchApi<Product[]>(fetch, '/api/v1/products')
  ]);

  return {
    health,
    featured: products.slice(0, 4)
  };
};
