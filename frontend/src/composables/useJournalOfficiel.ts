import { computed, ref } from 'vue'
import { marked } from 'marked'
import {
  fetchGlobalSummary,
  fetchLatestJoStatus,
  fetchPersonalizedSummary,
  fetchThematicSummary,
  startFetchLatestJo,
  type JoText,
} from '../api'

type Loading = 'fetch' | 'global' | 'thematic' | 'personalized' | null

const POLL_INTERVAL_MS = 2000

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export function useJournalOfficiel() {
  const loading = ref<Loading>(null)
  const error = ref<string | null>(null)

  const label = ref<string | null>(null)
  const texts = ref<JoText[]>([])

  const summaryHtml = ref<string | null>(null)

  const hasJo = computed(() => texts.value.length > 0)

  async function run<T>(kind: Exclude<Loading, null>, task: () => Promise<T>): Promise<T | null> {
    loading.value = kind
    error.value = null
    try {
      return await task()
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e)
      return null
    } finally {
      loading.value = null
    }
  }

  async function fetchLatest() {
    const result = await run('fetch', async () => {
      let status = await startFetchLatestJo()
      while (status.status === 'running') {
        await sleep(POLL_INTERVAL_MS)
        status = await fetchLatestJoStatus()
      }
      if (status.status === 'error') throw new Error(status.error ?? 'Fetch failed')
      return status
    })
    if (result?.status === 'done' && result.label && result.texts) {
      label.value = result.label
      texts.value = result.texts
      summaryHtml.value = null
    }
  }

  async function globalSummary() {
    const result = await run('global', fetchGlobalSummary)
    if (result) summaryHtml.value = await marked.parse(result.summary)
  }

  async function thematicSummary(topic: string) {
    if (!topic.trim()) return
    const result = await run('thematic', () => fetchThematicSummary(topic.trim()))
    if (result) summaryHtml.value = await marked.parse(result.summary)
  }

  async function personalizedSummary() {
    const result = await run('personalized', fetchPersonalizedSummary)
    if (result) summaryHtml.value = await marked.parse(result.summary)
  }

  return {
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
  }
}
