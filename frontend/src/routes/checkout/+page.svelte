<script lang="ts">
  import { onMount } from 'svelte';
  import { apiBaseUrl } from '$lib/config';

  let cart: Array<{ product_id: number; quantity: number }> = [];
  let loading = true;

  async function refreshCart() {
    loading = true;
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/cart`);
      const data = await response.json();
      cart = data.items || [];
    } finally {
      loading = false;
    }
  }

  async function addDemoItem() {
    await fetch(`${apiBaseUrl}/api/v1/cart/items`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_id: 1, quantity: 1 })
    });
    await refreshCart();
  }

  onMount(refreshCart);
</script>

<svelte:head>
  <script src={`${apiBaseUrl}/js/so-analytics.js`} defer></script>
  <script src={`${apiBaseUrl}/js/checkout-sdk.js?v=1.2.3`} defer></script>
  <script src={`${apiBaseUrl}/js/recommendations.js`} defer></script>
</svelte:head>

<section>
  <h1>Checkout</h1>
  <p>Cart and checkout surface with simulated payment SDK and tracking scripts.</p>
  <div class="controls">
    <button type="button" on:click={addDemoItem}>Add demo item</button>
    <button type="button" class="secondary" on:click={refreshCart} disabled={loading}>Refresh cart</button>
  </div>
</section>

<section>
  <h2>Your Cart</h2>
  {#if loading}
    <p>Loading cart...</p>
  {:else if cart.length === 0}
    <p>Your cart is empty.</p>
  {:else}
    <ul class="cart-list">
      {#each cart as item}
        <li>
          <p class="item-title">Product #{item.product_id}</p>
          <p>Quantity: {item.quantity}</p>
        </li>
      {/each}
    </ul>
  {/if}
</section>

<style>
  .controls {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .secondary {
    background: #fff;
    color: #8a4519;
    border: 1px solid #e4b892;
  }

  .cart-list {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 10px;
  }

  .cart-list li {
    border: 1px solid #f2ccb0;
    border-radius: 12px;
    background: #fff;
    padding: 12px;
  }

  .item-title {
    margin: 0 0 4px;
    font-weight: 700;
    color: #2e1f16;
  }
</style>
