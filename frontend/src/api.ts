export interface JoText {
  id: string
  titre: string
  nature: string | null
}

export interface FetchJobStatus {
  status: 'idle' | 'running' | 'done' | 'error'
  label: string | null
  texts: JoText[] | null
  error: string | null
}

export interface SessionUser {
  email: string
}

export interface PersonalizedTopic {
  title: string
  facts: string
  details: string
}

// Dispatched whenever a request comes back 401, so auth state elsewhere (see
// useAuth.ts) can reset without a hard reload.
export const SESSION_EXPIRED_EVENT = 'joff-session-expired'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(path, init)
  if (!resp.ok) {
    if (resp.status === 401) window.dispatchEvent(new CustomEvent(SESSION_EXPIRED_EVENT))
    const body = await resp.json().catch(() => null)
    throw new Error(body?.error ?? `Request failed (${resp.status})`)
  }
  return resp.json() as Promise<T>
}

function postJson<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export function register(email: string, password: string): Promise<SessionUser> {
  return postJson('/auth/register', { email, password })
}

export function login(email: string, password: string): Promise<SessionUser> {
  return postJson('/auth/login', { email, password })
}

export function logout(): Promise<{ ok: boolean }> {
  return request('/auth/logout', { method: 'POST' })
}

export function currentUser(): Promise<SessionUser> {
  return request('/auth/me')
}

// The fetch runs in the background on the server (see ADR 0006); this starts
// or observes it, and fetchLatestJoStatus() below is polled for the result.
export function startFetchLatestJo(): Promise<FetchJobStatus> {
  return request<FetchJobStatus>('/jo/latest', { method: 'POST' })
}

export function fetchLatestJoStatus(): Promise<FetchJobStatus> {
  return request<FetchJobStatus>('/jo/latest/status')
}

export function fetchGlobalSummary(): Promise<{ summary: string }> {
  return request('/jo/latest/summary')
}

export function fetchThematicSummary(topic: string): Promise<{ summary: string }> {
  return request(`/jo/latest/summary?topic=${encodeURIComponent(topic)}`)
}

export function fetchPersonalizedSummary(): Promise<{ topics: PersonalizedTopic[] }> {
  return request('/jo/latest/summary?personalized=1')
}

export function fetchProfile(): Promise<{ bio: string }> {
  return request('/profile')
}

export function saveProfile(bio: string): Promise<{ bio: string }> {
  return request('/profile', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ bio }),
  })
}
