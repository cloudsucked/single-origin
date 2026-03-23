import { writable, derived, get } from 'svelte/store';
import { apiBaseUrl } from '$lib/config';
import { browser } from '$app/environment';

export type CartItem = {
  product_id: number;
  quantity: number;
  name: string;
  price: number;
};

export const cartItems = writable<CartItem[]>([]);

export const cartCount = derived(cartItems, ($items) =>
  $items.reduce((sum, item) => sum + item.quantity, 0)
);

export const cartTotal = derived(cartItems, ($items) =>
  $items.reduce((sum, item) => sum + item.price * item.quantity, 0)
);

export function getCartSession(): string {
  if (!browser) return 'demo';
  try {
    const raw = localStorage.getItem('so_user');
    if (raw) {
      const user = JSON.parse(raw) as { email?: string };
      if (user.email) return user.email;
    }
  } catch {
    // ignore
  }
  return 'demo';
}

export async function loadCart(session?: string): Promise<void> {
  const s = session ?? getCartSession();
  try {
    const res = await fetch(`${apiBaseUrl}/api/v1/cart?session=${encodeURIComponent(s)}`);
    if (!res.ok) return;
    const data = (await res.json()) as { items: CartItem[] };
    cartItems.set(data.items ?? []);
  } catch {
    // ignore
  }
}

export async function addToCart(
  productId: number,
  name: string,
  price: number,
  quantity = 1,
  session?: string
): Promise<void> {
  const s = session ?? getCartSession();
  await fetch(`${apiBaseUrl}/api/v1/cart/items?session=${encodeURIComponent(s)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ product_id: productId, quantity, name, price })
  });
  await loadCart(s);
}

export async function removeFromCart(index: number, session?: string): Promise<void> {
  const s = session ?? getCartSession();
  await fetch(`${apiBaseUrl}/api/v1/cart/items/${index}?session=${encodeURIComponent(s)}`, {
    method: 'DELETE'
  });
  await loadCart(s);
}

export async function updateCartItem(
  index: number,
  productId: number,
  name: string,
  price: number,
  quantity: number,
  session?: string
): Promise<void> {
  const s = session ?? getCartSession();
  await fetch(`${apiBaseUrl}/api/v1/cart/items/${index}?session=${encodeURIComponent(s)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ product_id: productId, quantity, name, price })
  });
  await loadCart(s);
}

export async function clearCart(session?: string): Promise<void> {
  const s = session ?? getCartSession();
  const items = await fetch(`${apiBaseUrl}/api/v1/cart?session=${encodeURIComponent(s)}`)
    .then((r) => r.json() as Promise<{ items: CartItem[] }>)
    .then((d) => d.items ?? []);
  for (let i = items.length - 1; i >= 0; i--) {
    await fetch(`${apiBaseUrl}/api/v1/cart/items/${i}?session=${encodeURIComponent(s)}`, { method: 'DELETE' });
  }
  cartItems.set([]);
}
