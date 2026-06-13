import { useQuery } from '@tanstack/react-query'
import type { BackTranslateOut } from '@/types'

const API = import.meta.env['VITE_API_URL'] ?? 'http://localhost:8003'

export function useBackTranslation(
  text: string | null | undefined,
  sourceLang: 'zh' | 'ru' | 'ar',
) {
  return useQuery<BackTranslateOut>({
    queryKey: ['back-translate', sourceLang, text],
    queryFn: () =>
      fetch(`${API}/bias/back-translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, source_lang: sourceLang }),
      }).then((r) => r.json()),
    enabled: !!text,
    staleTime: Infinity,
  })
}
