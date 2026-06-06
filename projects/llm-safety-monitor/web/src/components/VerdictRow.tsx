import type { VerdictEntry } from '@/types'

const PAIR_LABEL: Record<number, { text: string; cls: string }> = {
  0: { text: 'Safe', cls: 'bg-green-100 text-green-800' },
  1: { text: 'Unsafe', cls: 'bg-red-100 text-red-800' },
}

const PROMPT_LABEL: Record<number, { text: string; cls: string }> = {
  0: { text: 'Benign', cls: 'bg-blue-100 text-blue-800' },
  1: { text: 'Adversarial', cls: 'bg-orange-100 text-orange-800' },
}

type Props = { verdicts: VerdictEntry[] }

export function VerdictRow({ verdicts }: Props) {
  const pair = verdicts.find((v) => v.model_name === 'pair_classifier')
  const prompt = verdicts.find((v) => v.model_name === 'prompt_detector')
  const taxonomy = verdicts.find((v) => v.model_name === 'taxonomy_classifier')

  return (
    <div className="flex gap-3 flex-wrap text-xs">
      <span className="font-medium text-gray-500">Pair:</span>
      {pair ? (
        <span className={`px-2 py-0.5 rounded-full font-medium ${PAIR_LABEL[pair.predicted_label]?.cls ?? 'bg-gray-100'}`}>
          {PAIR_LABEL[pair.predicted_label]?.text ?? pair.predicted_label}
        </span>
      ) : (
        <span className="text-gray-400">—</span>
      )}

      <span className="font-medium text-gray-500">Prompt:</span>
      {prompt ? (
        <span className={`px-2 py-0.5 rounded-full font-medium ${PROMPT_LABEL[prompt.predicted_label]?.cls ?? 'bg-gray-100'}`}>
          {PROMPT_LABEL[prompt.predicted_label]?.text ?? prompt.predicted_label}
        </span>
      ) : (
        <span className="text-gray-400">—</span>
      )}

      <span className="font-medium text-gray-500">Taxonomy:</span>
      {taxonomy ? (
        taxonomy.taxonomy_labels && taxonomy.taxonomy_labels.length > 0 ? (
          <span className="flex flex-wrap gap-1">
            {taxonomy.taxonomy_labels.map((label) => (
              <span key={label} className="px-2 py-0.5 rounded-full bg-purple-100 text-purple-800 font-medium">
                {label}
              </span>
            ))}
          </span>
        ) : (
          <span className="text-gray-400">none</span>
        )
      ) : (
        <span className="text-gray-400">—</span>
      )}
    </div>
  )
}
