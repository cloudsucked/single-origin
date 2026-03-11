<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';

  const guideDetailSections = ['quick-checklist', 'brew-targets', 'troubleshooting'] as const;
  let currentGuideDetailSection = 'quick-checklist';

  $: slug = $page.params.slug ?? '';
  $: title = slug
    .split('-')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');

  onMount(() => {
    const syncSectionFromHash = () => {
      const hash = window.location.hash.replace('#', '');
      currentGuideDetailSection = hash || 'quick-checklist';
    };

    syncSectionFromHash();
    window.addEventListener('hashchange', syncSectionFromHash);

    const sectionElements = guideDetailSections
      .map((id) => document.getElementById(id))
      .filter((element): element is HTMLElement => element !== null);

    const pickNearestSection = () => {
      if (window.location.hash) {
        return;
      }

      const viewportHeight = window.innerHeight;
      let activeId = sectionElements[0]?.id || 'quick-checklist';
      let bestVisiblePixels = -1;

      for (const element of sectionElements) {
        const rect = element.getBoundingClientRect();
        const visiblePixels = Math.max(0, Math.min(rect.bottom, viewportHeight) - Math.max(rect.top, 0));
        if (visiblePixels > bestVisiblePixels) {
          bestVisiblePixels = visiblePixels;
          activeId = element.id;
        }
      }

      currentGuideDetailSection = activeId;
    };

    const observer = new IntersectionObserver(pickNearestSection, {
      rootMargin: '-120px 0px -60% 0px',
      threshold: [0, 0.2, 0.5, 0.8]
    });

    const handleScroll = () => {
      window.requestAnimationFrame(pickNearestSection);
    };

    sectionElements.forEach((element) => observer.observe(element));
    window.addEventListener('scroll', handleScroll, { passive: true });
    document.addEventListener('scroll', handleScroll, { passive: true });
    pickNearestSection();

    return () => {
      window.removeEventListener('hashchange', syncSectionFromHash);
      window.removeEventListener('scroll', handleScroll);
      document.removeEventListener('scroll', handleScroll);
      observer.disconnect();
    };
  });
</script>

<section>
  <nav class="breadcrumb" aria-label="Breadcrumb">
    <a href="/">Home</a>
    <span class="sep">/</span>
    <a href="/guides">Guides</a>
    <span class="sep">/</span>
    <span aria-current="page">{title}</span>
  </nav>
  <h1>{title}</h1>
  <nav class="section-nav" aria-label="Guide navigation">
    <a href="#quick-checklist" class:active-tab={currentGuideDetailSection === 'quick-checklist'} aria-current={currentGuideDetailSection === 'quick-checklist' ? 'page' : undefined}>Checklist</a>
    <a href="#brew-targets" class:active-tab={currentGuideDetailSection === 'brew-targets'} aria-current={currentGuideDetailSection === 'brew-targets' ? 'page' : undefined}>Targets</a>
    <a href="#troubleshooting" class:active-tab={currentGuideDetailSection === 'troubleshooting'} aria-current={currentGuideDetailSection === 'troubleshooting' ? 'page' : undefined}>Troubleshooting</a>
    <a href="/guides">All guides</a>
    <a href="/assistant">Assistant</a>
    <a href="/shop">Shop coffees</a>
  </nav>
  <p>Step-by-step guide detail route used for SSR and navigation lab coverage.</p>
</section>

<section id="quick-checklist">
  <h2>Quick Checklist</h2>
  <ul class="checklist">
    <li>Prep your station, filter, and measured dose.</li>
    <li>Capture brew time, temperature, and tasting notes.</li>
    <li>Adjust one variable at a time and compare outcomes.</li>
  </ul>
  <p class="route-id">Route slug: <code>{slug}</code></p>
</section>

<section id="brew-targets">
  <h2>Brew Targets</h2>
  <ul class="checklist">
    <li><strong>Pour-over:</strong> 1:16 ratio, 92C-96C water, 2:45-3:30 total time.</li>
    <li><strong>Espresso:</strong> 1:2 ratio, 25-32 seconds, stable puck prep routine.</li>
    <li><strong>Cold brew:</strong> 1:8 concentrate, 12-16 hour steep, filtered twice.</li>
  </ul>
</section>

<section id="troubleshooting">
  <h2>Troubleshooting</h2>
  <ul class="checklist">
    <li><strong>Channeling:</strong> improve distribution and tamp consistency.</li>
    <li><strong>Weak body:</strong> increase dose or reduce brew water.</li>
    <li><strong>Over-extraction:</strong> coarsen grind and reduce contact time.</li>
  </ul>
</section>

<style>
  .checklist {
    margin: 0;
    padding-left: 18px;
    display: grid;
    gap: 8px;
  }

  .route-id {
    margin-top: 12px;
    font-size: 0.92rem;
  }
</style>
