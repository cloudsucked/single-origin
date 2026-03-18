<script lang="ts">
  import { onMount } from 'svelte';

  import { apiBaseUrl } from '$lib/config';

  type Dashboard = {
    users: number;
    products: number;
    orders: number;
    subscriptions: number;
    contacts: number;
    revenue: number;
  };

  let adminEmail = 'admin@singleorigin.example';
  let adminPassword = '';
  let adminToken = '';
  let loading = false;
  let error = '';
  let currentAdminSection = 'overview';

  let dashboard: Dashboard | null = null;
  let users: Array<{ id: number; email: string; name: string; role: string }> = [];
  let products: Array<{
    id: number;
    name: string;
    slug: string;
    category: string;
    price: number;
    origin?: string;
    roast_level?: string;
    description: string;
  }> = [];
  let orders: Array<{ id: number; user_email: string; total: number; status: string }> = [];
  let subscriptions: Array<{ id: number; user_email: string; plan: string; status: string }> = [];
  let auditLogs: Array<{ id: string; actor: string; action: string; severity: string }> = [];

  let newProduct = {
    name: '',
    slug: '',
    origin: '',
    roast_level: 'medium',
    category: 'beans',
    description: '',
    price: 0
  };

  async function request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${apiBaseUrl}${path}`, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...(adminToken ? { Authorization: `Bearer ${adminToken}` } : {}),
        ...(init?.headers || {})
      }
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(`${response.status} ${text}`);
    }
    return (await response.json()) as T;
  }

  async function login() {
    loading = true;
    error = '';
    try {
      const payload = await request<{ token: string }>('/api/v1/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email: adminEmail, password: adminPassword })
      });
      adminToken = payload.token;
      localStorage.setItem('single-origin-admin-token', adminToken);
      await loadAdminData();
    } catch (err) {
      error = String(err);
    } finally {
      loading = false;
    }
  }

  async function loadAdminData() {
    loading = true;
    error = '';
    try {
      const [dashboardData, usersData, productsData, ordersData, subscriptionsData, logsData] = await Promise.all([
        request<Dashboard>('/api/v1/admin/dashboard'),
        request<Array<{ id: number; email: string; name: string; role: string }>>('/api/v1/admin/users'),
        request<Array<any>>('/api/v1/admin/products'),
        request<Array<any>>('/api/v1/admin/orders'),
        request<Array<any>>('/api/v1/admin/subscriptions'),
        request<Array<any>>('/api/v1/admin/audit-logs')
      ]);
      dashboard = dashboardData;
      users = usersData;
      products = productsData;
      orders = ordersData;
      subscriptions = subscriptionsData;
      auditLogs = logsData;
    } catch (err) {
      error = String(err);
    } finally {
      loading = false;
    }
  }

  async function createProduct() {
    await request('/api/v1/admin/products', {
      method: 'POST',
      body: JSON.stringify({
        ...newProduct,
        origin: newProduct.origin || null,
        roast_level: newProduct.roast_level || null
      })
    });
    newProduct = {
      name: '',
      slug: '',
      origin: '',
      roast_level: 'medium',
      category: 'beans',
      description: '',
      price: 0
    };
    await loadAdminData();
  }

  async function updateOrderStatus(orderId: number, status: string) {
    await request(`/api/v1/admin/orders/${orderId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status })
    });
    await loadAdminData();
  }

  async function updateSubscriptionStatus(subscriptionId: number, status: string) {
    await request(`/api/v1/admin/subscriptions/${subscriptionId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status })
    });
    await loadAdminData();
  }

  async function deleteProduct(productId: number) {
    await request(`/api/v1/admin/products/${productId}`, {
      method: 'DELETE'
    });
    await loadAdminData();
  }

  function logout() {
    adminToken = '';
    currentAdminSection = 'admin-login';
    dashboard = null;
    users = [];
    products = [];
    orders = [];
    subscriptions = [];
    auditLogs = [];
    localStorage.removeItem('single-origin-admin-token');
  }

  onMount(() => {
    const syncSectionFromHash = () => {
      const hash = window.location.hash.replace('#', '');
      currentAdminSection = hash || (adminToken ? 'overview' : 'admin-login');
    };

    syncSectionFromHash();
    window.addEventListener('hashchange', syncSectionFromHash);

    const token = localStorage.getItem('single-origin-admin-token');
    if (!token) {
      currentAdminSection = 'admin-login';
      return () => window.removeEventListener('hashchange', syncSectionFromHash);
    }

    adminToken = token;
    void loadAdminData();

    return () => {
      window.removeEventListener('hashchange', syncSectionFromHash);
    };
  });
</script>

<section>
  <nav class="breadcrumb" aria-label="Breadcrumb">
    <a href="/">Home</a>
    <span class="sep">/</span>
    <span aria-current="page">Admin</span>
  </nav>
  <h1>Admin Portal</h1>
  <nav class="section-nav" aria-label="Admin sections">
    {#if !adminToken}
      <a
        href="#admin-login"
        class:active-tab={currentAdminSection === 'admin-login'}
        aria-current={currentAdminSection === 'admin-login' ? 'page' : undefined}
      >
        Sign in
      </a>
    {:else}
      <a href="#overview" class:active-tab={currentAdminSection === 'overview'} aria-current={currentAdminSection === 'overview' ? 'page' : undefined}>Overview</a>
      <a
        href="#create-product"
        class:active-tab={currentAdminSection === 'create-product'}
        aria-current={currentAdminSection === 'create-product' ? 'page' : undefined}
      >
        Create product
      </a>
      <a href="#users" class:active-tab={currentAdminSection === 'users'} aria-current={currentAdminSection === 'users' ? 'page' : undefined}>Users</a>
      <a href="#products" class:active-tab={currentAdminSection === 'products'} aria-current={currentAdminSection === 'products' ? 'page' : undefined}>Products</a>
      <a href="#orders" class:active-tab={currentAdminSection === 'orders'} aria-current={currentAdminSection === 'orders' ? 'page' : undefined}>Orders</a>
      <a
        href="#subscriptions"
        class:active-tab={currentAdminSection === 'subscriptions'}
        aria-current={currentAdminSection === 'subscriptions' ? 'page' : undefined}
      >
        Subscriptions
      </a>
      <a href="#audit-logs" class:active-tab={currentAdminSection === 'audit-logs'} aria-current={currentAdminSection === 'audit-logs' ? 'page' : undefined}>Audit logs</a>
    {/if}
  </nav>
  <p>Manage catalog, orders, subscriptions, and users from one modern control center.</p>
</section>

{#if !adminToken}
  <section>
    <h2 id="admin-login">Admin Login</h2>
    <form on:submit|preventDefault={login}>
      <label>
        Email
        <input type="email" bind:value={adminEmail} required />
      </label>
      <label>
        Password
        <input type="password" bind:value={adminPassword} required />
      </label>
      <button type="submit" disabled={loading}>{loading ? 'Signing in...' : 'Sign in as admin'}</button>
    </form>
  </section>
{:else}
  <section>
    <div class="toolbar">
      <p class="session">Signed in as admin</p>
      <div class="actions">
        <button type="button" on:click={loadAdminData} disabled={loading}>Refresh data</button>
        <button type="button" class="secondary" on:click={logout}>Sign out</button>
      </div>
    </div>
  </section>

  {#if dashboard}
    <section>
      <h2 id="overview">Overview</h2>
      <div class="stats-grid">
        <article><p class="stat-label">Users</p><p class="stat-value">{dashboard.users}</p></article>
        <article><p class="stat-label">Products</p><p class="stat-value">{dashboard.products}</p></article>
        <article><p class="stat-label">Orders</p><p class="stat-value">{dashboard.orders}</p></article>
        <article><p class="stat-label">Subscriptions</p><p class="stat-value">{dashboard.subscriptions}</p></article>
        <article><p class="stat-label">Contacts</p><p class="stat-value">{dashboard.contacts}</p></article>
        <article><p class="stat-label">Revenue</p><p class="stat-value">${dashboard.revenue.toFixed(2)}</p></article>
      </div>
    </section>

    <section>
      <h2 id="create-product">Create Product</h2>
      <form class="product-form" on:submit|preventDefault={createProduct}>
        <label>Name <input bind:value={newProduct.name} required /></label>
        <label>Slug <input bind:value={newProduct.slug} required /></label>
        <label>Origin <input bind:value={newProduct.origin} /></label>
        <label>Roast <input bind:value={newProduct.roast_level} /></label>
        <label>Category <input bind:value={newProduct.category} required /></label>
        <label>Description <textarea rows="3" bind:value={newProduct.description} required></textarea></label>
        <label>Price <input type="number" step="0.01" bind:value={newProduct.price} required /></label>
        <button type="submit">Create product</button>
      </form>
    </section>

    <section>
      <h2 id="users">Users</h2>
      <ul class="collection-list">
        {#each users as user}
          <li>
            <div>
              <p class="item-title">#{user.id} {user.name}</p>
              <p>{user.email}</p>
            </div>
            <span class="tag">{user.role}</span>
          </li>
        {/each}
      </ul>
    </section>

    <section>
      <h2 id="products">Products</h2>
      <ul class="collection-list">
        {#each products as product}
          <li>
            <div>
              <p class="item-title">#{product.id} {product.name}</p>
              <p>{product.slug} • ${product.price.toFixed(2)}</p>
            </div>
            <button type="button" class="danger" on:click={() => deleteProduct(product.id)}>Delete</button>
          </li>
        {/each}
      </ul>
    </section>

    <section>
      <h2 id="orders">Orders</h2>
      <ul class="collection-list">
        {#each orders as order}
          <li>
            <div>
              <p class="item-title">#{order.id} • {order.user_email}</p>
              <p>${order.total.toFixed(2)} • {order.status}</p>
            </div>
            <div class="actions">
              <button type="button" on:click={() => updateOrderStatus(order.id, 'PROCESSING')}>Processing</button>
              <button type="button" on:click={() => updateOrderStatus(order.id, 'DELIVERED')}>Delivered</button>
            </div>
          </li>
        {/each}
      </ul>
    </section>

    <section>
      <h2 id="subscriptions">Subscriptions</h2>
      <ul class="collection-list">
        {#each subscriptions as subscription}
          <li>
            <div>
              <p class="item-title">#{subscription.id} • {subscription.user_email}</p>
              <p>{subscription.plan}</p>
            </div>
            <div class="actions">
              <span class="tag">{subscription.status}</span>
              <button type="button" on:click={() => updateSubscriptionStatus(subscription.id, 'PAUSED')}>Pause</button>
              <button type="button" on:click={() => updateSubscriptionStatus(subscription.id, 'ACTIVE')}>Activate</button>
            </div>
          </li>
        {/each}
      </ul>
    </section>

    <section>
      <h2 id="audit-logs">Audit Logs</h2>
      <ul class="collection-list">
        {#each auditLogs as log}
          <li>
            <div>
              <p class="item-title">{log.actor}</p>
              <p>{log.action}</p>
            </div>
            <span class="tag">{log.severity}</span>
          </li>
        {/each}
      </ul>
    </section>
  {/if}
{/if}

{#if error}
  <section>
    <p class="error">Error: {error}</p>
  </section>
{/if}

<style>
  .toolbar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .session {
    margin: 0;
    font-weight: 700;
  }

  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .secondary {
    background: #fff;
    color: #8a4519;
    border: 1px solid #e4b892;
  }

  .danger {
    background: #cf4022;
  }

  .danger:hover {
    background: #ab3219;
  }

  .stats-grid {
    display: grid;
    gap: 10px;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  }

  .stats-grid article {
    border: 1px solid #f2ccb0;
    border-radius: 12px;
    padding: 12px;
    background: #fff;
  }

  .stat-label {
    margin: 0;
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #7a6c62;
  }

  .stat-value {
    margin: 2px 0 0;
    font-size: 1.2rem;
    font-weight: 800;
    color: #8a3d10;
  }

  .product-form {
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    max-width: none;
  }

  .product-form textarea,
  .product-form button {
    grid-column: 1 / -1;
  }

  .collection-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: grid;
    gap: 10px;
  }

  .collection-list li {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    border: 1px solid #f2ccb0;
    border-radius: 12px;
    background: #fff;
    padding: 12px;
  }

  .item-title {
    margin: 0 0 2px;
    font-weight: 700;
    color: #2e1f16;
  }

  .tag {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    border: 1px solid #f0b88d;
    background: #fff2e7;
    color: #8a4519;
    font-size: 0.8rem;
    font-weight: 700;
    padding: 4px 10px;
  }

  .error {
    color: #b0270f;
    font-weight: 700;
  }
</style>
