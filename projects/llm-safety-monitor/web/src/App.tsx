import { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { PanelTabBar } from '@/components/PanelTabBar'
import { Calibration } from '@/pages/Calibration'
import { HumanReview } from '@/pages/HumanReview'
import { ModelComparison } from '@/pages/ModelComparison'
import { ModelPerformance } from '@/pages/ModelPerformance'
import { StreamMonitor } from '@/pages/StreamMonitor'

const queryClient = new QueryClient()

const TABS = [
  { id: 'stream', label: 'Stream Monitor' },
  { id: 'performance', label: 'Model Performance' },
  { id: 'comparison', label: 'Model Comparison' },
  { id: 'calibration', label: 'Calibration' },
  { id: 'review', label: 'Human Review' },
]

function Dashboard() {
  const [activeTab, setActiveTab] = useState('stream')

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <h1 className="text-xl font-semibold text-gray-900">LLM Safety Monitor</h1>
      </header>
      <main className="max-w-6xl mx-auto px-6 py-6">
        <PanelTabBar tabs={TABS} activeTab={activeTab} onSelect={setActiveTab} />
        {activeTab === 'stream' && <StreamMonitor />}
        {activeTab === 'performance' && <ModelPerformance />}
        {activeTab === 'comparison' && <ModelComparison />}
        {activeTab === 'calibration' && <Calibration />}
        {activeTab === 'review' && <HumanReview />}
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
