<script setup lang="ts">
defineProps<{ fetching: boolean; disabled: boolean }>()
const emit = defineEmits<{ fetch: [] }>()
</script>

<template>
  <section class="fetch-panel">
    <button class="btn-primary" :disabled="disabled" @click="emit('fetch')">
      <span v-if="fetching" class="spinner" aria-hidden="true" />
      {{ fetching ? 'Fetching…' : 'Get latest JO' }}
    </button>
  </section>
</template>

<style scoped>
.fetch-panel {
  display: flex;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.65rem 1.25rem;
  border: 1px solid var(--color-accent);
  border-radius: var(--radius-md);
  background: var(--color-accent);
  color: var(--color-accent-contrast);
  font-weight: 500;
  cursor: pointer;
  transition:
    background-color 0.15s ease,
    transform 0.1s ease;
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-accent-strong);
  border-color: var(--color-accent-strong);
}

.btn-primary:active:not(:disabled) {
  transform: translateY(1px);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: default;
}

.btn-primary:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}

.spinner {
  width: 0.9rem;
  height: 0.9rem;
  border: 2px solid color-mix(in srgb, var(--color-accent-contrast) 40%, transparent);
  border-top-color: var(--color-accent-contrast);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
