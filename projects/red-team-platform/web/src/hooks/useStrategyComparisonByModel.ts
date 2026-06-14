import { useQueries } from '@tanstack/react-query'
import type { StrategyComparisonOut } from '@/types'

const API = import.meta.env['VITE_API_URL'] ?? 'http://localhost:8003'

export const MODEL_KEYS = ['gemma2:9b', 'qwen2.5:7b', 'llama3.1:8b'] as const
export type ModelKey = (typeof MODEL_KEYS)[number]

export const MODEL_COLOUR: Record<ModelKey, string> = {
  'gemma2:9b':    'danger',
  'qwen2.5:7b':  'warning',
  'llama3.1:8b': 'success',
}

export const MODEL_LABEL: Record<ModelKey, string> = {
  'gemma2:9b':    'Google gemma2:9b',
  'qwen2.5:7b':  'Alibaba qwen2.5:7b',
  'llama3.1:8b': 'Meta llama3.1:8b',
}

function fetchComparison(model: string): Promise<StrategyComparisonOut> {
  const url = `${API}/strategy-comparison?model_name=${encodeURIComponent(model)}`
  return fetch(url).then((r) => r.json())
}

export type ModelAsrMap = Record<string, Record<ModelKey, number | undefined>>

export function useStrategyComparisonByModel() {
  const results = useQueries({
    queries: MODEL_KEYS.map((model) => ({
      queryKey: ['strategyComparison', model],
      queryFn: () => fetchComparison(model),
      refetchInterval: 30_000,
    })),
  })

  const isLoading = results.some((r) => r.isLoading)
  const isError = results.some((r) => r.isError)

  // Build map: strategy → { 'gemma2:9b': asr, 'qwen2.5:7b': asr, 'llama3.1:8b': asr }
  const byStrategy: ModelAsrMap = {}
  results.forEach((r, i) => {
    const model = MODEL_KEYS[i]!
    for (const bar of r.data?.bars ?? []) {
      if (!byStrategy[bar.strategy]) byStrategy[bar.strategy] = {} as Record<ModelKey, number | undefined>
      byStrategy[bar.strategy]![model] = bar.asr
    }
  })

  return { byStrategy, isLoading, isError, results }
}
