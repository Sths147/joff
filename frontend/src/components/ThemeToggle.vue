<script setup lang="ts">
import { useTheme } from '../composables/useTheme'

const { theme, toggle } = useTheme()
</script>

<template>
  <button
    class="theme-toggle"
    type="button"
    :aria-label="theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'"
    :title="theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'"
    @click="toggle"
  >
    <svg
      v-if="theme === 'dark'"
      class="icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="1.75"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <circle cx="12" cy="12" r="4.5" />
      <path d="M12 2.5v2.5M12 19v2.5M4.6 4.6l1.8 1.8M17.6 17.6l1.8 1.8M2.5 12H5M19 12h2.5M4.6 19.4l1.8-1.8M17.6 6.4l1.8-1.8" />
    </svg>
    <svg
      v-else
      class="icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="1.75"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5Z" />
    </svg>
  </button>
</template>

<style scoped>
.theme-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.25rem;
  height: 2.25rem;
  padding: 0;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-surface);
  color: var(--color-text-soft);
  cursor: pointer;
  transition:
    color 0.15s ease,
    border-color 0.15s ease,
    background-color 0.15s ease;
}

.theme-toggle:hover {
  color: var(--color-text);
  border-color: var(--color-border-strong);
}

.theme-toggle:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}

.icon {
  width: 1.15rem;
  height: 1.15rem;
}
</style>
