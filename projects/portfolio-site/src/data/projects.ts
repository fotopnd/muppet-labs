export type MetricRow = {
  label: string
  value: string
}

export type Project = {
  id: string
  name: string
  tagline: string
  description: string
  metrics: MetricRow[]
  demoUrl: string | null
}

export const PROJECTS: Project[] = [
  {
    id: 'llm-safety-monitor',
    name: 'LLM Safety Monitor',
    tagline:
      'Fine-tuned classifiers that score production traffic for harmfulness, prompt injection, and taxonomy category in real time.',
    description:
      'Three RoBERTa-base classifiers trained on HH-RLHF and WildGuard data — one for pair-level harmfulness, one for prompt injection, one for 13-category harm taxonomy. The monitor streams live events through a Kafka pipeline and exposes a FastAPI metrics endpoint consumed by the moderation dashboard.',
    metrics: [
      { label: 'Prompt classifier F1', value: '0.818' },
      { label: 'Taxonomy macro-F1', value: '0.787' },
      { label: 'Pair classifier F1', value: '0.549' },
      { label: 'Training set', value: '50k pairs (HH-RLHF)' },
    ],
    demoUrl: 'http://localhost:5176',
  },
  {
    id: 'red-team-platform',
    name: 'Red-Team Platform',
    tagline:
      'Corpus-driven jailbreak campaigns with classifier scoring, semantic clustering, and live safety monitor integration.',
    description:
      'Runs structured attack campaigns against an Ollama-compatible model, scores every response with the shared safety classifier, clusters successful attacks by mechanism, and publishes all 1,797 events to the live monitor via Kafka outbox. A React dashboard surfaces attack-success-rate splits by strategy, semantic cluster breakdowns, and regression tracking across runs.',
    metrics: [
      { label: 'Attacks (Phase 1)', value: '1,797' },
      { label: 'Strategies tested', value: '6' },
      { label: 'Top ASR (few_shot_json)', value: '100%' },
      { label: 'Fully-resisted strategies', value: '3 of 6' },
    ],
    demoUrl: 'http://localhost:5173',
  },
  {
    id: 'error-hide-seek',
    name: 'Error Hide and Seek',
    tagline:
      'A randomised controlled trial measuring whether AI hints improve human detection of planted errors in academic abstracts.',
    description:
      'Two experiments across 100 papers and 67 human review sessions compared unaided detection against human+agent detection. Overall TPR uplift was −0.01 (null result). Category-level decomposition found +0.33 uplift for inverted-conclusion errors — the one category where Claude can reason without ground-truth access — and zero or negative uplift for domain-dependent categories.',
    metrics: [
      { label: 'Human+Agent TPR', value: '0.29' },
      { label: 'Unaided TPR', value: '0.30' },
      { label: 'Overall uplift', value: '−0.01' },
      { label: 'Inverted-conclusion uplift', value: '+0.33' },
    ],
    demoUrl: 'http://localhost:5174',
  },
]
