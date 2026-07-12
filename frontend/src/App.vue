<script setup lang="ts">
import JoFetchPanel from './components/JoFetchPanel.vue'
import JoTextList from './components/JoTextList.vue'
import SummaryPanel from './components/SummaryPanel.vue'
import { useJournalOfficiel } from './composables/useJournalOfficiel'

const { loading, error, label, texts, summaryHtml, hasJo, fetchLatest, globalSummary, thematicSummary } =
  useJournalOfficiel()
</script>

<template>
  <main>
    <h1>Journal Officiel</h1>

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
main {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.error {
  color: #c0392b;
}
</style>
