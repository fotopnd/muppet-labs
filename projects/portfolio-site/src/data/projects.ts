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
    id: 'red-team-platform',
    name: 'Red-Team Platform',
    tagline:
      'Corpus-driven jailbreak campaigns with classifier scoring, semantic clustering, and live safety monitor integration.',
    description:
      'Runs structured attack campaigns against an Ollama-compatible model, scores every response with the shared safety classifier, clusters successful attacks by mechanism, and publishes all events to the live monitor via Kafka outbox. A React dashboard surfaces attack-success-rate splits by strategy, semantic cluster breakdowns, and regression tracking across runs.',
    metrics: [
      { label: 'Attack runs logged', value: '11,688' },
      { label: 'Strategies tested', value: '13' },
      { label: 'Models evaluated', value: '3 open-weight' },
      { label: 'Top ASR (few_shot_json)', value: '100%' },
    ],
    demoUrl: 'https://red-team.fotopnd.dev',
  },
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
    demoUrl: 'https://llm-safety.fotopnd.dev',
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
    demoUrl: 'https://error-seek.fotopnd.dev',
  },
  {
    id: 'gork3',
    name: 'GORK-3',
    tagline:
      'A research game measuring whether AI recommendations anchor human judgment in content moderation — 15 real decisions, one Soviet-era classifier.',
    description:
      'Players act as operators of GORK-3, a document classifier inherited from a fallen authoritarian regime, reviewing 15 content-moderation decisions per session: Accept, Reject, or Escalate. On a randomly-assigned subset of documents, GORK-3 displays its own verdict — players can follow or override it. Sessions are logged to measure automation bias: how much GORK-3\'s recommendation shifts human accuracy when correct versus when wrong. A live telemetry dashboard aggregates agreement rate, override accuracy, per-category accuracy, and decision latency across all completed sessions.',
    metrics: [
      { label: 'Session length', value: '15 documents' },
      { label: 'Conditions tracked', value: '4 agent exposure levels' },
      { label: 'Primary signal', value: 'Automation bias' },
      { label: 'Dashboard', value: 'Live cross-session analytics' },
    ],
    demoUrl: 'https://gork3.fotopnd.dev',
  },
]
