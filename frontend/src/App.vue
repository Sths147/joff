<script setup lang="ts">
import JoFetchPanel from './components/JoFetchPanel.vue'
import JoTextList from './components/JoTextList.vue'
import SummaryPanel from './components/SummaryPanel.vue'
import ThemeToggle from './components/ThemeToggle.vue'
import { useJournalOfficiel } from './composables/useJournalOfficiel'

const { loading, error, label, texts, summaryHtml, hasJo, fetchLatest, globalSummary, thematicSummary } =
  useJournalOfficiel()
</script>

<template>
  <header class="masthead">
    <div class="masthead-row">
      <p class="eyebrow">République Française · Digest</p>
      <ThemeToggle />
    </div>
    <h1>Journal Officiel</h1>
  </header>

  <main>
    <JoFetchPanel
      :fetching="loading === 'fetch'"
      :disabled="loading !== null"
      @fetch="fetchLatest"
    />

    <p v-if="error" class="error">{{ error }}</p>

    <template v-if="hasJo">
      <JoTextList :label="label" :texts="texts" />
      <SummaryPanel
        :loading="loading"
        :summary-html="summaryHtml"
        @global="globalSummary"
        @thematic="thematicSummary"
      />
    </template>
  </main>
</template>

<style scoped>
.masthead {
  padding: 2.5rem 0 1.5rem;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: 2rem;
}

.masthead-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.eyebrow {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-soft);
}

.masthead h1 {
  font-size: 2.25rem;
  letter-spacing: -0.01em;
}

main {
  display: flex;
  flex-direction: column;
  gap: 1.75rem;
}

.error {
  padding: 0.75rem 1rem;
  border: 1px solid color-mix(in srgb, var(--color-danger) 35%, transparent);
  border-radius: var(--radius-md);
  background: color-mix(in srgb, var(--color-danger) 10%, transparent);
  color: var(--color-danger);
  font-size: 0.9rem;
}
</style>
