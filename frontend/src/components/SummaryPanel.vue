<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  loading: 'fetch' | 'global' | 'thematic' | null
  summaryHtml: string | null
}>()
const emit = defineEmits<{ global: []; thematic: [topic: string] }>()

const topic = ref('')

function onThematicSubmit() {
  if (!topic.value.trim()) return
  emit('thematic', topic.value)
}
</script>

<template>
  <section class="summary-actions">
    <button :disabled="props.loading !== null" @click="emit('global')">
      {{ props.loading === 'global' ? 'Summarizing…' : 'Global summary' }}
    </button>

    <form class="thematic-form" @submit.prevent="onThematicSubmit">
      <input v-model="topic" type="text" placeholder="Topic (e.g. health)" />
      <button :disabled="props.loading !== null || !topic.trim()" type="submit">
        {{ props.loading === 'thematic' ? 'Summarizing…' : 'Thematic summary' }}
      </button>
    </form>
  </section>

  <section v-if="summaryHtml">
    <h2>Summary</h2>
    <div class="summary" v-html="summaryHtml"></div>
  </section>
</template>

<style scoped>
.summary-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.thematic-form {
  display: flex;
  gap: 0.5rem;
}

.summary {
  line-height: 1.6;
}
</style>
