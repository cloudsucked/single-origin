<script lang="ts">
  import { page } from '$app/stores';

  let mobileMenuOpen = false;

  const isActive = (path: string): boolean => {
    if (path === '/') {
      return $page.url.pathname === '/';
    }
    return $page.url.pathname.startsWith(path);
  };
</script>

<svelte:head>
  <title>Single Origin</title>
</svelte:head>

<style>
  :global(:root) {
    --cf-orange: #f38020;
    --cf-orange-deep: #d85f0d;
    --cf-charcoal: #1f1f1f;
    --cf-slate: #424242;
    --cf-mist: #fff8f2;
    --cf-warm: #ffe7d2;
    --cf-card: #ffffff;
    --cf-border: #f2ccb0;
    --cf-shadow: 0 16px 42px rgba(243, 128, 32, 0.12);
  }

  :global(*) {
    box-sizing: border-box;
  }

  :global(body) {
    margin: 0;
    font-family: "Sora", "Avenir Next", "Segoe UI", sans-serif;
    background:
      radial-gradient(circle at 12% 8%, rgba(243, 128, 32, 0.22), transparent 35%),
      radial-gradient(circle at 92% 2%, rgba(243, 128, 32, 0.18), transparent 28%),
      linear-gradient(180deg, var(--cf-mist) 0%, var(--cf-warm) 100%);
    color: var(--cf-charcoal);
    min-height: 100vh;
  }

  :global(html) {
    scroll-behavior: smooth;
  }

  :global(main) {
    max-width: 1100px;
    margin: 0 auto;
    padding: 36px 24px 48px;
  }

  .topbar {
    position: sticky;
    top: 0;
    z-index: 20;
    backdrop-filter: blur(10px);
    background: rgba(255, 245, 236, 0.9);
    border-bottom: 1px solid var(--cf-border);
  }

  .topbar-inner {
    max-width: 1100px;
    margin: 0 auto;
    padding: 14px 24px 16px;
    display: grid;
    gap: 10px;
  }

  .utility-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .brand {
    display: flex;
    align-items: baseline;
    gap: 10px;
  }

  .brand-link {
    display: flex;
    align-items: baseline;
    gap: 10px;
    color: inherit;
  }

  .brand-mark {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    background: linear-gradient(140deg, var(--cf-orange) 0%, #ff9c47 100%);
    box-shadow: 0 10px 28px rgba(243, 128, 32, 0.35);
  }

  .brand-text {
    margin: 0;
    letter-spacing: -0.02em;
    font-size: 1.05rem;
    font-weight: 700;
  }

  .utility-nav,
  .primary-nav,
  .mobile-drawer-nav {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .utility-nav {
    justify-content: flex-end;
  }

  :global(a) {
    color: var(--cf-orange-deep);
    text-decoration: none;
    font-weight: 700;
    transition: color 140ms ease, background-color 140ms ease, transform 140ms ease;
  }

  :global(a:focus-visible) {
    outline: 3px solid rgba(243, 128, 32, 0.4);
    outline-offset: 2px;
  }

  .utility-nav a,
  .primary-nav a,
  .mobile-drawer-nav a {
    padding: 8px 12px;
    border-radius: 999px;
    background: transparent;
  }

  .utility-nav a:hover,
  .primary-nav a:hover,
  .mobile-drawer-nav a:hover {
    color: var(--cf-orange);
    background: rgba(243, 128, 32, 0.1);
    transform: translateY(-1px);
  }

  .utility-nav a.active-nav,
  .primary-nav a.active-nav,
  .mobile-drawer-nav a.active-nav {
    color: #fff;
    background: linear-gradient(140deg, var(--cf-orange) 0%, var(--cf-orange-deep) 100%);
    box-shadow: 0 8px 22px rgba(216, 95, 13, 0.26);
  }

  .primary-nav {
    align-items: center;
    border-top: 1px solid var(--cf-border);
    padding-top: 10px;
  }

  .primary-nav .admin-link {
    margin-left: auto;
  }

  .menu-toggle {
    display: none;
    width: 40px;
    height: 40px;
    border-radius: 10px;
    border: 1px solid var(--cf-border);
    background: #fff;
    color: var(--cf-orange-deep);
    font-size: 1.2rem;
    line-height: 1;
    box-shadow: none;
    padding: 0;
  }

  .mobile-drawer {
    display: none;
  }

  .mobile-drawer h3 {
    margin: 14px 0 8px;
    font-size: 0.88rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #8b4f30;
  }

  .mobile-drawer-nav {
    gap: 6px;
  }

  :global(h1) {
    margin: 0 0 8px;
    font-size: clamp(1.7rem, 2.8vw, 2.45rem);
    letter-spacing: -0.03em;
  }

  :global(h2) {
    margin: 24px 0 10px;
    font-size: clamp(1.2rem, 2vw, 1.55rem);
    letter-spacing: -0.02em;
  }

  :global(h2[id]) {
    scroll-margin-top: 120px;
  }

  :global(section[id]) {
    scroll-margin-top: 120px;
  }

  :global(p) {
    margin: 0 0 12px;
    color: var(--cf-slate);
    line-height: 1.6;
  }

  :global(strong) {
    color: var(--cf-charcoal);
  }

  :global(main > ul) {
    list-style: none;
    padding: 0;
    margin: 14px 0 18px;
    display: grid;
    gap: 12px;
  }

  :global(main > ul > li) {
    background: var(--cf-card);
    border: 1px solid var(--cf-border);
    border-radius: 14px;
    box-shadow: var(--cf-shadow);
    padding: 14px 16px;
  }

  :global(form) {
    display: grid;
    gap: 14px;
    max-width: 620px;
    padding: 18px;
    border-radius: 16px;
    border: 1px solid var(--cf-border);
    background: rgba(255, 255, 255, 0.86);
    box-shadow: var(--cf-shadow);
  }

  :global(label) {
    display: grid;
    gap: 8px;
    font-weight: 600;
    color: var(--cf-slate);
  }

  :global(input, textarea, button) {
    font: inherit;
    padding: 11px 12px;
    border-radius: 10px;
    border: 1px solid #dfb795;
  }

  :global(input, textarea) {
    background: #fffdfb;
  }

  :global(input:focus, textarea:focus) {
    outline: none;
    border-color: var(--cf-orange);
    box-shadow: 0 0 0 3px rgba(243, 128, 32, 0.2);
  }

  :global(button) {
    background: var(--cf-orange);
    color: #fff;
    cursor: pointer;
    border-color: transparent;
    font-weight: 700;
    transition: transform 120ms ease, background-color 120ms ease, box-shadow 120ms ease;
  }

  :global(button:hover) {
    background: var(--cf-orange-deep);
    transform: translateY(-1px);
    box-shadow: 0 8px 20px rgba(216, 95, 13, 0.28);
  }

  :global(button:disabled) {
    cursor: not-allowed;
    opacity: 0.62;
    transform: none;
    box-shadow: none;
  }

  :global(button:focus-visible) {
    outline: 3px solid rgba(243, 128, 32, 0.4);
    outline-offset: 2px;
  }

  :global(main section) {
    background: rgba(255, 255, 255, 0.75);
    border: 1px solid var(--cf-border);
    border-radius: 18px;
    padding: 18px;
    box-shadow: var(--cf-shadow);
    margin-bottom: 20px;
  }

  :global(.section-nav) {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 0 0 14px;
  }

  :global(.section-nav a) {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    border: 1px solid #e7c9b2;
    background: rgba(255, 255, 255, 0.8);
    color: #8a4519;
    font-size: 0.88rem;
    font-weight: 700;
    padding: 6px 11px;
  }

  :global(.section-nav a.active-tab) {
    color: #fff;
    border-color: transparent;
    background: linear-gradient(140deg, var(--cf-orange) 0%, var(--cf-orange-deep) 100%);
  }

  :global(.breadcrumb) {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
    margin: 0 0 10px;
    font-size: 0.86rem;
    color: #8b4f30;
  }

  :global(.breadcrumb a) {
    color: #8b4f30;
    font-weight: 700;
  }

  :global(.breadcrumb .sep) {
    opacity: 0.58;
    font-weight: 700;
  }

  :global(code) {
    background: rgba(243, 128, 32, 0.12);
    border-radius: 6px;
    padding: 2px 6px;
  }

  @media (max-width: 720px) {
    .topbar-inner {
      padding: 12px 16px 14px;
    }

    :global(main) {
      padding: 22px 16px 36px;
    }

    .utility-nav,
    .primary-nav {
      display: none;
    }

    .menu-toggle {
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }

    .mobile-drawer {
      display: block;
      margin-top: 2px;
      border-top: 1px solid var(--cf-border);
      padding-top: 10px;
    }

    .mobile-drawer-nav a {
      font-size: 0.9rem;
      padding: 7px 10px;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    :global(html) {
      scroll-behavior: auto;
    }
  }
</style>

<header class="topbar">
  <div class="topbar-inner">
    <div class="utility-row">
      <div class="brand">
        <a class="brand-link" href="/" on:click={() => (mobileMenuOpen = false)}>
          <div class="brand-mark"></div>
          <p class="brand-text">Single Origin Lab</p>
        </a>
      </div>

      <nav class="utility-nav" aria-label="Utility">
        <a href="/search" class:active-nav={isActive('/search')}>Search</a>
        <a href="/account" class:active-nav={isActive('/account')}>Account</a>
        <a href="/checkout" class:active-nav={isActive('/checkout')}>Checkout</a>
      </nav>

      <button
        class="menu-toggle"
        type="button"
        aria-label="Open menu"
        aria-expanded={mobileMenuOpen}
        on:click={() => (mobileMenuOpen = !mobileMenuOpen)}
      >
        {mobileMenuOpen ? 'x' : '☰'}
      </button>
    </div>

    <nav class="primary-nav" aria-label="Primary">
      <a href="/shop" class:active-nav={isActive('/shop')}>Shop</a>
      <a href="/subscribe" class:active-nav={isActive('/subscribe')}>Subscriptions</a>
      <a href="/guides" class:active-nav={isActive('/guides')}>Learn</a>
      <a href="/assistant" class:active-nav={isActive('/assistant')}>Assistant</a>
      <a href="/contact" class:active-nav={isActive('/contact')}>Support</a>
      <a href="/admin" class:active-nav={isActive('/admin')} class="admin-link">Admin</a>
    </nav>

    {#if mobileMenuOpen}
      <div class="mobile-drawer">
        <h3>Shop</h3>
        <nav class="mobile-drawer-nav" aria-label="Mobile shop">
          <a href="/shop" class:active-nav={isActive('/shop')} on:click={() => (mobileMenuOpen = false)}>Catalog</a>
          <a href="/subscribe" class:active-nav={isActive('/subscribe')} on:click={() => (mobileMenuOpen = false)}>Subscriptions</a>
          <a href="/checkout" class:active-nav={isActive('/checkout')} on:click={() => (mobileMenuOpen = false)}>Checkout</a>
        </nav>

        <h3>Learn</h3>
        <nav class="mobile-drawer-nav" aria-label="Mobile learn">
          <a href="/guides" class:active-nav={isActive('/guides')} on:click={() => (mobileMenuOpen = false)}>Guides</a>
          <a href="/assistant" class:active-nav={isActive('/assistant')} on:click={() => (mobileMenuOpen = false)}>Assistant</a>
        </nav>

        <h3>Account</h3>
        <nav class="mobile-drawer-nav" aria-label="Mobile account">
          <a href="/login" class:active-nav={isActive('/login')} on:click={() => (mobileMenuOpen = false)}>Login</a>
          <a href="/register" class:active-nav={isActive('/register')} on:click={() => (mobileMenuOpen = false)}>Register</a>
          <a href="/account" class:active-nav={isActive('/account')} on:click={() => (mobileMenuOpen = false)}>Account</a>
        </nav>

        <h3>Admin</h3>
        <nav class="mobile-drawer-nav" aria-label="Mobile admin">
          <a href="/admin" class:active-nav={isActive('/admin')} on:click={() => (mobileMenuOpen = false)}>Admin Console</a>
        </nav>
      </div>
    {/if}
  </div>
</header>

<main>
  <slot />
</main>
