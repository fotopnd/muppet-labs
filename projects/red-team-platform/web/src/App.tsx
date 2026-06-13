import { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AttackBrowser } from '@/pages/AttackBrowser'
import { CoverageHeatmap } from '@/pages/CoverageHeatmap'
import { StrategyComparison } from '@/pages/StrategyComparison'
import { RegressionTracker } from '@/pages/RegressionTracker'
import { SampleReview } from '@/pages/SampleReview'
import { FailureClusters } from '@/pages/FailureClusters'
import { BiasHeatmap } from '@/pages/BiasHeatmap'

const queryClient = new QueryClient()

type Tab = 'attacks' | 'coverage' | 'strategy' | 'regression' | 'sample' | 'clusters' | 'bias'

const TABS: { id: Tab; label: string }[] = [
  { id: 'attacks', label: 'Attack Browser' },
  { id: 'coverage', label: 'Coverage Heatmap' },
  { id: 'strategy', label: 'Strategy Comparison' },
  { id: 'regression', label: 'Regression Tracker' },
  { id: 'sample', label: 'Sample Review' },
  { id: 'clusters', label: 'Failure Clusters' },
  { id: 'bias', label: 'Bias Heatmap' },
]

function Dashboard() {
  const [activeTab, setActiveTab] = useState<Tab>('attacks')

  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', minHeight: '100vh' }}>
      <header style={{ background: '#1e293b', color: '#fff', padding: '0.75rem 1rem' }}>
        <h1 style={{ margin: 0, fontSize: '1.1rem', letterSpacing: '0.02em' }}>Red-Team Platform</h1>
      </header>
      <nav style={{ display: 'flex', borderBottom: '2px solid #e2e8f0', background: '#f8fafc' }}>
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '0.6rem 1rem',
              border: 'none',
              borderBottom: activeTab === tab.id ? '2px solid #4f46e5' : '2px solid transparent',
              background: 'none',
              cursor: 'pointer',
              fontWeight: activeTab === tab.id ? 600 : 400,
              color: activeTab === tab.id ? '#4f46e5' : '#475569',
              fontSize: '0.9rem',
              marginBottom: '-2px',
            }}
          >
            {tab.label}
          </button>
        ))}
      </nav>
      <main>
        {activeTab === 'attacks' && <AttackBrowser />}
        {activeTab === 'coverage' && <CoverageHeatmap />}
        {activeTab === 'strategy' && <StrategyComparison />}
        {activeTab === 'regression' && <RegressionTracker />}
        {activeTab === 'sample' && <SampleReview />}
        {activeTab === 'clusters' && <FailureClusters />}
        {activeTab === 'bias' && <BiasHeatmap />}
      </main>
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Dashboard />
    </QueryClientProvider>
  )
}
