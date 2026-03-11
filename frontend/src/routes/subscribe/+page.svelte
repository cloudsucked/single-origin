<script lang="ts">
  import { apiBaseUrl } from '$lib/config';

  let formEl: HTMLFormElement | null = null;
  let submitting = false;
  let error = '';
  let success = '';

  let plan = 'Explorer';
  let frequency = 'Every 2 weeks';

  async function submitSubscription() {
    submitting = true;
    error = '';
    success = '';

    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/subscriptions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          plan,
          cadence: frequency
        })
      });

      const data = (await response.json()) as {
        status?: string;
        detail?: string;
      };

      if (!response.ok) {
        throw new Error(data.detail || 'Subscription setup failed.');
      }

      success = data.status === 'created' ? 'Subscription started. You can review it in your account.' : 'Subscription submitted.';
      formEl?.reset();
      plan = 'Explorer';
      frequency = 'Every 2 weeks';
    } catch (err) {
      error = err instanceof Error ? err.message : 'Subscription setup failed.';
    } finally {
      submitting = false;
    }
  }
</script>

<section>
  <h1>Subscribe</h1>
  <p>Set up recurring deliveries with flexible cadence for home or office.</p>
</section>

<section>
  <h2>Choose a Plan</h2>
  <div class="plan-grid">
    <article>
      <p class="plan-name">Explorer</p>
      <p>2 bags monthly</p>
      <p class="plan-price">$32 / month</p>
    </article>
    <article>
      <p class="plan-name">Roaster's Pick</p>
      <p>4 bags monthly</p>
      <p class="plan-price">$58 / month</p>
    </article>
    <article>
      <p class="plan-name">Cafe Team</p>
      <p>10kg monthly</p>
      <p class="plan-price">$220 / month</p>
    </article>
  </div>
</section>

<section>
  <h2>Start Subscription</h2>
  <form bind:this={formEl} on:submit|preventDefault={submitSubscription}>
    <label>
      Plan
      <select name="plan" bind:value={plan}>
        <option value="Explorer">Explorer</option>
        <option value="Roaster's Pick">Roaster's Pick</option>
        <option value="Cafe Team">Cafe Team</option>
      </select>
    </label>
    <label>
      Delivery Frequency
      <select name="frequency" bind:value={frequency}>
        <option value="Every 2 weeks">Every 2 weeks</option>
        <option value="Monthly">Monthly</option>
      </select>
    </label>
    <button type="submit" disabled={submitting}>{submitting ? 'Starting subscription...' : 'Start subscription'}</button>
  </form>
  {#if success}
    <p class="success">{success}</p>
  {/if}
  {#if error}
    <p class="error">{error}</p>
  {/if}
</section>

<style>
  .plan-grid {
    display: grid;
    gap: 10px;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  }

  .plan-grid article {
    border: 1px solid #f2ccb0;
    border-radius: 12px;
    background: #fff;
    padding: 12px;
  }

  .plan-name {
    margin: 0 0 4px;
    font-weight: 700;
    color: #2e1f16;
  }

  .plan-price {
    margin-bottom: 0;
    font-weight: 700;
    color: #8a3d10;
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

  select {
    font: inherit;
    padding: 11px 12px;
    border-radius: 10px;
    border: 1px solid #dfb795;
    background: #fffdfb;
  }

  select:focus {
    outline: none;
    border-color: #f38020;
    box-shadow: 0 0 0 3px rgba(243, 128, 32, 0.2);
  }
</style>
