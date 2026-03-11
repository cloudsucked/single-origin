<script lang="ts">
  export let data: {
    inventory: Array<{ sku: string; available_kg: number }>;
    orders: Array<{ id: number; status: string; total_kg: number }>;
    invoices: Array<{ id: number; tax_id: string; bank_reference: string }>;
  };
</script>

<section>
  <h1>Wholesale Portal</h1>
  <p>Track inventory, orders, and invoice references in one view.</p>
</section>

<section>
  <h2>Inventory</h2>
  <ul class="grid-list">
    {#each data.inventory as item}
      <li>
        <p class="item-title">{item.sku}</p>
        <p>{item.available_kg}kg available</p>
      </li>
    {/each}
  </ul>
</section>

<section>
  <h2>Recent Orders</h2>
  <ul class="grid-list">
    {#each data.orders as order}
      <li>
        <p class="item-title">Order #{order.id}</p>
        <p>{order.total_kg}kg • {order.status}</p>
      </li>
    {/each}
  </ul>
</section>

<section>
  <h2>Invoices</h2>
  <ul class="grid-list">
    {#each data.invoices as invoice}
      <li>
        <p class="item-title">Invoice #{invoice.id}</p>
        <p>Tax ID: {invoice.tax_id}</p>
        <p>Reference: {invoice.bank_reference}</p>
      </li>
    {/each}
  </ul>
</section>

<style>
  .grid-list {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 10px;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  }

  .grid-list li {
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
