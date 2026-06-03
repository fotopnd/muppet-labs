import { useState } from 'react'
import { PanelTabBar } from '@/components/PanelTabBar'
import { Analytics } from '@/pages/Analytics'
import { HumanReview } from '@/pages/HumanReview'
import { ModelComparison } from '@/pages/ModelComparison'
import { ModelPerformance } from '@/pages/ModelPerformance'
import { StreamMonitor } from '@/pages/StreamMonitor'

type TabId = 'stream-monitor' | 'model-performance' | 'model-comparison' | 'human-review' | 'analytics'

function renderPanel(tab: TabId) {
  switch (tab) {
    case 'stream-monitor':    return <StreamMonitor />
    case 'model-performance': return <ModelPerformance />
    case 'model-comparison':  return <ModelComparison />
    case 'human-review':      return <HumanReview />
    case 'analytics':         return <Analytics />
  }
}

export default function App() {
  const [activeTab, setActiveTab] = useState<TabId>('stream-monitor')

  return (
    <div className="min-h-screen bg-background font-interface">
      <header className="h-14 bg-surface border-b border-border flex items-center px-6">
        <span className="text-base font-semibold text-text-intense font-interface">
          Moderation Dashboard
        </span>
      </header>

      <PanelTabBar activeTab={activeTab} onTabChange={tab => setActiveTab(tab as TabId)} />

      <main className="max-w-7xl mx-auto px-6 py-6">
        {renderPanel(activeTab)}
      </main>
    </div>
  )
}
