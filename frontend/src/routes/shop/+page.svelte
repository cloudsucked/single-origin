<script lang="ts">
  import { coffeeImageFor } from '$lib/coffee-images';

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

  {#if data.filters.origin || data.filters.roast || data.filters.category}
    <p class="active-filters">
      Active filters:
      {data.filters.origin ? ` origin=${data.filters.origin}` : ''}
      {data.filters.roast ? ` roast=${data.filters.roast}` : ''}
      {data.filters.category ? ` category=${data.filters.category}` : ''}
    </p>
  {/if}

  <div class="product-grid">
    {#each data.products as product, index}
      <article class="product-card">
        <img class="product-photo" src={coffeeImageFor(product.slug, index)} alt={product.name} loading="lazy" />
        <a href={`/shop/${product.slug}`}>{product.name}</a>
        <p class="meta">{product.origin || 'Multi-origin'} • {product.roast_level || 'N/A'} • {product.category}</p>
        <p>{product.description}</p>
        <p class="price">${product.price.toFixed(2)}</p>
      </article>
    {/each}
  </div>
</section>

<style>
  .product-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 12px;
  }

  .product-card {
    border: 1px solid var(--cf-border);
    border-radius: 14px;
    background: #fff;
    box-shadow: var(--cf-shadow);
    padding: 14px;
  }

  .product-photo {
    width: 100%;
    aspect-ratio: 4 / 3;
    object-fit: cover;
    border-radius: 12px;
    border: 1px solid rgba(138, 61, 16, 0.12);
    margin-bottom: 10px;
  }

  .active-filters {
    display: inline-block;
    background: rgba(243, 128, 32, 0.14);
    border-radius: 999px;
    padding: 6px 12px;
    font-weight: 600;
  }

  .meta {
    font-size: 0.88rem;
    color: #8b4f30;
    margin-bottom: 8px;
  }

  .price {
    margin: 10px 0 0;
    font-size: 1.04rem;
    font-weight: 700;
    color: #a94805;
  }
</style>
