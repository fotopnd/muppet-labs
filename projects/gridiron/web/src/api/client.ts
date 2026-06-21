export const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8006'

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init)
  if (!res.ok) throw res
  return res.json() as Promise<T>
}
