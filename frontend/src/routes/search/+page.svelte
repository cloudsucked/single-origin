<script lang="ts">
  export let data: { query: string; results: Array<{ type: string; id: number; name: string; slug?: string }> };
</script>

<section>
  <h1>Search</h1>
  <form class="search-form" method="GET" action="/search">
    <label for="q">Search query</label>
    <div class="search-row">
      <input id="q" name="q" value={data.query} placeholder="Try: yirgacheffe, ethiopia, espresso..." />
      <button type="submit">Search</button>
    </div>
  </form>
</section>

<section>
  <h2>Results</h2>
  {#if !data.query}
    <p>Enter a search term above to find products.</p>
  {:else if data.results.length === 0}
    <p>No results found for <strong>{data.query}</strong>. Try a different term.</p>
  {:else}
    <p class="result-count">{data.results.length} result{data.results.length !== 1 ? 's' : ''} for <strong>{data.query}</strong></p>
    <ul class="results-list">
      {#each data.results as result}
        <li>
          <a href="/shop/{result.slug ?? result.name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')}" class="result-link">
            <p class="result-name">{result.name}</p>
            <p class="result-meta">{result.type} #{result.id}</p>
          </a>
        </li>
      {/each}
    </ul>
  {/if}
</section>

<style>
  .search-form {
    max-width: none;
  }

  .search-row {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }

  .search-row input {
    flex: 1 1 260px;
  }

  .result-count {
    font-size: 0.9rem;
    color: #8b4f30;
    margin-bottom: 10px;
  }

  .results-list {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 10px;
  }

  .results-list li {
    border: 1px solid #f2ccb0;
    border-radius: 12px;
    background: #fff;
    overflow: hidden;
  }

  .result-link {
    display: block;
    padding: 14px;
    color: inherit;
    text-decoration: none;
    transition: background-color 120ms ease;
  }

  .result-link:hover {
    background: rgba(243, 128, 32, 0.06);
  }

  .result-name {
    margin: 0 0 4px;
    font-weight: 700;
    color: #2e1f16;
  }

  .result-meta {
    margin: 0;
    font-size: 0.84rem;
    color: #8b4f30;
    text-transform: capitalize;
  }
</style>
