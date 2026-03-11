import type { PageLoad } from './$types';
import { fetchApi } from '$lib/api';

export const load: PageLoad = async ({ fetch }) => {
  const [inventory, orders, invoices] = await Promise.all([
    fetchApi(fetch, '/api/v1/wholesale/inventory'),
    fetchApi(fetch, '/api/v1/wholesale/orders'),
    fetchApi(fetch, '/api/v1/wholesale/invoices')
  ]);

  return { inventory, orders, invoices };
};
