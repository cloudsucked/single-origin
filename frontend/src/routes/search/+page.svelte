<script lang="ts">
  export let data: { query: string; results: Array<{ type: string; id: number; name: string }> };
</script>

<section>
  <h1>Search</h1>
  <p>Find products, entities, and IDs exposed through the lab search endpoint.</p>
  <form class="search-form" method="GET" action="/search">
    <label for="q">Search query</label>
    <div class="search-row">
      <input id="q" name="q" value={data.query} placeholder="Try: yirgacheffe" />
      <button type="submit">Search</button>
    </div>
  </form>
</section>

<section>
  <h2>Results</h2>
  <p>{data.results.length} matches for <strong>{data.query || '(empty)'}</strong></p>

  {#if data.results.length === 0}
    <p>No results yet.</p>
  {:else}
    <ul class="results-list">
      {#each data.results as result}
        <li>
          <p class="result-name">{result.name}</p>
          <p>{result.type} #{result.id}</p>
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
    padding: 12px;
  }

  .result-name {
    margin: 0 0 4px;
    font-weight: 700;
    color: #2e1f16;
  }
</style>
