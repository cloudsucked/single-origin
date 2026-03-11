import type { PageLoad } from './$types';
import { fetchApi } from '$lib/api';

type Product = {
  id: number;
  name: string;
  slug: string;
  origin?: string;
  roast_level?: string;
  category: string;
  description: string;
  price: number;
};

export const load: PageLoad = async ({ fetch, url }) => {
  const origin = url.searchParams.get('origin');
  const roast = url.searchParams.get('roast');
  const category = url.searchParams.get('category');

  const query = new URLSearchParams();
  if (origin) query.set('origin', origin);
  if (roast) query.set('roast', roast);
  if (category) query.set('category', category);

  const suffix = query.size > 0 ? `?${query.toString()}` : '';
  const products = await fetchApi<Product[]>(fetch, `/api/v1/products${suffix}`);

  return {
    products,
    filters: { origin, roast, category }
  };
};
