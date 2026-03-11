import type { PageLoad } from './$types';
import { fetchApi } from '$lib/api';

export const load: PageLoad = async ({ fetch }) => {
  const [profile, orders, subscriptions] = await Promise.all([
    fetchApi(fetch, '/api/v1/account'),
    fetchApi(fetch, '/api/v1/orders'),
    fetchApi(fetch, '/api/v1/subscriptions')
  ]);

  return { profile, orders, subscriptions };
};
