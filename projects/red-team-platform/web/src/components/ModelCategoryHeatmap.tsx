import { useModelCategoryHeatmap } from '@/hooks/useModelCategoryHeatmap'
import { abbrevName, labelName } from '@/lib/categoryLabels'

const MODEL_SHORT: Record<string, string> = {
  'gemma2:9b':    'gemma2',
  'qwen2.5:7b':  'qwen2.5',
  'llama3.1:8b': 'llama3.1',
}

const MODEL_HEADER_CLS: Record<string, string> = {
  'gemma2:9b':    'text-blue-700',
  'qwen2.5:7b':  'text-orange-700',
  'llama3.1:8b': 'text-violet-700',
}

function asrBg(asr: number): string {
  if (asr >= 0.5) return 'bg-red-100 text-red-800'
  if (asr >= 0.3) return 'bg-orange-50 text-orange-800'
  if (asr >= 0.1) return 'bg-amber-50 text-amber-800'
  return 'bg-green-50 text-green-800'
}

export function ModelCategoryHeatmap() {
  const { data, isLoading, isError } = useModelCategoryHeatmap()

  if (isLoading) return <p className="text-text-secondary text-sm">Loading…</p>
  if (isError) return <p className="text-danger text-sm">Error loading heatmap.</p>
  if (!data?.cells.length) return <p className="text-text-muted text-sm">No data yet.</p>

  // Build lookup: model → category → asr
  const lookup: Record<string, Record<string, number>> = {}
  for (const cell of data.cells) {
    if (!lookup[cell.model_name]) lookup[cell.model_name] = {}
    lookup[cell.model_name]![cell.harm_category] = cell.asr
  }

  const models = data.models
  const categories = [...data.categories].sort()

  // Find which column has highest ASR per row for highlighting
  const rowMax = (cat: string) =>
    Math.max(...models.map((m) => lookup[m]?.[cat] ?? 0))

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr className="bg-surface-muted">
            <th className="text-left px-3 py-2 font-medium text-text-secondary border-b border-border w-44">
              Harm Category
            </th>
            {models.map((m) => (
              <th key={m} className={`px-3 py-2 font-medium border-b border-border text-center w-24 ${MODEL_HEADER_CLS[m] ?? 'text-text-secondary'}`}>
                {MODEL_SHORT[m] ?? m}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {categories.map((cat) => {
            const max = rowMax(cat)
            return (
              <tr key={cat} className="border-b border-border hover:bg-surface-muted/50">
                <td className="px-3 py-1.5 text-text-secondary" title={labelName(cat)}>
                  {abbrevName(cat)}
                </td>
                {models.map((m) => {
                  const asr = lookup[m]?.[cat]
                  if (asr === undefined) {
                    return <td key={m} className="px-3 py-1.5 text-center text-text-muted">—</td>
                  }
                  const isMax = asr === max && max > 0
                  return (
                    <td key={m} className="px-3 py-1.5 text-center">
                      <span className={`inline-block px-1.5 py-0.5 rounded font-mono font-semibold ${asrBg(asr)} ${isMax ? 'ring-1 ring-red-400' : ''}`}>
                        {(asr * 100).toFixed(0)}%
                      </span>
                    </td>
                  )
                })}
              </tr>
            )
          })}
        </tbody>
      </table>
      <p className="text-xs text-text-muted mt-2">
        Ring indicates highest ASR per category row. Green &lt;10%, amber 10–30%, orange 30–50%, red ≥50%.
      </p>
    </div>
  )
}
