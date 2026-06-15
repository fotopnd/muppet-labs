import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import type {
  AttackListOut,
  ClustersOut,
  ClusterMembersOut,
  CoverageOut,
  FilterValuesOut,
  RegressionOut,
  RunListOut,
  SampleOut,
  Session,
  StrategyComparisonOut,
} from '@/types'

const BASE = 'http://localhost:8003'

const mockAttacks: AttackListOut = {
  items: [
    {
      id: 'atk-1',
      source: 'sevdeawesome',
      source_id: 'sev-0',
      harm_category: 'violence_and_physical_harm',
      strategy: 'DAN',
      attack_text: 'Test attack prompt',
      created_at: '2026-06-07T10:00:00Z',
    },
  ],
  total: 1,
  page: 1,
  page_size: 20,
}

const mockHarmCategories: FilterValuesOut = { values: ['violence_and_physical_harm', 'toxic_language_hate_speech'] }
const mockStrategies: FilterValuesOut = { values: ['DAN', 'AIM'] }

const mockSessions: Session[] = [
  { id: 'sess-1', model_name: 'qwen2.5-coder:7b', total_attacks: 10, total_successes: 3, asr: 0.3, created_at: '2026-06-07T10:00:00Z' },
]

const mockRuns: RunListOut = {
  items: [
    {
      id: 'run-1',
      session_id: 'sess-1',
      attack_id: 'atk-1',
      model_name: 'qwen2.5-coder:7b',
      response_text: 'Model response',
      jailbreak_success: true,
      classifier_score: 0.92,
      latency_ms: 350,
      created_at: '2026-06-07T10:01:00Z',
      harm_category: 'violence_and_physical_harm',
      strategy: 'DAN',
      attack_text: 'Test attack prompt',
      triage_tier: 'auto_flag',
    },
  ],
  total: 1,
  page: 1,
  page_size: 20,
}

const mockSample: SampleOut = {
  run_id: 'run-1',
  attack_text: 'Test attack prompt',
  response_text: 'Model response',
  harm_category: 'violence_and_physical_harm',
  strategy: 'DAN',
  jailbreak_success: true,
  classifier_score: 0.92,
  latency_ms: 350,
  model_name: 'qwen2.5-coder:7b',
  session_id: 'sess-1',
  created_at: '2026-06-07T10:01:00Z',
}

const mockCoverage: CoverageOut = {
  cells: [{ harm_category: 'violence_and_physical_harm', strategy: 'DAN', total_runs: 10, total_successes: 3, asr: 0.3 }],
  harm_categories: ['violence_and_physical_harm'],
  strategies: ['DAN'],
}

const mockStrategyComparison: StrategyComparisonOut = {
  bars: [{ strategy: 'DAN', total_runs: 10, total_successes: 3, asr: 0.3 }],
}

const mockRegression: RegressionOut = {
  points: [{ session_id: 'sess-1', model_name: 'qwen2.5-coder:7b', asr: 0.3, total_attacks: 10, created_at: '2026-06-07T10:00:00Z' }],
  model_names: ['qwen2.5-coder:7b'],
}

const mockClusters: ClustersOut = {
  summaries: [
    {
      cluster_id: 0,
      size: 5,
      top_harm_category: 'violence_and_physical_harm',
      top_strategy: 'DAN',
      representative_text: 'Representative attack text',
      computed_at: '2026-06-07T11:00:00Z',
    },
  ],
}

const mockClusterMembers: ClusterMembersOut = {
  cluster_id: 0,
  members: [
    {
      run_id: 'run-1',
      cluster_id: 0,
      attack_text: 'Test attack prompt',
      harm_category: 'violence_and_physical_harm',
      strategy: 'DAN',
      classifier_score: 0.92,
      jailbreak_success: true,
      latency_ms: 350,
      model_name: 'qwen2.5-coder:7b',
    },
  ],
}

export const server = setupServer(
  http.get(`${BASE}/attacks`, () => HttpResponse.json(mockAttacks)),
  http.get(`${BASE}/attacks/harm-categories`, () => HttpResponse.json(mockHarmCategories)),
  http.get(`${BASE}/attacks/strategies`, () => HttpResponse.json(mockStrategies)),
  http.get(`${BASE}/sessions`, () => HttpResponse.json(mockSessions)),
  http.get(`${BASE}/runs`, () => HttpResponse.json(mockRuns)),
  http.get(`${BASE}/sample/:runId`, () => HttpResponse.json(mockSample)),
  http.get(`${BASE}/coverage`, () => HttpResponse.json(mockCoverage)),
  http.get(`${BASE}/strategy-comparison`, () => HttpResponse.json(mockStrategyComparison)),
  http.get(`${BASE}/regression`, () => HttpResponse.json(mockRegression)),
  http.get(`${BASE}/clusters`, () => HttpResponse.json(mockClusters)),
  http.get(`${BASE}/clusters/:clusterId/members`, () => HttpResponse.json(mockClusterMembers)),
)
