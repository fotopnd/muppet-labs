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
    <div className="min-h-screen bg-canvas font-sans">
      <header className="bg-surface border-b border-border px-4 py-3">
        <h1 className="text-sm font-semibold text-text-primary tracking-wide">Red-Team Platform</h1>
      </header>
      <nav className="flex border-b-2 border-border bg-surface overflow-x-auto">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2.5 text-sm whitespace-nowrap border-b-2 -mb-0.5 transition-colors ${
              activeTab === tab.id
                ? 'border-accent text-accent font-semibold'
                : 'border-transparent text-text-secondary hover:text-text-primary font-normal'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </nav>
      <main className="p-0">
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
