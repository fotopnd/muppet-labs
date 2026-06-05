const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8002'

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export async function apiFetch<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`)
  if (!response.ok) {
    throw new ApiError(response.status, `API error ${response.status}: ${path}`)
  }
  return response.json() as Promise<T>
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    headers: body !== undefined ? { 'Content-Type': 'application/json' } : {},
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  if (!response.ok) {
    throw new ApiError(response.status, `API error ${response.status}: ${path}`)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export async function externalFetch<T>(url: string): Promise<T> {
  const response = await fetch(url)
  if (!response.ok) {
    throw new ApiError(response.status, `External API error ${response.status}: ${url}`)
  }
  return response.json() as Promise<T>
}
