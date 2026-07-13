<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  loading: 'fetch' | 'global' | 'thematic' | 'personalized' | null
  summaryHtml: string | null
}>()
const emit = defineEmits<{ global: []; thematic: [topic: string]; personalized: [] }>()

const topic = ref('')

function onThematicSubmit() {
  if (!topic.value.trim()) return
  emit('thematic', topic.value)
}
</script>

<template>
  <section class="summary-actions">
    <button class="btn-outline" :disabled="props.loading !== null" @click="emit('global')">
      {{ props.loading === 'global' ? 'Summarizing…' : 'Global summary' }}
    </button>

    <form class="thematic-form" @submit.prevent="onThematicSubmit">
      <input v-model="topic" type="text" placeholder="Topic (e.g. health)" />
      <button class="btn-outline" :disabled="props.loading !== null || !topic.trim()" type="submit">
        {{ props.loading === 'thematic' ? 'Summarizing…' : 'Thematic summary' }}
      </button>
    </form>

    <button class="btn-outline" :disabled="props.loading !== null" @click="emit('personalized')">
      {{ props.loading === 'personalized' ? 'Summarizing…' : 'Personalized summary' }}
    </button>
  </section>

  <section v-if="summaryHtml" class="card summary-card">
    <header class="card-header">
      <h2>Summary</h2>
    </header>
    <div class="summary" v-html="summaryHtml"></div>
  </section>
</template>

<style scoped>
.summary-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.btn-outline {
  padding: 0.55rem 1.1rem;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text);
  font-weight: 500;
  cursor: pointer;
  transition:
    border-color 0.15s ease,
    color 0.15s ease,
    background-color 0.15s ease;
}

.btn-outline:hover:not(:disabled) {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.btn-outline:disabled {
  opacity: 0.55;
  cursor: default;
}

.btn-outline:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}

.thematic-form {
  display: flex;
  gap: 0.5rem;
}

.thematic-form input {
  padding: 0.55rem 0.85rem;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text);
  min-width: 12rem;
}

.thematic-form input:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 1px;
}

.thematic-form input::placeholder {
  color: var(--color-text-soft);
}

.card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
}

.card-header {
  padding: 1.1rem 1.35rem;
  border-bottom: 1px solid var(--color-border);
}

.card-header h2 {
  font-size: 1.15rem;
}

.summary {
  padding: 1.35rem;
  line-height: 1.7;
}

.summary :deep(h1),
.summary :deep(h2),
.summary :deep(h3) {
  margin: 1.25rem 0 0.5rem;
  font-size: 1.05rem;
}

.summary :deep(h1:first-child),
.summary :deep(h2:first-child),
.summary :deep(h3:first-child) {
  margin-top: 0;
}

.summary :deep(p) {
  margin: 0.65rem 0;
}

.summary :deep(ul),
.summary :deep(ol) {
  margin: 0.65rem 0;
  padding-left: 1.4rem;
}

.summary :deep(li) {
  margin: 0.3rem 0;
}

.summary :deep(strong) {
  color: var(--color-heading);
}
</style>
