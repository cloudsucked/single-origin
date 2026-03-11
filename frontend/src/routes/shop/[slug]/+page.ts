import { error } from '@sveltejs/kit';
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
  farm?: {
    name: string;
    farmer: string;
    coordinates: { lat: number; lng: number };
  };
};

export const load: PageLoad = async ({ fetch, params }) => {
  const products = await fetchApi<Product[]>(fetch, '/api/v1/products');
  const summary = products.find((item) => item.slug === params.slug);
  if (!summary) {
    throw error(404, 'Product not found');
  }

  const product = await fetchApi<Product>(fetch, `/api/v1/products/${summary.id}`);
  const reviews = await fetchApi<Array<{ id: number; rating: number; title: string; body: string }>>(
    fetch,
    `/api/v1/products/${summary.id}/reviews`
  );

  return { product, reviews };
};
