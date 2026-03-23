import type { PageLoad } from './$types';
import { fetchApi } from '$lib/api';
import { browser } from '$app/environment';

export const ssr = false;

export const load: PageLoad = async ({ fetch }) => {
  // Read user email from localStorage when available (client-side only)
  let email = 'demo@singleorigin.example';
  if (browser) {
    try {
      const raw = localStorage.getItem('so_user');
      if (raw) {
        const user = JSON.parse(raw) as { email?: string };
        if (user.email) email = user.email;
      }
    } catch {
      // ignore
    }
  }

  const emailParam = encodeURIComponent(email);

  const [profile, orders, subscriptions] = await Promise.all([
    fetchApi(fetch, '/api/v1/account'),
    fetchApi(fetch, `/api/v1/orders?email=${emailParam}`),
    fetchApi(fetch, `/api/v1/subscriptions?email=${emailParam}`)
  ]);

  return { profile, orders, subscriptions };
};
