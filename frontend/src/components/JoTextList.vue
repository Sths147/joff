<script setup lang="ts">
import type { JoText } from '../api'

defineProps<{ label: string | null; texts: JoText[] }>()
</script>

<template>
  <section class="card">
    <header class="card-header">
      <h2>{{ label }}</h2>
      <span class="count">{{ texts.length }} texts</span>
    </header>
    <ul class="texts">
      <li v-for="t in texts" :key="t.id">
        <span v-if="t.nature" class="nature">{{ t.nature }}</span>
        <span class="title">{{ t.titre }}</span>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.1rem 1.35rem;
  border-bottom: 1px solid var(--color-border);
}

.card-header h2 {
  font-size: 1.15rem;
}

.count {
  flex-shrink: 0;
  font-size: 0.8rem;
  color: var(--color-text-soft);
}

.texts {
  list-style: none;
  max-height: 22rem;
  overflow-y: auto;
}

.texts li {
  display: flex;
  align-items: baseline;
  gap: 0.65rem;
  padding: 0.7rem 1.35rem;
  border-bottom: 1px solid var(--color-border);
  font-size: 0.92rem;
}

.texts li:last-child {
  border-bottom: none;
}

.texts li:hover {
  background: var(--color-bg);
}

.nature {
  flex-shrink: 0;
  padding: 0.1rem 0.5rem;
  border-radius: 999px;
  background: var(--color-accent-tint);
  color: var(--color-accent);
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}

.title {
  color: var(--color-text);
}
</style>
