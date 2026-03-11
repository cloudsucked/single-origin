import { env } from '$env/dynamic/public';

export const apiBaseUrl = env.PUBLIC_API_BASE_URL || 'http://localhost:8000';
export const turnstileSiteKey = env.PUBLIC_TURNSTILE_SITEKEY || '1x00000000000000000000AA';
