<script setup lang="ts">
import { onMounted, ref } from 'vue'
import JoFetchPanel from './components/JoFetchPanel.vue'
import JoTextList from './components/JoTextList.vue'
import LoginView from './components/LoginView.vue'
import ProfileView from './components/ProfileView.vue'
import SummaryPanel from './components/SummaryPanel.vue'
import ThemeToggle from './components/ThemeToggle.vue'
import { useAuth } from './composables/useAuth'
import { useJournalOfficiel } from './composables/useJournalOfficiel'

type View = 'digest' | 'profile'
const view = ref<View>('digest')

const { email, checked, checkSession, logout } = useAuth()
onMounted(checkSession)

const {
  loading,
  error,
  label,
  texts,
  summaryHtml,
  hasJo,
  fetchLatest,
  globalSummary,
  thematicSummary,
  personalizedSummary,
} = useJournalOfficiel()
</script>

<template>
  <template v-if="!checked" />

  <LoginView v-else-if="!email" />

  <template v-else>
    <header class="masthead">
      <div class="masthead-row">
        <p class="eyebrow">République Française · Digest</p>
        <div class="masthead-actions">
          <span class="user-email">{{ email }}</span>
          <button class="btn-link" @click="logout">Log out</button>
          <ThemeToggle />
        </div>
      </div>
      <h1>Journal Officiel</h1>
      <nav class="tabs">
        <button class="tab" :class="{ active: view === 'digest' }" @click="view = 'digest'">
          Digest
        </button>
        <button class="tab" :class="{ active: view === 'profile' }" @click="view = 'profile'">
          Profile
        </button>
      </nav>
    </header>

    <main v-if="view === 'digest'">
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
          @personalized="personalizedSummary"
        />
      </template>
    </main>

    <main v-else>
      <ProfileView />
    </main>
  </template>
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

.masthead-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.user-email {
  font-size: 0.85rem;
  color: var(--color-text-soft);
}

.btn-link {
  border: none;
  background: none;
  color: var(--color-text-soft);
  font-size: 0.85rem;
  text-decoration: underline;
  cursor: pointer;
  padding: 0;
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

.tabs {
  display: flex;
  gap: 1.5rem;
  margin-top: 1.25rem;
}

.tab {
  padding: 0.25rem 0;
  border: none;
  border-bottom: 2px solid transparent;
  background: none;
  color: var(--color-text-soft);
  font-weight: 500;
  cursor: pointer;
  transition:
    color 0.15s ease,
    border-color 0.15s ease;
}

.tab:hover {
  color: var(--color-text);
}

.tab.active {
  color: var(--color-accent);
  border-bottom-color: var(--color-accent);
}

.tab:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
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
