import { ref } from 'vue'
import {
  SESSION_EXPIRED_EVENT,
  currentUser,
  login as apiLogin,
  logout as apiLogout,
  register as apiRegister,
} from '../api'

// Session lives in an httpOnly cookie the browser manages — this ref just
// mirrors "are we logged in" for the UI. It can't be read from the cookie
// directly, hence checkSession() asking the backend via GET /auth/me.
const email = ref<string | null>(null)
const checked = ref(false)

window.addEventListener(SESSION_EXPIRED_EVENT, () => {
  email.value = null
})

export function useAuth() {
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function checkSession() {
    try {
      const user = await currentUser()
      email.value = user.email
    } catch {
      email.value = null
    } finally {
      checked.value = true
    }
  }

  async function login(emailInput: string, password: string) {
    loading.value = true
    error.value = null
    try {
      const user = await apiLogin(emailInput, password)
      email.value = user.email
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  async function register(emailInput: string, password: string) {
    loading.value = true
    error.value = null
    try {
      const user = await apiRegister(emailInput, password)
      email.value = user.email
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    await apiLogout().catch(() => undefined)
    email.value = null
  }

  return { email, checked, loading, error, checkSession, login, register, logout }
}
