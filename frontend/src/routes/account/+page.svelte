<script lang="ts">
  export let data: {
    profile: { name: string; email: string; phone: string; payment_methods: Array<{ brand: string; last4: string }> };
    orders: Array<{ id: number; total: number; status: string; billing_address: string; card_last4: string }>;
    subscriptions: Array<{ id: number; plan: string; frequency: string; status: string }>;
  };
</script>

<section>
  <h1>Account</h1>
  <nav class="section-nav" aria-label="Account navigation">
    <a href="/account" class="active-tab" aria-current="page">Overview</a>
    <a href="/subscribe">Manage subscriptions</a>
    <a href="/shop">Continue shopping</a>
  </nav>
  <p>{data.profile.name}</p>
  <p>{data.profile.email} • {data.profile.phone}</p>
</section>

<section>
  <h2>Payment Methods</h2>
  <ul class="stack-list">
    {#each data.profile.payment_methods as card}
      <li>
        <p class="item-title">{card.brand}</p>
        <p>**** {card.last4}</p>
      </li>
    {/each}
  </ul>
</section>

<section>
  <h2>Orders</h2>
  <ul class="stack-list">
    {#each data.orders as order}
      <li>
        <p class="item-title">Order #{order.id}</p>
        <p>${order.total.toFixed(2)} • {order.status}</p>
        <p>{order.billing_address}</p>
      </li>
    {/each}
  </ul>
</section>

<section>
  <h2>Subscriptions</h2>
  <ul class="stack-list">
    {#each data.subscriptions as subscription}
      <li>
        <p class="item-title">{subscription.plan}</p>
        <p>{subscription.frequency}</p>
        <span class="tag">{subscription.status}</span>
      </li>
    {/each}
  </ul>
</section>

<style>
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

  .item-title {
    margin: 0 0 4px;
    font-weight: 700;
    color: #2e1f16;
  }

  .tag {
    display: inline-flex;
    border-radius: 999px;
    padding: 4px 10px;
    border: 1px solid #f0b88d;
    background: #fff2e7;
    color: #8a4519;
    font-size: 0.82rem;
    font-weight: 700;
  }
</style>
