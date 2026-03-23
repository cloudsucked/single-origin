<script lang="ts">
  import { onMount } from 'svelte';
  import { apiBaseUrl } from '$lib/config';
  import { addToCart, loadCart } from '$lib/cart';
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
    farm?: { name: string; farmer: string; coordinates: { lat: number; lng: number } };
  };

  type Review = { id: number; rating: number; title: string; body: string };

  export let data: { product: Product; reviews: Review[] };

  let quantity = 1;
  let adding = false;
  let added = false;

  // Review form
  let reviewName = '';
  let reviewRating = 5;
  let reviewBody = '';
  let submittingReview = false;
  let reviewSuccess = '';
  let reviewError = '';

  onMount(() => loadCart());

  async function handleAddToCart() {
    adding = true;
    await addToCart(data.product.id, data.product.name, data.product.price, quantity);
    adding = false;
    added = true;
    setTimeout(() => (added = false), 2000);
  }

  async function submitReview() {
    submittingReview = true;
    reviewSuccess = '';
    reviewError = '';
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/products/${data.product.id}/reviews`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating: reviewRating, title: reviewName, body: reviewBody })
      });
      if (!res.ok) throw new Error('Failed to submit review.');
      reviewSuccess = 'Review submitted. Thank you!';
      reviewName = '';
      reviewRating = 5;
      reviewBody = '';
    } catch (err) {
      reviewError = err instanceof Error ? err.message : 'Failed to submit review.';
    } finally {
      submittingReview = false;
    }
  }

  function starLabel(n: number): string {
    return '★'.repeat(n) + '☆'.repeat(5 - n);
  }
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
    <a href={`/shop?category=${data.product.category}`}>{data.product.category === 'beans' ? 'Beans' : 'Equipment'}</a>
    <span class="sep">/</span>
    <span aria-current="page">{data.product.name}</span>
  </nav>

  <div class="product-detail">
    <div class="product-image-col">
      <img
        class="product-photo"
        src={coffeeImageFor(data.product.slug, data.product.id)}
        alt={data.product.name}
      />
    </div>
    <div class="product-info-col">
      <h1>{data.product.name}</h1>
      <nav class="section-nav" aria-label="Product navigation">
        <a href="/shop" class="active-tab" aria-current="page">Catalog</a>
        <a href="/shop?category=beans">Beans</a>
        <a href="/shop?category=equipment">Equipment</a>
        <a href="/subscribe">Subscriptions</a>
      </nav>
      <p class="description">{data.product.description}</p>
      <p class="meta">
        {#if data.product.origin}{data.product.origin} •{/if}
        {#if data.product.roast_level}{data.product.roast_level} roast •{/if}
        {data.product.category}
      </p>
      <p class="price">${data.product.price.toFixed(2)}</p>

      <div class="add-row">
        <label class="qty-label">
          Qty
          <input
            type="number"
            class="qty-input"
            bind:value={quantity}
            min="1"
            max="99"
          />
        </label>
        <button
          type="button"
          class="add-btn"
          class:added
          disabled={adding}
          on:click={handleAddToCart}
        >
          {#if adding}
            Adding...
          {:else if added}
            ✓ Added to cart
          {:else}
            Add to cart
          {/if}
        </button>
      </div>

      <p class="checkout-link"><a href="/checkout">View cart & checkout →</a></p>
    </div>
  </div>
</section>

{#if data.product.farm}
  <section>
    <h2>Origin Farm</h2>
    <p>
      <strong>{data.product.farm.name}</strong> — grown by {data.product.farm.farmer}.
      Coordinates: {data.product.farm.coordinates.lat}, {data.product.farm.coordinates.lng}
    </p>
  </section>
{/if}

<section>
  <h2>Reviews</h2>
  {#if data.reviews.length === 0}
    <p>No reviews yet. Be the first!</p>
  {:else}
    <ul class="reviews-list">
      {#each data.reviews as review}
        <li>
          <p class="review-stars" aria-label="{review.rating} out of 5 stars">{starLabel(review.rating)}</p>
          <p class="review-title">{review.title}</p>
          <p>{@html review.body}</p>
        </li>
      {/each}
    </ul>
  {/if}

  <h3>Write a review</h3>
  <form on:submit|preventDefault={submitReview}>
    <label>
      Title
      <input type="text" bind:value={reviewName} required placeholder="Short summary" />
    </label>
    <label>
      Rating
      <select bind:value={reviewRating}>
        {#each [5, 4, 3, 2, 1] as r}
          <option value={r}>{starLabel(r)} ({r}/5)</option>
        {/each}
      </select>
    </label>
    <label>
      Review
      <textarea rows="4" bind:value={reviewBody} required placeholder="Your thoughts..."></textarea>
    </label>
    <button type="submit" disabled={submittingReview}>{submittingReview ? 'Submitting...' : 'Submit review'}</button>
  </form>
  {#if reviewSuccess}
    <p class="success">{reviewSuccess}</p>
  {/if}
  {#if reviewError}
    <p class="error">{reviewError}</p>
  {/if}
</section>

<style>
  .product-detail {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    align-items: start;
  }

  @media (max-width: 680px) {
    .product-detail {
      grid-template-columns: 1fr;
    }
  }

  .product-photo {
    width: 100%;
    aspect-ratio: 4 / 3;
    object-fit: cover;
    border-radius: 14px;
    border: 1px solid rgba(138, 61, 16, 0.12);
  }

  .description {
    color: #424242;
    line-height: 1.7;
  }

  .meta {
    font-size: 0.88rem;
    color: #8b4f30;
  }

  .price {
    font-size: 1.5rem;
    font-weight: 800;
    color: #a94805;
    margin: 12px 0;
  }

  .add-row {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  }

  .qty-label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
  }

  .qty-input {
    width: 64px;
    text-align: center;
    padding: 10px 8px;
  }

  .add-btn {
    flex: 1;
    min-width: 140px;
  }

  .add-btn.added {
    background: #20643a;
    border-color: transparent;
  }

  .checkout-link {
    margin-top: 10px;
    font-size: 0.9rem;
  }

  .reviews-list {
    list-style: none;
    padding: 0;
    margin: 0 0 20px;
    display: grid;
    gap: 12px;
  }

  .reviews-list li {
    background: #fff;
    border: 1px solid #f2ccb0;
    border-radius: 12px;
    padding: 14px;
  }

  .review-stars {
    color: #f38020;
    font-size: 1.1rem;
    margin-bottom: 4px;
    letter-spacing: 1px;
  }

  .review-title {
    margin-bottom: 8px;
    font-weight: 700;
    color: #7a3611;
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
