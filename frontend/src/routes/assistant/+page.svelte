<script lang="ts">
  import { apiBaseUrl } from '$lib/config';

  let prompt = 'I like fruity light roasts. What should I try?';
  let responseText = '';
  let loading = false;

  async function askAssistant() {
    loading = true;
    responseText = '';
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/ai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'brew-assistant-v1',
          messages: [{ role: 'user', content: prompt }]
        })
      });
      const data = await response.json();
      responseText = data?.choices?.[0]?.message?.content || 'No response';
    } catch (error) {
      responseText = `Request failed: ${String(error)}`;
    } finally {
      loading = false;
    }
  }
</script>

<section>
  <h1>Brew Assistant</h1>
  <p>Test recommendation prompts, prompt-injection patterns, and PII-like strings.</p>
  <form class="assistant-form" on:submit|preventDefault={askAssistant}>
    <label for="assistant-prompt">Prompt</label>
    <textarea id="assistant-prompt" bind:value={prompt} rows="6"></textarea>
    <button type="submit" disabled={loading}>{loading ? 'Asking...' : 'Ask Assistant'}</button>
  </form>
</section>

{#if responseText}
  <section>
    <h2>Response</h2>
    <pre>{responseText}</pre>
  </section>
{/if}

<style>
  .assistant-form {
    max-width: none;
  }

  pre {
    margin: 0;
    padding: 12px;
    border-radius: 12px;
    border: 1px solid #f2ccb0;
    background: #fff;
    color: #2e1f16;
    white-space: pre-wrap;
    line-height: 1.55;
  }
</style>
