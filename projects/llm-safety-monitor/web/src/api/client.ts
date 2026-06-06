const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8002'

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
  }
}

export async function apiFetch<T>(path: string): Promise<T> {
  const resp = await fetch(`${BASE_URL}${path}`)
  if (!resp.ok) {
    throw new ApiError(resp.status, `API error ${resp.status}: ${path}`)
  }
  return resp.json() as Promise<T>
}
