import { ref } from 'vue'
import { fetchProfile, saveProfile } from '../api'

export function useProfile() {
  const bio = ref('')
  const loading = ref(false)
  const saving = ref(false)
  const error = ref<string | null>(null)
  const saved = ref(false)

  async function load() {
    loading.value = true
    error.value = null
    try {
      const profile = await fetchProfile()
      bio.value = profile.bio
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  async function save() {
    saving.value = true
    error.value = null
    saved.value = false
    try {
      const profile = await saveProfile(bio.value)
      bio.value = profile.bio
      saved.value = true
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      saving.value = false
    }
  }

  return { bio, loading, saving, error, saved, load, save }
}
