<script lang="ts">
  import { apiBaseUrl, turnstileSiteKey } from '$lib/config';

  let formEl: HTMLFormElement | null = null;
  let submitting = false;
  let error = '';
  let success = '';

  async function submitLogin() {
    if (!formEl) {
      return;
    }

    submitting = true;
    error = '';
    success = '';

    try {
      const formData = new FormData(formEl);
      const payload = new URLSearchParams();

      for (const [key, value] of formData.entries()) {
        if (typeof value === 'string') {
          payload.append(key, value);
        }
      }

      const response = await fetch(`${apiBaseUrl}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
        },
        body: payload
      });

      const data = (await response.json()) as {
        token?: string;
        user?: { email?: string; name?: string };
        detail?: string;
      };

      if (!response.ok) {
        throw new Error(data.detail || 'Login failed.');
      }

      success = `Signed in as ${data.user?.name || data.user?.email || 'user'}.`;
      formEl.reset();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Login failed.';
    } finally {
      submitting = false;
    }
  }
</script>

<svelte:head>
  <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
</svelte:head>

<section>
  <h1>Login</h1>
  <nav class="section-nav" aria-label="Account navigation">
    <a href="/login" class="active-tab" aria-current="page">Sign in</a>
    <a href="/register">Create account</a>
    <a href="/account">Account overview</a>
  </nav>
  <p>Secure sign-in flow with Cloudflare Turnstile challenge support.</p>
  <form bind:this={formEl} on:submit|preventDefault={submitLogin}>
    <label>
      Email
      <input type="email" name="email" autocomplete="email" required value="demo@singleorigin.example" />
    </label>

    <label>
      Password
      <input type="password" name="password" autocomplete="current-password" required />
    </label>

    <div class="cf-turnstile" data-sitekey={turnstileSiteKey} data-action="login"></div>

    <button type="submit" disabled={submitting}>{submitting ? 'Signing in...' : 'Sign in'}</button>
  </form>
  {#if success}
    <p class="success">{success}</p>
  {/if}
  {#if error}
    <p class="error">{error}</p>
  {/if}
  <p class="helper">Need an account? <a href="/register">Create one</a>.</p>
</section>

<style>
  .helper {
    margin-top: 10px;
    font-size: 0.95rem;
  }

  .success {
    margin-top: 10px;
    color: #20643a;
    font-weight: 700;
  }

  .error {
    margin-top: 10px;
    color: #b0270f;
    font-weight: 700;
  }
</style>
