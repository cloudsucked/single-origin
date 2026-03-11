<script lang="ts">
  import { apiBaseUrl, turnstileSiteKey } from '$lib/config';

  let formEl: HTMLFormElement | null = null;
  let submitting = false;
  let error = '';
  let success = '';

  async function submitRegister() {
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

      const response = await fetch(`${apiBaseUrl}/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
        },
        body: payload
      });

      const data = (await response.json()) as {
        user?: { email?: string; name?: string };
        detail?: string;
      };

      if (!response.ok) {
        throw new Error(data.detail || 'Registration failed.');
      }

      success = `Account created for ${data.user?.name || data.user?.email || 'new user'}.`;
      formEl.reset();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Registration failed.';
    } finally {
      submitting = false;
    }
  }
</script>

<svelte:head>
  <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
</svelte:head>

<section>
  <h1>Register</h1>
  <nav class="section-nav" aria-label="Account navigation">
    <a href="/login">Sign in</a>
    <a href="/register" class="active-tab" aria-current="page">Create account</a>
    <a href="/account">Account overview</a>
  </nav>
  <p>Create an account with Turnstile-backed abuse protection.</p>

  <form bind:this={formEl} on:submit|preventDefault={submitRegister}>
    <label>
      Name
      <input type="text" name="name" autocomplete="name" required />
    </label>

    <label>
      Email
      <input type="email" name="email" autocomplete="email" required />
    </label>

    <label>
      Password
      <input type="password" name="password" autocomplete="new-password" required />
    </label>

    <div class="cf-turnstile" data-sitekey={turnstileSiteKey} data-action="register"></div>

    <button type="submit" disabled={submitting}>{submitting ? 'Creating account...' : 'Create account'}</button>
  </form>
  {#if success}
    <p class="success">{success}</p>
  {/if}
  {#if error}
    <p class="error">{error}</p>
  {/if}
  <p class="helper">Already have an account? <a href="/login">Sign in</a>.</p>
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
