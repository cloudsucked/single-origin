<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { apiBaseUrl } from '$lib/config';
  import { cartItems, cartTotal, loadCart, removeFromCart, updateCartItem, clearCart } from '$lib/cart';
  import { authUser } from '$lib/auth';

  let loading = true;
  let submitting = false;
  let orderSuccess: { id: number; total: number } | null = null;
  let orderError = '';

  // Billing form
  let firstName = '';
  let lastName = '';
  let email = '';
  let phone = '';
  let address = '';
  let city = '';
  let state = '';
  let zip = '';
  let country = 'US';
  let cardNumber = '';
  let cardExpiry = '';
  let cardCvc = '';

  // Pre-fill billing form from auth store — cleaned up in onDestroy
  const unsubAuth = authUser.subscribe((user) => {
    if (user) {
      email = user.email;
      const parts = user.name.split(' ');
      firstName = parts[0] ?? '';
      lastName = parts.slice(1).join(' ');
    }
  });

  onDestroy(unsubAuth);

  onMount(async () => {
    await loadCart();
    loading = false;
  });

  async function handleRemove(index: number) {
    await removeFromCart(index);
  }

  async function handleQtyChange(index: number, item: typeof $cartItems[number], qty: number) {
    if (qty < 1) {
      await removeFromCart(index);
      return;
    }
    await updateCartItem(index, item.product_id, item.name, item.price, qty);
  }

  async function placeOrder() {
    submitting = true;
    orderError = '';
    orderSuccess = null;

    try {
      const billingAddress = `${firstName} ${lastName}, ${address}, ${city}, ${state} ${zip}, ${country}`;
      const last4 = cardNumber.replace(/\s/g, '').slice(-4);

      const payload = {
        email: email || 'demo@singleorigin.example',
        items: $cartItems.map((item) => ({
          product_id: item.product_id,
          quantity: item.quantity,
          name: item.name,
          price: item.price
        })),
        billing_address: billingAddress,
        card_last4: last4,
        phone,
        total: $cartTotal
      };

      const res = await fetch(`${apiBaseUrl}/api/v1/orders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const err = (await res.json()) as { detail?: string };
        throw new Error(err.detail || 'Order placement failed.');
      }

      const data = (await res.json()) as { status: string; order: { id: number; total: number } };
      orderSuccess = { id: data.order.id, total: data.order.total };

      // Clear cart after successful order
      await clearCart();
    } catch (err) {
      orderError = err instanceof Error ? err.message : 'Order placement failed.';
    } finally {
      submitting = false;
    }
  }

  function formatCard(value: string): string {
    return value
      .replace(/\D/g, '')
      .slice(0, 16)
      .replace(/(.{4})/g, '$1 ')
      .trim();
  }

  function formatExpiry(value: string): string {
    const digits = value.replace(/\D/g, '').slice(0, 4);
    if (digits.length >= 3) return digits.slice(0, 2) + '/' + digits.slice(2);
    return digits;
  }
</script>

<svelte:head>
  <script src={`${apiBaseUrl}/js/so-analytics.js`} defer></script>
  <script src={`${apiBaseUrl}/js/checkout-sdk.js?v=1.2.3`} defer></script>
  <script src={`${apiBaseUrl}/js/recommendations.js`} defer></script>
</svelte:head>

{#if orderSuccess}
  <section class="success-section">
    <h1>Order confirmed!</h1>
    <p>Order <strong>#{orderSuccess.id}</strong> placed successfully.</p>
    <p>Total charged: <strong>${orderSuccess.total.toFixed(2)}</strong></p>
    <p>
      <a href="/account">View your orders</a> or <a href="/shop">continue shopping</a>.
    </p>
  </section>
{:else}
  <section>
    <h1>Checkout</h1>
    <nav class="breadcrumb" aria-label="Breadcrumb">
      <a href="/shop">Shop</a>
      <span class="sep">/</span>
      <span aria-current="page">Checkout</span>
    </nav>
  </section>

  <div class="checkout-layout">
    <!-- Cart summary -->
    <div class="cart-col">
      <section>
        <h2>Your cart</h2>
        {#if loading}
          <p>Loading cart...</p>
        {:else if $cartItems.length === 0}
          <p>Your cart is empty. <a href="/shop">Browse products</a>.</p>
        {:else}
          <ul class="cart-list">
            {#each $cartItems as item, index}
              <li class="cart-item">
                <div class="item-info">
                  <p class="item-name">{item.name || `Product #${item.product_id}`}</p>
                  <p class="item-price">${item.price.toFixed(2)} each</p>
                </div>
                <div class="item-controls">
                  <button
                    type="button"
                    class="qty-btn"
                    on:click={() => handleQtyChange(index, item, item.quantity - 1)}
                    aria-label="Decrease quantity"
                  >−</button>
                  <span class="qty-display">{item.quantity}</span>
                  <button
                    type="button"
                    class="qty-btn"
                    on:click={() => handleQtyChange(index, item, item.quantity + 1)}
                    aria-label="Increase quantity"
                  >+</button>
                  <span class="item-subtotal">${(item.price * item.quantity).toFixed(2)}</span>
                  <button
                    type="button"
                    class="remove-btn"
                    on:click={() => handleRemove(index)}
                    aria-label="Remove item"
                  >×</button>
                </div>
              </li>
            {/each}
          </ul>
          <div class="cart-total">
            <span>Subtotal</span>
            <strong>${$cartTotal.toFixed(2)}</strong>
          </div>
        {/if}
      </section>
    </div>

    <!-- Checkout form -->
    {#if $cartItems.length > 0}
      <div class="form-col">
        <section>
          <h2>Billing &amp; payment</h2>
          <form on:submit|preventDefault={placeOrder} class="checkout-form">
            <fieldset>
              <legend>Contact</legend>
              <div class="row-2">
                <label>
                  First name
                  <input type="text" bind:value={firstName} required autocomplete="given-name" />
                </label>
                <label>
                  Last name
                  <input type="text" bind:value={lastName} required autocomplete="family-name" />
                </label>
              </div>
              <label>
                Email
                <input type="email" bind:value={email} required autocomplete="email" />
              </label>
              <label>
                Phone
                <input type="tel" bind:value={phone} autocomplete="tel" placeholder="+1 555 000 0000" />
              </label>
            </fieldset>

            <fieldset>
              <legend>Shipping address</legend>
              <label>
                Street address
                <input type="text" bind:value={address} required autocomplete="street-address" placeholder="123 Main St" />
              </label>
              <div class="row-3">
                <label>
                  City
                  <input type="text" bind:value={city} required autocomplete="address-level2" />
                </label>
                <label>
                  State
                  <input type="text" bind:value={state} autocomplete="address-level1" placeholder="CA" maxlength="4" />
                </label>
                <label>
                  ZIP
                  <input type="text" bind:value={zip} required autocomplete="postal-code" placeholder="94107" maxlength="10" />
                </label>
              </div>
            </fieldset>

            <fieldset>
              <legend>Payment</legend>
              <p class="sandbox-note">This is a demo — no real payment is processed.</p>
              <label>
                Card number
                <input
                  type="text"
                  inputmode="numeric"
                  placeholder="4242 4242 4242 4242"
                  maxlength="19"
                  required
                  value={cardNumber}
                  on:input={(e) => (cardNumber = formatCard((e.target as HTMLInputElement).value))}
                  autocomplete="cc-number"
                />
              </label>
              <div class="row-2">
                <label>
                  Expiry (MM/YY)
                  <input
                    type="text"
                    inputmode="numeric"
                    placeholder="08/27"
                    maxlength="5"
                    required
                    value={cardExpiry}
                    on:input={(e) => (cardExpiry = formatExpiry((e.target as HTMLInputElement).value))}
                    autocomplete="cc-exp"
                  />
                </label>
                <label>
                  CVC
                  <input
                    type="text"
                    inputmode="numeric"
                    placeholder="123"
                    maxlength="4"
                    required
                    bind:value={cardCvc}
                    autocomplete="cc-csc"
                  />
                </label>
              </div>
            </fieldset>

            <div class="order-summary-row">
              <span>Total</span>
              <strong class="total-price">${$cartTotal.toFixed(2)}</strong>
            </div>

            <button type="submit" disabled={submitting} class="place-btn">
              {submitting ? 'Placing order...' : `Place order — $${$cartTotal.toFixed(2)}`}
            </button>

            {#if orderError}
              <p class="error">{orderError}</p>
            {/if}
          </form>
        </section>
      </div>
    {/if}
  </div>
{/if}

<style>
  .checkout-layout {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    align-items: start;
  }

  @media (max-width: 720px) {
    .checkout-layout {
      grid-template-columns: 1fr;
    }
  }

  .success-section {
    text-align: center;
    padding: 40px 20px;
  }

  .cart-list {
    list-style: none;
    padding: 0;
    margin: 0 0 14px;
    display: grid;
    gap: 10px;
  }

  .cart-item {
    border: 1px solid #f2ccb0;
    border-radius: 12px;
    background: #fff;
    padding: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
  }

  .item-name {
    margin: 0 0 2px;
    font-weight: 700;
    color: #2e1f16;
  }

  .item-price {
    margin: 0;
    font-size: 0.88rem;
    color: #8b4f30;
  }

  .item-controls {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .qty-btn {
    width: 28px;
    height: 28px;
    padding: 0;
    border-radius: 999px;
    font-size: 1.1rem;
    line-height: 1;
    font-weight: 700;
    background: #fff;
    color: #8a4519;
    border: 1px solid #e4b892;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .qty-display {
    min-width: 24px;
    text-align: center;
    font-weight: 700;
  }

  .item-subtotal {
    font-weight: 700;
    color: #a94805;
    min-width: 52px;
    text-align: right;
  }

  .remove-btn {
    width: 28px;
    height: 28px;
    padding: 0;
    border-radius: 999px;
    font-size: 1.1rem;
    line-height: 1;
    background: #fff;
    color: #b0270f;
    border: 1px solid #e4b892;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .cart-total {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 1.08rem;
    padding-top: 10px;
    border-top: 1px solid #f2ccb0;
  }

  .checkout-form {
    max-width: none;
  }

  fieldset {
    border: 1px solid var(--cf-border);
    border-radius: 12px;
    padding: 14px;
    margin: 0 0 14px;
  }

  legend {
    font-weight: 700;
    color: #7a3611;
    padding: 0 6px;
    font-size: 0.9rem;
  }

  .row-2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }

  .row-3 {
    display: grid;
    grid-template-columns: 2fr 1fr 1.2fr;
    gap: 10px;
  }

  .sandbox-note {
    font-size: 0.82rem;
    color: #8b4f30;
    background: rgba(243, 128, 32, 0.1);
    border-radius: 8px;
    padding: 6px 10px;
    margin-bottom: 10px;
  }

  .order-summary-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 1.1rem;
    padding: 10px 0;
  }

  .total-price {
    font-size: 1.3rem;
    color: #a94805;
  }

  .place-btn {
    width: 100%;
    padding: 14px;
    font-size: 1rem;
  }

  .error {
    margin-top: 10px;
    color: #b0270f;
    font-weight: 700;
  }
</style>
