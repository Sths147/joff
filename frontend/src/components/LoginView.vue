<script setup lang="ts">
import { ref } from 'vue'
import { useAuth } from '../composables/useAuth'

const { loading, error, login, register } = useAuth()

const mode = ref<'login' | 'register'>('login')
const email = ref('')
const password = ref('')

function submit() {
  if (!email.value || !password.value) return
  if (mode.value === 'login') login(email.value, password.value)
  else register(email.value, password.value)
}

function toggleMode() {
  mode.value = mode.value === 'login' ? 'register' : 'login'
}
</script>

<template>
  <section class="card login-card">
    <header class="card-header">
      <h2>{{ mode === 'login' ? 'Log in' : 'Create an account' }}</h2>
      <p class="hint">
        {{
          mode === 'login'
            ? 'Log in to see your digest and personalized summaries.'
            : 'Register to get your own profile and personalized summaries.'
        }}
      </p>
    </header>

    <form class="card-body" @submit.prevent="submit">
      <label class="field">
        <span>Email</span>
        <input v-model="email" type="email" autocomplete="email" required :disabled="loading" />
      </label>

      <label class="field">
        <span>Password</span>
        <input
          v-model="password"
          type="password"
          :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
          minlength="8"
          required
          :disabled="loading"
        />
      </label>

      <div class="actions">
        <button class="btn-primary" type="submit" :disabled="loading">
          {{ loading ? 'Please wait…' : mode === 'login' ? 'Log in' : 'Register' }}
        </button>
        <button class="btn-link" type="button" :disabled="loading" @click="toggleMode">
          {{ mode === 'login' ? "Don't have an account? Register" : 'Already have an account? Log in' }}
        </button>
      </div>

      <p v-if="error" class="error">{{ error }}</p>
    </form>
  </section>
</template>

<style scoped>
.login-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
  max-width: 26rem;
  margin: 3rem auto;
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

.field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  font-size: 0.9rem;
  color: var(--color-text-soft);
}

.field input {
  padding: 0.65rem 0.85rem;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text);
  font-family: inherit;
  font-size: 0.95rem;
}

.field input:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 1px;
}

.field input:disabled {
  opacity: 0.6;
}

.actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
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

.btn-link {
  border: none;
  background: none;
  color: var(--color-text-soft);
  font-size: 0.85rem;
  text-decoration: underline;
  cursor: pointer;
}

.btn-link:disabled {
  opacity: 0.6;
  cursor: default;
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
