<script lang="ts">
  import { onMount } from 'svelte';

  const guideSections = ['featured-guides', 'brew-calibration', 'lab-scenarios', 'faq'] as const;
  let currentGuideSection = 'featured-guides';

  onMount(() => {
    const syncSectionFromHash = () => {
      const hash = window.location.hash.replace('#', '');
      currentGuideSection = hash || 'featured-guides';
    };

    syncSectionFromHash();
    window.addEventListener('hashchange', syncSectionFromHash);

    const sectionElements = guideSections
      .map((id) => document.getElementById(id))
      .filter((element): element is HTMLElement => element !== null);

    const pickNearestSection = () => {
      if (window.location.hash) {
        return;
      }

      const viewportHeight = window.innerHeight;
      let activeId = sectionElements[0]?.id || 'featured-guides';
      let bestVisiblePixels = -1;

      for (const element of sectionElements) {
        const rect = element.getBoundingClientRect();
        const visiblePixels = Math.max(0, Math.min(rect.bottom, viewportHeight) - Math.max(rect.top, 0));
        if (visiblePixels > bestVisiblePixels) {
          bestVisiblePixels = visiblePixels;
          activeId = element.id;
        }
      }

      currentGuideSection = activeId;
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
  <h1>Brew Guides</h1>
  <nav class="section-nav" aria-label="Learning sections">
    <a href="#featured-guides" class:active-tab={currentGuideSection === 'featured-guides'} aria-current={currentGuideSection === 'featured-guides' ? 'page' : undefined}>Featured</a>
    <a href="#brew-calibration" class:active-tab={currentGuideSection === 'brew-calibration'} aria-current={currentGuideSection === 'brew-calibration' ? 'page' : undefined}>Calibration</a>
    <a href="#lab-scenarios" class:active-tab={currentGuideSection === 'lab-scenarios'} aria-current={currentGuideSection === 'lab-scenarios' ? 'page' : undefined}>Lab scenarios</a>
    <a href="#faq" class:active-tab={currentGuideSection === 'faq'} aria-current={currentGuideSection === 'faq' ? 'page' : undefined}>FAQ</a>
    <a href="/assistant">Assistant</a>
    <a href="/shop">Shop coffees</a>
  </nav>
  <p>Hands-on brewing playbooks for learners testing user journeys and content flows.</p>
</section>

<section id="featured-guides">
  <h2>Featured Guides</h2>
  <ul class="guide-grid">
    <li>
      <a href="/guides/pour-over-basics">Pour-over basics</a>
      <p>Dial in grind size, bloom timing, and pour cadence for clean cups.</p>
    </li>
    <li>
      <a href="/guides/espresso-foundations">Espresso foundations</a>
      <p>Learn dose, yield, and extraction adjustments for balanced shots.</p>
    </li>
    <li>
      <a href="/guides/cold-brew-lab">Cold brew lab</a>
      <p>Build concentrate recipes and dilution plans for batch service.</p>
    </li>
  </ul>
</section>

<section id="brew-calibration">
  <h2>Brew Calibration Basics</h2>
  <p>Use this quick matrix to adjust flavor outcomes. Change one variable at a time and keep notes per roast.</p>
  <ul class="notes-list">
    <li><strong>Too sour:</strong> grind finer, increase water temperature, or extend brew time.</li>
    <li><strong>Too bitter:</strong> grind coarser, reduce brew time, or lower water temperature.</li>
    <li><strong>Flat cup:</strong> increase dose slightly and reduce bypass water.</li>
  </ul>
</section>

<section id="lab-scenarios">
  <h2>Lab Scenarios</h2>
  <ul class="scenario-grid">
    <li>
      <p class="scenario-title">Morning Rush Espresso</p>
      <p>Simulate a high-volume queue and test shot consistency while adjusting grinder settings every 20 pulls.</p>
    </li>
    <li>
      <p class="scenario-title">Cold Brew Batch Day</p>
      <p>Compare 12-hour vs 16-hour steep times and map flavor + dilution ratios for menu-ready service.</p>
    </li>
    <li>
      <p class="scenario-title">Origin Showcase Flight</p>
      <p>Cup 3 single origins blind and score sweetness, acidity, and body to inform featured coffee rotation.</p>
    </li>
  </ul>
</section>

<section id="faq">
  <h2>FAQ</h2>
  <ul class="notes-list">
    <li><strong>How often should I recalibrate?</strong> At least once per roast or whenever humidity shifts noticeably.</li>
    <li><strong>Best water temperature range?</strong> 92C-96C works for most specialty coffee workflows.</li>
    <li><strong>How long should bloom last?</strong> Start with 30-45 seconds and adjust based on roast freshness.</li>
  </ul>
</section>

<style>
  .guide-grid {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 10px;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  }

  .guide-grid li {
    border: 1px solid #f2ccb0;
    border-radius: 12px;
    background: #fff;
    padding: 12px;
  }

  .guide-grid li p {
    margin-top: 8px;
    margin-bottom: 0;
    color: #5a4a40;
  }

  .notes-list {
    margin: 0;
    padding-left: 18px;
    display: grid;
    gap: 8px;
  }

  .scenario-grid {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 10px;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  }

  .scenario-grid li {
    border: 1px solid #f2ccb0;
    border-radius: 12px;
    background: #fff;
    padding: 12px;
  }

  .scenario-title {
    margin: 0 0 6px;
    font-weight: 700;
    color: #2e1f16;
  }
</style>
