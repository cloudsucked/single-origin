<script lang="ts">
  import { goto } from '$app/navigation';
  import { authUser, isLoggedIn, clearAuth } from '$lib/auth';
  import { apiBaseUrl } from '$lib/config';
  import { onMount } from 'svelte';

  export let data: {
    profile: { name: string; email: string; phone: string; payment_methods: Array<{ brand: string; last4: string }> };
    orders: Array<{ id: number; total: number; status: string; billing_address: string; card_last4: string }>;
    subscriptions: Array<{ id: number; plan: string; frequency: string; status: string }>;
  };

  function signOut() {
    clearAuth();
    goto('/login');
  }

  function statusClass(status: string): string {
    if (status === 'DELIVERED' || status === 'ACTIVE') return 'tag-green';
    if (status === 'PROCESSING') return 'tag-orange';
    if (status === 'CANCELLED' || status === 'PAUSED') return 'tag-grey';
    return '';
  }
</script>

<section>
  <h1>Account</h1>
  <nav class="section-nav" aria-label="Account navigation">
    <a href="/account" class="active-tab" aria-current="page">Overview</a>
    <a href="/subscribe">Manage subscriptions</a>
    <a href="/shop">Continue shopping</a>
    {#if $isLoggedIn}
      <button type="button" class="sign-out-btn" on:click={signOut}>Sign out</button>
    {:else}
      <a href="/login">Sign in</a>
    {/if}
  </nav>

  <div class="profile-row">
    <div class="avatar" aria-hidden="true">{data.profile.name.charAt(0).toUpperCase()}</div>
    <div>
      <p class="profile-name">{data.profile.name}</p>
      <p class="profile-meta">{data.profile.email}{data.profile.phone ? ' • ' + data.profile.phone : ''}</p>
    </div>
  </div>
</section>

<section>
  <h2>Payment methods</h2>
  {#if data.profile.payment_methods.length === 0}
    <p>No payment methods on file.</p>
  {:else}
    <ul class="stack-list">
      {#each data.profile.payment_methods as card}
        <li>
          <p class="item-title">{card.brand.toUpperCase()}</p>
          <p>**** **** **** {card.last4}</p>
        </li>
      {/each}
    </ul>
  {/if}
</section>

<section>
  <h2>Orders</h2>
  {#if data.orders.length === 0}
    <p>No orders yet. <a href="/shop">Start shopping</a>.</p>
  {:else}
    <ul class="stack-list">
      {#each data.orders as order}
        <li>
          <div class="item-header">
            <p class="item-title">Order #{order.id}</p>
            <span class="tag {statusClass(order.status)}">{order.status}</span>
          </div>
          <p>${order.total.toFixed(2)}</p>
          <p class="item-meta">{order.billing_address}</p>
        </li>
      {/each}
    </ul>
  {/if}
</section>

<section>
  <h2>Subscriptions</h2>
  {#if data.subscriptions.length === 0}
    <p>No active subscriptions. <a href="/subscribe">Browse plans</a>.</p>
  {:else}
    <ul class="stack-list">
      {#each data.subscriptions as sub}
        <li>
          <div class="item-header">
            <p class="item-title">{sub.plan}</p>
            <span class="tag {statusClass(sub.status)}">{sub.status}</span>
          </div>
          <p>{sub.frequency}</p>
        </li>
      {/each}
    </ul>
  {/if}
</section>

<style>
  .profile-row {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-top: 10px;
  }

  .avatar {
    width: 52px;
    height: 52px;
    border-radius: 999px;
    background: linear-gradient(140deg, var(--cf-orange) 0%, #ff9c47 100%);
    color: #fff;
    font-size: 1.4rem;
    font-weight: 800;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .profile-name {
    margin: 0;
    font-weight: 700;
    font-size: 1.1rem;
    color: #2e1f16;
  }

  .profile-meta {
    margin: 2px 0 0;
    font-size: 0.9rem;
    color: #8b4f30;
  }

  .stack-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: grid;
    gap: 10px;
  }

  .stack-list li {
    background: #fff;
    border: 1px solid #f2ccb0;
    border-radius: 12px;
    padding: 12px;
  }

  .item-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 4px;
  }

  .item-title {
    margin: 0;
    font-weight: 700;
    color: #2e1f16;
  }

  .item-meta {
    margin: 4px 0 0;
    font-size: 0.86rem;
    color: #777;
  }

  .tag {
    display: inline-flex;
    border-radius: 999px;
    padding: 3px 10px;
    border: 1px solid #f0b88d;
    background: #fff2e7;
    color: #8a4519;
    font-size: 0.78rem;
    font-weight: 700;
    white-space: nowrap;
  }

  .tag-green {
    background: #e8f5ee;
    border-color: #a3d4b5;
    color: #1a6b3c;
  }

  .tag-orange {
    background: #fff2e7;
    border-color: #f0b88d;
    color: #8a4519;
  }

  .tag-grey {
    background: #f5f5f5;
    border-color: #ccc;
    color: #555;
  }

  .sign-out-btn {
    background: transparent;
    color: #8a4519;
    border: 1px solid #e7c9b2;
    font-size: 0.88rem;
    padding: 6px 11px;
    border-radius: 999px;
    font-weight: 700;
    cursor: pointer;
  }

  .sign-out-btn:hover {
    background: rgba(243, 128, 32, 0.08);
    transform: translateY(-1px);
  }
</style>
