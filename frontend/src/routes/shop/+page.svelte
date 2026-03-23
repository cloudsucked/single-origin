<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { coffeeImageFor } from '$lib/coffee-images';
  import { addToCart, loadCart } from '$lib/cart';

  type Product = {
    id: number;
    name: string;
    slug: string;
    origin?: string;
    roast_level?: string;
    category: string;
    description: string;
    price: number;
  };

  type Data = {
    products: Product[];
    filters: { origin: string | null; roast: string | null; category: string | null };
  };

  export let data: Data;

  let addingId: number | null = null;
  let addedId: number | null = null;

  // Sort state
  let sortBy = 'default';

  $: sortedProducts = [...data.products].sort((a, b) => {
    if (sortBy === 'price-asc') return a.price - b.price;
    if (sortBy === 'price-desc') return b.price - a.price;
    if (sortBy === 'name') return a.name.localeCompare(b.name);
    return 0;
  });

  onMount(() => loadCart());

  async function handleAddToCart(product: Product) {
    addingId = product.id;
    await addToCart(product.id, product.name, product.price);
    addingId = null;
    addedId = product.id;
    setTimeout(() => {
      if (addedId === product.id) addedId = null;
    }, 1500);
  }

  function applyFilter(param: string, value: string | null) {
    const url = new URL($page.url);
    if (value) {
      url.searchParams.set(param, value);
    } else {
      url.searchParams.delete(param);
    }
    goto(url.toString());
  }

  const ORIGINS = ['Ethiopia', 'Colombia', 'Guatemala', 'Kenya', 'Indonesia', 'Multi-origin'];
  const ROASTS = ['light', 'light-medium', 'medium', 'medium-dark', 'dark'];
</script>

<section>
  <h1>Shop</h1>
  <nav class="section-nav" aria-label="Shop sections">
    <a href="/shop" class:active-tab={!data.filters.category} aria-current={!data.filters.category ? 'page' : undefined}>All products</a>
    <a
      href="/shop?category=beans"
      class:active-tab={data.filters.category === 'beans'}
      aria-current={data.filters.category === 'beans' ? 'page' : undefined}
    >
      Beans
    </a>
    <a
      href="/shop?category=equipment"
      class:active-tab={data.filters.category === 'equipment'}
      aria-current={data.filters.category === 'equipment' ? 'page' : undefined}
    >
      Equipment
    </a>
    <a href="/subscribe">Subscriptions</a>
  </nav>

  <div class="filter-bar">
    <div class="filter-group">
      <label for="filter-origin">Origin</label>
      <select
        id="filter-origin"
        value={data.filters.origin ?? ''}
        on:change={(e) => applyFilter('origin', (e.target as HTMLSelectElement).value || null)}
      >
        <option value="">All origins</option>
        {#each ORIGINS as origin}
          <option value={origin}>{origin}</option>
        {/each}
      </select>
    </div>

    {#if !data.filters.category || data.filters.category === 'beans'}
      <div class="filter-group">
        <label for="filter-roast">Roast</label>
        <select
          id="filter-roast"
          value={data.filters.roast ?? ''}
          on:change={(e) => applyFilter('roast', (e.target as HTMLSelectElement).value || null)}
        >
          <option value="">All roasts</option>
          {#each ROASTS as roast}
            <option value={roast}>{roast}</option>
          {/each}
        </select>
      </div>
    {/if}

    <div class="filter-group">
      <label for="sort-by">Sort</label>
      <select id="sort-by" bind:value={sortBy}>
        <option value="default">Featured</option>
        <option value="price-asc">Price: low → high</option>
        <option value="price-desc">Price: high → low</option>
        <option value="name">Name A–Z</option>
      </select>
    </div>

    {#if data.filters.origin || data.filters.roast || data.filters.category}
      <a href="/shop" class="clear-filters">Clear filters ×</a>
    {/if}
  </div>

  <p class="result-count">{data.products.length} product{data.products.length !== 1 ? 's' : ''}</p>

  <div class="product-grid">
    {#each sortedProducts as product, index}
      <article class="product-card">
        <a href={`/shop/${product.slug}`} class="product-image-link">
          <img class="product-photo" src={coffeeImageFor(product.slug, index)} alt={product.name} loading="lazy" />
        </a>
        <div class="product-body">
          <a href={`/shop/${product.slug}`} class="product-name">{product.name}</a>
          <p class="meta">{product.origin || 'Multi-origin'} • {product.roast_level || 'N/A'} • {product.category}</p>
          <p class="description">{product.description}</p>
          <div class="product-footer">
            <p class="price">${product.price.toFixed(2)}</p>
            <button
              type="button"
              class="add-btn"
              class:added={addedId === product.id}
              disabled={addingId === product.id}
              on:click={() => handleAddToCart(product)}
            >
              {#if addingId === product.id}
                Adding...
              {:else if addedId === product.id}
                ✓ Added
              {:else}
                Add to cart
              {/if}
            </button>
          </div>
        </div>
      </article>
    {/each}
  </div>
</section>

<style>
  .product-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 12px;
  }

  .product-card {
    border: 1px solid var(--cf-border);
    border-radius: 14px;
    background: #fff;
    box-shadow: var(--cf-shadow);
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .product-image-link {
    display: block;
  }

  .product-photo {
    width: 100%;
    aspect-ratio: 4 / 3;
    object-fit: cover;
    border-bottom: 1px solid rgba(138, 61, 16, 0.1);
    display: block;
  }

  .product-body {
    padding: 14px;
    display: flex;
    flex-direction: column;
    flex: 1;
  }

  .product-name {
    font-weight: 700;
    color: #2e1f16;
    font-size: 1rem;
    margin-bottom: 4px;
    display: block;
  }

  .meta {
    font-size: 0.85rem;
    color: #8b4f30;
    margin-bottom: 6px;
  }

  .description {
    font-size: 0.9rem;
    color: #555;
    flex: 1;
    margin-bottom: 12px;
  }

  .product-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-top: auto;
  }

  .price {
    margin: 0;
    font-size: 1.04rem;
    font-weight: 700;
    color: #a94805;
  }

  .add-btn {
    font-size: 0.82rem;
    padding: 7px 12px;
    border-radius: 999px;
    white-space: nowrap;
    transition: background-color 120ms ease, transform 120ms ease;
  }

  .add-btn.added {
    background: #20643a;
    border-color: transparent;
  }

  .filter-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: flex-end;
    margin-bottom: 14px;
  }

  .filter-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .filter-group label {
    font-size: 0.78rem;
    font-weight: 700;
    color: #8b4f30;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .filter-group select {
    font: inherit;
    font-size: 0.88rem;
    padding: 8px 10px;
    border-radius: 10px;
    border: 1px solid #dfb795;
    background: #fffdfb;
    color: #2e1f16;
    cursor: pointer;
  }

  .clear-filters {
    align-self: flex-end;
    font-size: 0.82rem;
    padding: 8px 12px;
    border-radius: 999px;
    background: rgba(243, 128, 32, 0.12);
    color: #a94805;
    font-weight: 700;
    border: 1px solid rgba(243, 128, 32, 0.3);
  }

  .result-count {
    font-size: 0.88rem;
    color: #8b4f30;
    margin-bottom: 10px;
  }
</style>
