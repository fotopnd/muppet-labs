const BASE_URL = import.meta.env['VITE_API_URL'] ?? 'http://localhost:8000'

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-Actor-Id': import.meta.env['VITE_ACTOR_ID'] ?? 'dev-user',
      'X-Actor-Role': import.meta.env['VITE_ACTOR_ROLE'] ?? 'reviewer',
      ...options.headers,
    },
  })

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }))
    throw new ApiError(response.status, (body as { detail: string }).detail)
  }

  return response.json() as Promise<T>
}
