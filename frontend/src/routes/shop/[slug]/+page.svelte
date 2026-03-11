<script lang="ts">
  import { apiBaseUrl } from '$lib/config';

  type Product = {
    id: number;
    name: string;
    slug: string;
    origin?: string;
    roast_level?: string;
    category: string;
    description: string;
    price: number;
    farm?: { name: string; farmer: string; coordinates: { lat: number; lng: number } };
  };

  type Review = { id: number; rating: number; title: string; body: string };

  export let data: { product: Product; reviews: Review[] };
</script>

<svelte:head>
  <script src={`${apiBaseUrl}/js/so-analytics.js`} defer></script>
  <script src={`${apiBaseUrl}/js/reviews-widget.js`} defer></script>
  <script src={`${apiBaseUrl}/js/recommendations.js`} defer></script>
  <script src={`${apiBaseUrl}/js/chat-widget.js`} defer></script>
  <script src={`${apiBaseUrl}/js/social-pixel.js`} defer></script>
</svelte:head>

<section>
  <nav class="breadcrumb" aria-label="Breadcrumb">
    <a href="/">Home</a>
    <span class="sep">/</span>
    <a href="/shop">Shop</a>
    <span class="sep">/</span>
    <span aria-current="page">{data.product.name}</span>
  </nav>
  <h1>{data.product.name}</h1>
  <nav class="section-nav" aria-label="Product navigation">
    <a href="/shop" class="active-tab" aria-current="page">Catalog</a>
    <a href="/shop?category=beans">Beans</a>
    <a href="/shop?category=equipment">Equipment</a>
    <a href="/subscribe">Subscriptions</a>
  </nav>
  <p>{data.product.description}</p>
  <p class="price-row">
    ${data.product.price.toFixed(2)} • {data.product.origin || 'Multi-origin'} • {data.product.roast_level || 'N/A'}
  </p>
</section>

{#if data.product.farm}
  <section>
    <h2>Origin Farm</h2>
    <p>
      {data.product.farm.name} by {data.product.farm.farmer}
      ({data.product.farm.coordinates.lat}, {data.product.farm.coordinates.lng})
    </p>
  </section>
{/if}

<section>
  <h2>Reviews</h2>
  <ul>
    {#each data.reviews as review}
      <li>
        <p class="review-title">{review.rating}/5 — {review.title}</p>
        <p>{@html review.body}</p>
      </li>
    {/each}
  </ul>
</section>

<style>
  .price-row {
    font-size: 1.1rem;
    font-weight: 700;
    color: #a94805;
  }

  .review-title {
    margin-bottom: 8px;
    font-weight: 700;
    color: #7a3611;
  }
</style>
