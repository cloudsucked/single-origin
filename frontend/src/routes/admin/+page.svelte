<script lang="ts">
  import { onMount } from 'svelte';
  import { apiBaseUrl } from '$lib/config';
  import { setAuth, clearAuth } from '$lib/auth';

  type Dashboard = {
    users: number;
    products: number;
    orders: number;
    subscriptions: number;
    contacts: number;
    revenue: number;
  };

  type User = { id: number; email: string; name: string; role: string };

  type Product = {
    id: number;
    name: string;
    slug: string;
    category: string;
    price: number;
    origin?: string;
    roast_level?: string;
    description: string;
  };

  type Order = { id: number; user_email: string; total: number; status: string };

  type Subscription = { id: number; user_email: string; plan: string; status: string };

  type AuditLog = {
    id: number;
    actor: string;
    action: string;
    target_type: string | null;
    target_id: string | null;
    severity: string;
    created_at: string;
  };

  let adminEmail = 'admin@singleorigin.example';
  let adminPassword = '';
  let adminToken = '';
  let loading = false;
  let error = '';
  let currentAdminSection = 'overview';

  let dashboard: Dashboard | null = null;
  let users: User[] = [];
  let products: Product[] = [];
  let orders: Order[] = [];
  let subscriptions: Subscription[] = [];
  let auditLogs: AuditLog[] = [];

  // ── Product state ─────────────────────────────────────────────────────────
  let newProduct: Omit<Product, 'id'> = {
    name: '', slug: '', origin: '', roast_level: 'medium',
    category: 'beans', description: '', price: 0
  };
  let editingProduct: Product | null = null;

  // ── User state ────────────────────────────────────────────────────────────
  let newUser = { email: '', name: '', password: '', role: 'customer' };
  let editingUser: User | null = null;
  let showCreateUser = false;

  // ── Generic fetch helper ──────────────────────────────────────────────────
  async function request<T>(path: string, init?: RequestInit): Promise<T> {
    const res = await fetch(`${apiBaseUrl}${path}`, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...(adminToken ? { Authorization: `Bearer ${adminToken}` } : {}),
        ...(init?.headers ?? {})
      }
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`${res.status} ${text}`);
    }
    return (await res.json()) as T;
  }

  // ── Auth ──────────────────────────────────────────────────────────────────
  async function login() {
    loading = true; error = '';
    try {
      const payload = await request<{ token: string; user: { id: number; email: string; name: string; role: string } }>('/api/v1/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email: adminEmail, password: adminPassword })
      });
      adminToken = payload.token;
      // Store in shared auth store so the nav bar and other pages see the session
      setAuth(payload.token, payload.user);
      await loadAdminData();
    } catch (err) {
      error = String(err);
    } finally {
      loading = false;
    }
  }

  function logout() {
    adminToken = '';
    currentAdminSection = 'admin-login';
    dashboard = null; users = []; products = [];
    orders = []; subscriptions = []; auditLogs = [];
    // Clear shared auth store so nav bar and other pages also see the sign-out
    clearAuth();
  }

  // ── Load all data ─────────────────────────────────────────────────────────
  async function loadAdminData() {
    loading = true; error = '';
    try {
      const [d, u, p, o, s, l] = await Promise.all([
        request<Dashboard>('/api/v1/admin/dashboard'),
        request<User[]>('/api/v1/admin/users'),
        request<Product[]>('/api/v1/admin/products'),
        request<Order[]>('/api/v1/admin/orders'),
        request<Subscription[]>('/api/v1/admin/subscriptions'),
        request<AuditLog[]>('/api/v1/admin/audit-logs')
      ]);
      dashboard = d; users = u; products = p;
      orders = o; subscriptions = s; auditLogs = l;
    } catch (err) {
      error = String(err);
    } finally {
      loading = false;
    }
  }

  // ── Products ──────────────────────────────────────────────────────────────
  async function createProduct() {
    await request('/api/v1/admin/products', {
      method: 'POST',
      body: JSON.stringify({ ...newProduct, origin: newProduct.origin || null, roast_level: newProduct.roast_level || null })
    });
    newProduct = { name: '', slug: '', origin: '', roast_level: 'medium', category: 'beans', description: '', price: 0 };
    await loadAdminData();
  }

  function startEditProduct(p: Product) {
    editingProduct = { ...p };
  }

  function cancelEditProduct() {
    editingProduct = null;
  }

  async function saveEditProduct() {
    if (!editingProduct) return;
    await request(`/api/v1/admin/products/${editingProduct.id}`, {
      method: 'PUT',
      body: JSON.stringify({
        name: editingProduct.name,
        slug: editingProduct.slug,
        origin: editingProduct.origin || null,
        roast_level: editingProduct.roast_level || null,
        category: editingProduct.category,
        description: editingProduct.description,
        price: editingProduct.price
      })
    });
    editingProduct = null;
    await loadAdminData();
  }

  async function deleteProduct(id: number) {
    if (!confirm('Delete this product?')) return;
    await request(`/api/v1/admin/products/${id}`, { method: 'DELETE' });
    await loadAdminData();
  }

  // ── Users ─────────────────────────────────────────────────────────────────
  async function createUserAdmin() {
    await request('/api/v1/admin/users', {
      method: 'POST',
      body: JSON.stringify(newUser)
    });
    newUser = { email: '', name: '', password: '', role: 'customer' };
    showCreateUser = false;
    await loadAdminData();
  }

  function startEditUser(u: User) {
    editingUser = { ...u };
  }

  function cancelEditUser() {
    editingUser = null;
  }

  async function saveEditUser() {
    if (!editingUser) return;
    await request(`/api/v1/admin/users/${editingUser.id}`, {
      method: 'PUT',
      body: JSON.stringify({ email: editingUser.email, name: editingUser.name, role: editingUser.role })
    });
    editingUser = null;
    await loadAdminData();
  }

  async function deleteUserAdmin(id: number, email: string) {
    if (!confirm(`Delete user ${email}? This cannot be undone.`)) return;
    await request(`/api/v1/admin/users/${id}`, { method: 'DELETE' });
    await loadAdminData();
  }

  // ── Orders ────────────────────────────────────────────────────────────────
  async function updateOrderStatus(id: number, status: string) {
    await request(`/api/v1/admin/orders/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status })
    });
    await loadAdminData();
  }

  // ── Subscriptions ─────────────────────────────────────────────────────────
  async function updateSubscriptionStatus(id: number, status: string) {
    await request(`/api/v1/admin/subscriptions/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status })
    });
    await loadAdminData();
  }

  // ── Helpers ───────────────────────────────────────────────────────────────
  function autoSlug(name: string): string {
    return name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
  }

  function severityClass(s: string): string {
    if (s === 'high' || s === 'critical') return 'tag-red';
    if (s === 'medium') return 'tag-orange';
    if (s === 'low') return 'tag-blue';
    return 'tag-grey';
  }

  function roleClass(r: string): string {
    if (r === 'admin') return 'tag-red';
    if (r === 'wholesale_partner') return 'tag-blue';
    return 'tag-grey';
  }

  function fmtDate(iso: string): string {
    try { return new Date(iso).toLocaleString(); } catch { return iso; }
  }

  onMount(() => {
    const syncSection = () => {
      const hash = window.location.hash.replace('#', '');
      currentAdminSection = hash || (adminToken ? 'overview' : 'admin-login');
    };
    syncSection();
    window.addEventListener('hashchange', syncSection);

    const token = localStorage.getItem('so_token');
    if (!token) {
      currentAdminSection = 'admin-login';
      return () => window.removeEventListener('hashchange', syncSection);
    }
    adminToken = token;
    void loadAdminData();
    return () => window.removeEventListener('hashchange', syncSection);
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
      <a href="#admin-login" class:active-tab={currentAdminSection === 'admin-login'}>Sign in</a>
    {:else}
      <a href="#overview"      class:active-tab={currentAdminSection === 'overview'}>Overview</a>
      <a href="#users"         class:active-tab={currentAdminSection === 'users'}>Users</a>
      <a href="#products"      class:active-tab={currentAdminSection === 'products'}>Products</a>
      <a href="#orders"        class:active-tab={currentAdminSection === 'orders'}>Orders</a>
      <a href="#subscriptions" class:active-tab={currentAdminSection === 'subscriptions'}>Subscriptions</a>
      <a href="#audit-logs"    class:active-tab={currentAdminSection === 'audit-logs'}>Audit logs</a>
    {/if}
  </nav>
  <p>Manage catalog, orders, subscriptions, and users.</p>
</section>

<!-- ── Login ────────────────────────────────────────────────────────────── -->
{#if !adminToken}
  <section>
    <h2 id="admin-login">Admin Login</h2>
    <form on:submit|preventDefault={login}>
      <label>Email     <input type="email"    bind:value={adminEmail}    required /></label>
      <label>Password  <input type="password" bind:value={adminPassword} required /></label>
      <button type="submit" disabled={loading}>{loading ? 'Signing in…' : 'Sign in as admin'}</button>
    </form>
  </section>
{:else}

<!-- ── Toolbar ──────────────────────────────────────────────────────────── -->
  <section>
    <div class="toolbar">
      <p class="session">Signed in as admin</p>
      <div class="actions">
        <button type="button" on:click={loadAdminData} disabled={loading}>Refresh</button>
        <button type="button" class="secondary" on:click={logout}>Sign out</button>
      </div>
    </div>
  </section>

  {#if dashboard}

  <!-- ── Overview ─────────────────────────────────────────────────────── -->
  <section>
    <h2 id="overview">Overview</h2>
    <div class="stats-grid">
      <article><p class="stat-label">Users</p>         <p class="stat-value">{dashboard.users}</p></article>
      <article><p class="stat-label">Products</p>      <p class="stat-value">{dashboard.products}</p></article>
      <article><p class="stat-label">Orders</p>        <p class="stat-value">{dashboard.orders}</p></article>
      <article><p class="stat-label">Subscriptions</p> <p class="stat-value">{dashboard.subscriptions}</p></article>
      <article><p class="stat-label">Contacts</p>      <p class="stat-value">{dashboard.contacts}</p></article>
      <article><p class="stat-label">Revenue</p>       <p class="stat-value">${dashboard.revenue.toFixed(2)}</p></article>
    </div>
  </section>

  <!-- ── Users ─────────────────────────────────────────────────────────── -->
  <section>
    <h2 id="users">Users</h2>
    <div class="section-toolbar">
      <button type="button" class="small" on:click={() => (showCreateUser = !showCreateUser)}>
        {showCreateUser ? 'Cancel' : '+ New user'}
      </button>
    </div>

    {#if showCreateUser}
      <form class="inline-form" on:submit|preventDefault={createUserAdmin}>
        <label>Email     <input type="email"    bind:value={newUser.email}    required /></label>
        <label>Name      <input type="text"     bind:value={newUser.name}     required /></label>
        <label>Password  <input type="password" bind:value={newUser.password} required /></label>
        <label>Role
          <select bind:value={newUser.role}>
            <option value="customer">customer</option>
            <option value="wholesale_partner">wholesale_partner</option>
            <option value="admin">admin</option>
          </select>
        </label>
        <button type="submit">Create user</button>
      </form>
    {/if}

    <ul class="collection-list">
      {#each users as user (user.id)}
        <li class="collection-item">
          {#if editingUser?.id === user.id}
            <form class="inline-edit-form" on:submit|preventDefault={saveEditUser}>
              <label>Email <input type="email" bind:value={editingUser.email} required /></label>
              <label>Name  <input type="text"  bind:value={editingUser.name}  required /></label>
              <label>Role
                <select bind:value={editingUser.role}>
                  <option value="customer">customer</option>
                  <option value="wholesale_partner">wholesale_partner</option>
                  <option value="admin">admin</option>
                </select>
              </label>
              <div class="edit-actions">
                <button type="submit">Save</button>
                <button type="button" class="secondary" on:click={cancelEditUser}>Cancel</button>
              </div>
            </form>
          {:else}
            <div class="item-main">
              <p class="item-title">#{user.id} {user.name}</p>
              <p>{user.email}</p>
            </div>
            <div class="item-actions">
              <span class="tag {roleClass(user.role)}">{user.role}</span>
              <button type="button" class="small" on:click={() => startEditUser(user)}>Edit</button>
              <button type="button" class="small danger" on:click={() => deleteUserAdmin(user.id, user.email)}>Delete</button>
            </div>
          {/if}
        </li>
      {/each}
    </ul>
  </section>

  <!-- ── Products ──────────────────────────────────────────────────────── -->
  <section>
    <h2 id="products">Products</h2>

    <details class="create-panel">
      <summary>+ New product</summary>
      <form class="product-form" on:submit|preventDefault={createProduct}>
        <label>Name
          <input bind:value={newProduct.name} required
            on:input={() => { if (!newProduct.slug) newProduct.slug = autoSlug(newProduct.name); }} />
        </label>
        <label>Slug        <input bind:value={newProduct.slug}        required /></label>
        <label>Origin      <input bind:value={newProduct.origin} /></label>
        <label>Roast       <input bind:value={newProduct.roast_level} /></label>
        <label>Category    <input bind:value={newProduct.category}    required /></label>
        <label>Price       <input type="number" step="0.01" bind:value={newProduct.price} required /></label>
        <label class="span-full">Description
          <textarea rows="2" bind:value={newProduct.description} required></textarea>
        </label>
        <button type="submit" class="span-full">Create product</button>
      </form>
    </details>

    <ul class="collection-list">
      {#each products as product (product.id)}
        <li class="collection-item col-stack">
          {#if editingProduct?.id === product.id}
            <form class="product-form" on:submit|preventDefault={saveEditProduct}>
              <label>Name        <input bind:value={editingProduct.name}        required /></label>
              <label>Slug        <input bind:value={editingProduct.slug}        required /></label>
              <label>Origin      <input bind:value={editingProduct.origin} /></label>
              <label>Roast       <input bind:value={editingProduct.roast_level} /></label>
              <label>Category    <input bind:value={editingProduct.category}    required /></label>
              <label>Price       <input type="number" step="0.01" bind:value={editingProduct.price} required /></label>
              <label class="span-full">Description
                <textarea rows="2" bind:value={editingProduct.description} required></textarea>
              </label>
              <div class="edit-actions span-full">
                <button type="submit">Save changes</button>
                <button type="button" class="secondary" on:click={cancelEditProduct}>Cancel</button>
              </div>
            </form>
          {:else}
            <div class="item-row">
              <div class="item-main">
                <p class="item-title">#{product.id} {product.name}</p>
                <p>{product.slug} • ${product.price.toFixed(2)} • {product.category}</p>
              </div>
              <div class="item-actions">
                <button type="button" class="small" on:click={() => startEditProduct(product)}>Edit</button>
                <button type="button" class="small danger" on:click={() => deleteProduct(product.id)}>Delete</button>
              </div>
            </div>
          {/if}
        </li>
      {/each}
    </ul>
  </section>

  <!-- ── Orders ────────────────────────────────────────────────────────── -->
  <section>
    <h2 id="orders">Orders</h2>
    <ul class="collection-list">
      {#each orders as order (order.id)}
        <li class="collection-item">
          <div class="item-main">
            <p class="item-title">#{order.id} • {order.user_email}</p>
            <p>${order.total.toFixed(2)}</p>
          </div>
          <div class="item-actions">
            <span class="tag {order.status === 'DELIVERED' ? 'tag-green' : 'tag-orange'}">{order.status}</span>
            <button type="button" class="small" on:click={() => updateOrderStatus(order.id, 'PROCESSING')}>Processing</button>
            <button type="button" class="small" on:click={() => updateOrderStatus(order.id, 'DELIVERED')}>Delivered</button>
          </div>
        </li>
      {/each}
    </ul>
  </section>

  <!-- ── Subscriptions ─────────────────────────────────────────────────── -->
  <section>
    <h2 id="subscriptions">Subscriptions</h2>
    <ul class="collection-list">
      {#each subscriptions as sub (sub.id)}
        <li class="collection-item">
          <div class="item-main">
            <p class="item-title">#{sub.id} • {sub.user_email}</p>
            <p>{sub.plan}</p>
          </div>
          <div class="item-actions">
            <span class="tag {sub.status === 'ACTIVE' ? 'tag-green' : 'tag-grey'}">{sub.status}</span>
            <button type="button" class="small" on:click={() => updateSubscriptionStatus(sub.id, 'PAUSED')}>Pause</button>
            <button type="button" class="small" on:click={() => updateSubscriptionStatus(sub.id, 'ACTIVE')}>Activate</button>
          </div>
        </li>
      {/each}
    </ul>
  </section>

  <!-- ── Audit Logs ─────────────────────────────────────────────────────── -->
  <section>
    <h2 id="audit-logs">Audit Logs</h2>
    {#if auditLogs.length === 0}
      <p>No audit events recorded yet.</p>
    {:else}
      <ul class="collection-list">
        {#each auditLogs as log (log.id)}
          <li class="collection-item">
            <div class="item-main">
              <p class="item-title">{log.action}</p>
              <p class="item-meta">
                {log.actor}
                {#if log.target_type} · {log.target_type} #{log.target_id}{/if}
                · {fmtDate(log.created_at)}
              </p>
            </div>
            <span class="tag {severityClass(log.severity)}">{log.severity}</span>
          </li>
        {/each}
      </ul>
    {/if}
  </section>

  {/if}
{/if}

{#if error}
  <section><p class="error">Error: {error}</p></section>
{/if}

<style>
  .toolbar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .session { margin: 0; font-weight: 700; }

  .actions, .item-actions, .edit-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    align-items: center;
  }

  .section-toolbar {
    margin-bottom: 12px;
  }

  .secondary {
    background: #fff;
    color: #8a4519;
    border: 1px solid #e4b892;
  }

  .small {
    font-size: 0.8rem;
    padding: 5px 10px;
    border-radius: 8px;
  }

  .danger { background: #cf4022; }
  .danger:hover { background: #ab3219; }

  /* Stats */
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

  /* Create-product collapsible */
  .create-panel {
    margin-bottom: 14px;
    border: 1px solid #f2ccb0;
    border-radius: 12px;
    background: #fff;
    padding: 12px;
  }

  .create-panel summary {
    cursor: pointer;
    font-weight: 700;
    color: #8a3d10;
    font-size: 0.9rem;
    list-style: none;
  }

  .create-panel[open] summary {
    margin-bottom: 12px;
  }

  /* Product / inline forms */
  .product-form, .inline-form {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 10px;
    max-width: none;
    border: none;
    padding: 0;
    background: transparent;
    box-shadow: none;
  }

  .span-full { grid-column: 1 / -1; }

  .inline-form {
    margin-bottom: 14px;
    border: 1px solid #f2ccb0 !important;
    border-radius: 12px !important;
    padding: 14px !important;
    background: rgba(255,255,255,0.9) !important;
  }

  .inline-edit-form {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 10px;
    width: 100%;
  }

  /* Collection list */
  .collection-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: grid;
    gap: 10px;
  }

  .collection-item {
    border: 1px solid #f2ccb0;
    border-radius: 12px;
    background: #fff;
    padding: 12px;
  }

  .item-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
  }

  .collection-item:not(.col-stack) {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
  }

  .item-main { flex: 1; min-width: 0; }

  .item-title {
    margin: 0 0 2px;
    font-weight: 700;
    color: #2e1f16;
  }

  .item-meta {
    margin: 2px 0 0;
    font-size: 0.82rem;
    color: #7a6c62;
  }

  /* Tags */
  .tag {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    border: 1px solid #f0b88d;
    background: #fff2e7;
    color: #8a4519;
    font-size: 0.78rem;
    font-weight: 700;
    padding: 3px 10px;
    white-space: nowrap;
  }

  .tag-green  { background: #e8f5ee; border-color: #a3d4b5; color: #1a6b3c; }
  .tag-orange { background: #fff2e7; border-color: #f0b88d; color: #8a4519; }
  .tag-blue   { background: #e8f0fb; border-color: #9ab8ef; color: #1a3a7c; }
  .tag-grey   { background: #f5f5f5; border-color: #ccc;    color: #555; }
  .tag-red    { background: #fce8e6; border-color: #e5a09a; color: #8b1a12; }

  .error { color: #b0270f; font-weight: 700; }

  select {
    font: inherit;
    padding: 10px 12px;
    border-radius: 10px;
    border: 1px solid #dfb795;
    background: #fffdfb;
    width: 100%;
  }
</style>
