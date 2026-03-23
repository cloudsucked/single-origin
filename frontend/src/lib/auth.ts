import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';

export type AuthUser = {
  id: number;
  email: string;
  name: string;
  role: string;
};

const TOKEN_KEY = 'so_token';
const USER_KEY = 'so_user';

function loadFromStorage(): { token: string | null; user: AuthUser | null } {
  if (!browser) return { token: null, user: null };
  try {
    const token = localStorage.getItem(TOKEN_KEY);
    const raw = localStorage.getItem(USER_KEY);
    const user = raw ? (JSON.parse(raw) as AuthUser) : null;
    return { token, user };
  } catch {
    return { token: null, user: null };
  }
}

const initial = loadFromStorage();

export const authToken = writable<string | null>(initial.token);
export const authUser = writable<AuthUser | null>(initial.user);

export const isLoggedIn = derived(authToken, ($token) => !!$token);

authToken.subscribe((token) => {
  if (!browser) return;
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
});

authUser.subscribe((user) => {
  if (!browser) return;
  if (user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  } else {
    localStorage.removeItem(USER_KEY);
  }
});

export function setAuth(token: string, user: AuthUser): void {
  authToken.set(token);
  authUser.set(user);
}

export function clearAuth(): void {
  authToken.set(null);
  authUser.set(null);
}
