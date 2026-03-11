<script lang="ts">
  import { apiBaseUrl } from '$lib/config';
  import { coffeeImageFor } from '$lib/coffee-images';

  type Data = {
    health: { status: string; version: string };
    featured: Array<{ id: number; name: string; slug: string; price: number }>;
  };

  export let data: Data;
</script>

<svelte:head>
  <script src={`${apiBaseUrl}/js/so-analytics.js`} defer></script>
  <script src={`${apiBaseUrl}/js/chat-widget.js`} defer></script>
  <script src={`${apiBaseUrl}/js/social-pixel.js`} defer></script>
  <script src={`${apiBaseUrl}/js/cookie-consent.js`} defer></script>
  <script src={`${apiBaseUrl}/js/newsletter-popup.js`} defer></script>
</svelte:head>

<section class="hero">
  <p class="eyebrow">Cloudflare AppSec Lab</p>
  <h1>Single Origin</h1>
  <p>Specialty coffee storefront built as a realistic target for security and abuse-testing exercises.</p>
  <p>API status: <strong>{data.health.status}</strong> (v{data.health.version})</p>
  <div class="cta-row">
    <a href="/shop">Explore products</a>
    <a href="/admin">Open admin portal</a>
  </div>
</section>

<section>
  <h2>Featured coffees</h2>
  <div class="featured-grid">
    {#each data.featured as product, index}
      <article class="coffee-card">
        <img class="coffee-photo" src={coffeeImageFor(product.slug, index)} alt={product.name} loading="lazy" />
        <a class="card-link" href={`/shop/${product.slug}`}>{product.name}</a>
        <p class="price">${product.price.toFixed(2)}</p>
      </article>
    {/each}
  </div>
</section>

<section>
  <h2>Lab-ready surfaces</h2>
  <ul>
    <li>Turnstile integration points on login, register, and contact forms.</li>
    <li>Backend API endpoints for auth and contact submission.</li>
    <li>Editable SvelteKit and FastAPI source for learner exercises.</li>
  </ul>
</section>

<style>
  .hero {
    background: linear-gradient(135deg, rgba(243, 128, 32, 0.17) 0%, rgba(255, 255, 255, 0.9) 65%);
  }

  .eyebrow {
    display: inline-block;
    margin-bottom: 10px;
    padding: 4px 10px;
    border-radius: 999px;
    background: rgba(216, 95, 13, 0.12);
    color: #a94805;
    font-weight: 700;
    font-size: 0.82rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }

  .cta-row {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 6px;
  }

  .cta-row a {
    padding: 10px 14px;
    border-radius: 10px;
    background: rgba(243, 128, 32, 0.12);
  }

  .featured-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 14px;
  }

  .coffee-card {
    display: grid;
    gap: 10px;
    padding: 14px;
    border-radius: 14px;
    border: 1px solid var(--cf-border);
    background: #fff;
    box-shadow: var(--cf-shadow);
  }

  .card-link {
    font-size: 1.02rem;
  }

  .coffee-photo {
    width: 100%;
    aspect-ratio: 4 / 3;
    object-fit: cover;
    border-radius: 12px;
    border: 1px solid rgba(138, 61, 16, 0.12);
  }

  .price {
    margin: 6px 0 0;
    font-weight: 700;
    color: #7a3611;
  }
</style>
