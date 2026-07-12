<script setup lang="ts">
import type { JoText } from '../api'

defineProps<{ label: string | null; texts: JoText[] }>()
</script>

<template>
  <section>
    <h2>{{ label }} — {{ texts.length }} texts</h2>
    <ul class="texts">
      <li v-for="t in texts" :key="t.id">
        <span v-if="t.nature" class="nature">[{{ t.nature }}]</span> {{ t.titre }}
      </li>
    </ul>
  </section>
</template>

<style scoped>
.texts {
  padding-left: 1.25rem;
}

.nature {
  font-weight: 600;
  opacity: 0.7;
}
</style>
