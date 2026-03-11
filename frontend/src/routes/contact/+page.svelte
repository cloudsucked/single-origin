<script lang="ts">
  import { apiBaseUrl, turnstileSiteKey } from '$lib/config';

  let formEl: HTMLFormElement | null = null;
  let submitting = false;
  let error = '';
  let success = '';

  async function submitContact() {
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

      const response = await fetch(`${apiBaseUrl}/contact/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
        },
        body: payload
      });

      const data = (await response.json()) as {
        status?: string;
        detail?: string;
      };

      if (!response.ok) {
        throw new Error(data.detail || 'Message send failed.');
      }

      success = data.status === 'accepted' ? 'Message sent successfully.' : 'Message submitted.';
      formEl.reset();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Message send failed.';
    } finally {
      submitting = false;
    }
  }
</script>

<svelte:head>
  <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
  <script src={`${apiBaseUrl}/js/so-analytics.js`} defer></script>
  <script src={`${apiBaseUrl}/js/chat-widget.js`} defer></script>
</svelte:head>

<section>
  <h1>Contact</h1>
  <p>Send support requests, abuse reports, or account questions through the protected form.</p>

  <form bind:this={formEl} on:submit|preventDefault={submitContact}>
    <label>
      Name
      <input type="text" name="name" autocomplete="name" required />
    </label>

    <label>
      Email
      <input type="email" name="email" autocomplete="email" required />
    </label>

    <label>
      Message
      <textarea name="message" rows="6" required></textarea>
    </label>

    <div class="cf-turnstile" data-sitekey={turnstileSiteKey} data-action="contact"></div>

    <button type="submit" disabled={submitting}>{submitting ? 'Sending...' : 'Send message'}</button>
  </form>
  {#if success}
    <p class="success">{success}</p>
  {/if}
  {#if error}
    <p class="error">{error}</p>
  {/if}
</section>

<style>
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
