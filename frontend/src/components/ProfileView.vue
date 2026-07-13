<script setup lang="ts">
import { onMounted } from 'vue'
import { useProfile } from '../composables/useProfile'

const { bio, loading, saving, error, saved, load, save } = useProfile()

onMounted(load)
</script>

<template>
  <section class="card profile-card">
    <header class="card-header">
      <h2>Profile</h2>
      <p class="hint">
        Describe yourself here — the "Personalized summary" button on the digest will tailor
        the JO summary to it.
      </p>
    </header>

    <div class="card-body">
      <textarea
        v-model="bio"
        :disabled="loading || saving"
        rows="8"
        placeholder="e.g. I'm a startup founder in Lyon interested in tax law, labor regulations, and digital economy policy."
      />

      <div class="actions">
        <button class="btn-primary" :disabled="loading || saving" @click="save">
          {{ saving ? 'Saving…' : 'Save' }}
        </button>
        <span v-if="saved" class="saved">Saved</span>
      </div>

      <p v-if="error" class="error">{{ error }}</p>
    </div>
  </section>
</template>

<style scoped>
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

.hint {
  margin-top: 0.4rem;
  color: var(--color-text-soft);
  font-size: 0.9rem;
}

.card-body {
  padding: 1.35rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

textarea {
  width: 100%;
  padding: 0.75rem 0.9rem;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text);
  font-family: inherit;
  font-size: 0.95rem;
  line-height: 1.6;
  resize: vertical;
}

textarea:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 1px;
}

textarea::placeholder {
  color: var(--color-text-soft);
}

textarea:disabled {
  opacity: 0.6;
}

.actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
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

.saved {
  color: var(--color-text-soft);
  font-size: 0.9rem;
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
