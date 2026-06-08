import { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { PanelTabBar } from '@/components/PanelTabBar'
import { Disagreements } from '@/pages/Disagreements'
import { HumanReview } from '@/pages/HumanReview'
import { ModelPerformance } from '@/pages/ModelPerformance'
import { StreamMonitor } from '@/pages/StreamMonitor'
import { TaxonomyTrends } from '@/pages/TaxonomyTrends'

const queryClient = new QueryClient()

const TABS = [
  { id: 'stream', label: 'Stream Monitor' },
  { id: 'performance', label: 'Model Performance' },
  { id: 'taxonomy', label: 'Taxonomy Trends' },
  { id: 'review', label: 'Human Review' },
  { id: 'disagreements', label: 'Disagreements' },
]

function Dashboard() {
  const [activeTab, setActiveTab] = useState('stream')

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="h-14 bg-white border-b border-slate-200 flex items-center px-6">
        <h1 className="text-base font-semibold text-slate-900">LLM Safety Monitor</h1>
      </header>
      <main className="max-w-7xl mx-auto px-6 py-6">
        <PanelTabBar tabs={TABS} activeTab={activeTab} onSelect={setActiveTab} />
        {activeTab === 'stream' && <StreamMonitor />}
        {activeTab === 'performance' && <ModelPerformance />}
        {activeTab === 'taxonomy' && <TaxonomyTrends />}
        {activeTab === 'review' && <HumanReview />}
        {activeTab === 'disagreements' && <Disagreements />}
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
