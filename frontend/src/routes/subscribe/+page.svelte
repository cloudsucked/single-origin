<script lang="ts">
  import { apiBaseUrl } from '$lib/config';
  import { authUser } from '$lib/auth';
  import { get } from 'svelte/store';

  type Plan = {
    id: string;
    name: string;
    bags: string;
    price: number;
    frequency: string;
    description: string;
    highlight?: boolean;
  };

  const PLANS: Plan[] = [
    {
      id: 'explorer',
      name: 'Explorer',
      bags: '2 bags',
      price: 32,
      frequency: 'Every 2 weeks',
      description: 'Perfect for solo coffee enthusiasts. Two 250g bags of rotating single origins.'
    },
    {
      id: 'roasters-pick',
      name: "Roaster's Pick",
      bags: '4 bags',
      price: 58,
      frequency: 'Monthly',
      description: 'Our curated selection of four seasonal coffees, hand-picked by our head roaster.',
      highlight: true
    },
    {
      id: 'cafe-team',
      name: 'Cafe Team',
      bags: '10 kg',
      price: 220,
      frequency: 'Monthly',
      description: 'Bulk supply for offices and small cafes. Mix of blends and single origins.'
    }
  ];

  let selectedPlan: Plan = PLANS[0];
  let frequency = PLANS[0].frequency;
  let formEl: HTMLFormElement | null = null;
  let submitting = false;
  let error = '';
  let success = '';

  function selectPlan(plan: Plan) {
    selectedPlan = plan;
    frequency = plan.frequency;
  }

  async function submitSubscription() {
    submitting = true;
    error = '';
    success = '';

    const user = get(authUser);

    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/subscriptions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          plan: selectedPlan.name,
          cadence: frequency,
          user_email: user?.email ?? 'demo@singleorigin.example'
        })
      });

      const data = (await response.json()) as {
        status?: string;
        detail?: string;
      };

      if (!response.ok) {
        throw new Error(data.detail || 'Subscription setup failed.');
      }

      success =
        data.status === 'created'
          ? `${selectedPlan.name} subscription started at $${selectedPlan.price}/mo. Check your account to manage it.`
          : 'Subscription submitted.';
    } catch (err) {
      error = err instanceof Error ? err.message : 'Subscription setup failed.';
    } finally {
      submitting = false;
    }
  }
</script>

<section>
  <h1>Subscribe</h1>
  <p>Fresh beans on autopilot. Cancel or pause anytime. Free shipping on all plans.</p>
</section>

<section>
  <h2>Choose a plan</h2>
  <div class="plan-grid">
    {#each PLANS as plan}
      <button
        type="button"
        class="plan-card"
        class:selected={selectedPlan.id === plan.id}
        class:highlighted={plan.highlight}
        on:click={() => selectPlan(plan)}
        aria-pressed={selectedPlan.id === plan.id}
      >
        {#if plan.highlight}
          <span class="badge">Most popular</span>
        {/if}
        <p class="plan-name">{plan.name}</p>
        <p class="plan-bags">{plan.bags}</p>
        <p class="plan-price">${plan.price}<span class="plan-per">/mo</span></p>
        <p class="plan-freq">{plan.frequency}</p>
        <p class="plan-desc">{plan.description}</p>
        <span class="plan-check" aria-hidden="true">{selectedPlan.id === plan.id ? '✓ Selected' : 'Select'}</span>
      </button>
    {/each}
  </div>
</section>

<section>
  <h2>Confirm subscription</h2>
  <div class="summary-card">
    <div class="summary-row">
      <span>Plan</span>
      <strong>{selectedPlan.name}</strong>
    </div>
    <div class="summary-row">
      <span>Delivery</span>
      <strong>{selectedPlan.frequency}</strong>
    </div>
    <div class="summary-row">
      <span>Amount</span>
      <strong class="summary-price">${selectedPlan.price}/mo</strong>
    </div>
  </div>

  <form bind:this={formEl} on:submit|preventDefault={submitSubscription} class="sub-form">
    <label>
      Delivery frequency
      <select name="frequency" bind:value={frequency}>
        <option value={selectedPlan.frequency}>{selectedPlan.frequency} (plan default)</option>
        {#if selectedPlan.id !== 'explorer'}
          <option value="Every 2 weeks">Every 2 weeks (+$0)</option>
        {/if}
      </select>
    </label>
    <button type="submit" disabled={submitting}>
      {submitting ? 'Starting subscription...' : `Start ${selectedPlan.name} — $${selectedPlan.price}/mo`}
    </button>
  </form>

  {#if success}
    <p class="success">{success}</p>
    <p><a href="/account">View your subscriptions →</a></p>
  {/if}
  {#if error}
    <p class="error">{error}</p>
  {/if}
</section>

<style>
  .plan-grid {
    display: grid;
    gap: 12px;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    margin-bottom: 0;
  }

  .plan-card {
    position: relative;
    border: 2px solid #f2ccb0;
    border-radius: 16px;
    background: #fff;
    padding: 18px 16px 14px;
    text-align: left;
    cursor: pointer;
    transition: border-color 140ms ease, box-shadow 140ms ease, transform 120ms ease;
    font: inherit;
    box-shadow: none;
    color: #2e1f16;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .plan-card:hover {
    border-color: var(--cf-orange);
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(243, 128, 32, 0.15);
    background: #fff;
  }

  .plan-card.selected {
    border-color: var(--cf-orange);
    background: rgba(243, 128, 32, 0.04);
    box-shadow: 0 0 0 3px rgba(243, 128, 32, 0.2);
  }

  .plan-card.highlighted {
    border-color: #d85f0d;
  }

  .badge {
    display: inline-block;
    background: var(--cf-orange);
    color: #fff;
    font-size: 0.72rem;
    font-weight: 800;
    border-radius: 999px;
    padding: 2px 8px;
    margin-bottom: 6px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    width: fit-content;
  }

  .plan-name {
    margin: 0;
    font-weight: 800;
    font-size: 1.1rem;
    color: #2e1f16;
  }

  .plan-bags {
    margin: 0;
    font-size: 0.9rem;
    color: #8b4f30;
  }

  .plan-price {
    margin: 6px 0 2px;
    font-size: 1.6rem;
    font-weight: 800;
    color: #a94805;
  }

  .plan-per {
    font-size: 0.9rem;
    font-weight: 600;
    color: #8b4f30;
  }

  .plan-freq {
    margin: 0 0 6px;
    font-size: 0.82rem;
    color: #8b4f30;
  }

  .plan-desc {
    margin: 0 0 10px;
    font-size: 0.84rem;
    color: #555;
    line-height: 1.5;
    flex: 1;
  }

  .plan-check {
    font-size: 0.82rem;
    font-weight: 700;
    color: var(--cf-orange);
    align-self: flex-start;
  }

  .summary-card {
    background: rgba(255, 255, 255, 0.8);
    border: 1px solid #f2ccb0;
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 14px;
    display: grid;
    gap: 8px;
  }

  .summary-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.95rem;
  }

  .summary-price {
    font-size: 1.1rem;
    color: #a94805;
  }

  .sub-form {
    max-width: 480px;
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
