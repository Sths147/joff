const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:5001'

export interface JoText {
  id: string
  titre: string
  nature: string | null
}

export interface LatestJo {
  label: string
  texts: JoText[]
}

export interface FetchJobStatus {
  status: 'idle' | 'running' | 'done' | 'error'
  label: string | null
  texts: JoText[] | null
  error: string | null
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, init)
  if (!resp.ok) {
    const body = await resp.json().catch(() => null)
    throw new Error(body?.error ?? `Request failed (${resp.status})`)
  }
  return resp.json() as Promise<T>
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

export function fetchPersonalizedSummary(): Promise<{ summary: string }> {
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
