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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, init)
  if (!resp.ok) {
    const body = await resp.json().catch(() => null)
    throw new Error(body?.error ?? `Request failed (${resp.status})`)
  }
  return resp.json() as Promise<T>
}

export function fetchLatestJo(): Promise<LatestJo> {
  return request<LatestJo>('/jo/latest', { method: 'POST' })
}

export function fetchGlobalSummary(): Promise<{ summary: string }> {
  return request('/jo/latest/summary')
}

export function fetchThematicSummary(topic: string): Promise<{ summary: string }> {
  return request(`/jo/latest/summary?topic=${encodeURIComponent(topic)}`)
}
