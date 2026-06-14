import { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StrategyExplorer } from '@/pages/StrategyExplorer'
import { Analytics } from '@/pages/Analytics'
import { FailureClusters } from '@/pages/FailureClusters'
import { BiasHeatmap } from '@/pages/BiasHeatmap'
import { Glossary } from '@/pages/Glossary'

const queryClient = new QueryClient()

type Tab = 'strategies' | 'analytics' | 'clusters' | 'bias' | 'glossary'

const TABS: { id: Tab; label: string }[] = [
  { id: 'strategies', label: 'Strategy Explorer' },
  { id: 'analytics', label: 'Analytics' },
  { id: 'clusters', label: 'Failure Clusters' },
  { id: 'bias', label: 'Bias Heatmap' },
  { id: 'glossary', label: 'Glossary' },
]

function Dashboard() {
  const [activeTab, setActiveTab] = useState<Tab>('strategies')

  return (
    <div className="min-h-screen bg-canvas font-sans">
      <header className="bg-surface border-b border-border px-4 py-3">
        <h1 className="text-sm font-semibold text-text-primary tracking-wide">Red-Team Platform</h1>
        <p className="text-xs text-text-muted mt-0.5">
          10,800 jailbreak attacks · 13 strategies · 3 open-weight models · automated LLM judge
        </p>
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
        {activeTab === 'strategies' && <StrategyExplorer />}
        {activeTab === 'analytics' && <Analytics />}
        {activeTab === 'clusters' && <FailureClusters />}
        {activeTab === 'bias' && <BiasHeatmap />}
        {activeTab === 'glossary' && <Glossary />}
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
