type Tab = {
  id: string
  label: string
}

const TABS: Tab[] = [
  { id: 'stream-monitor', label: 'Stream Monitor' },
  { id: 'model-performance', label: 'Model Performance' },
  { id: 'model-comparison', label: 'Model Comparison' },
  { id: 'human-review', label: 'Human Review' },
  { id: 'analytics', label: 'Analytics' },
]

type PanelTabBarProps = {
  activeTab: string
  onTabChange: (tab: string) => void
}

export function PanelTabBar({ activeTab, onTabChange }: PanelTabBarProps) {
  return (
    <nav className="border-b border-border">
      <ul className="flex">
        {TABS.map(tab => (
          <li key={tab.id}>
            <button
              onClick={() => onTabChange(tab.id)}
              className={[
                'px-4 py-3 text-sm font-interface transition-colors border-b-2',
                activeTab === tab.id
                  ? 'border-accent text-text-intense font-medium'
                  : 'border-transparent text-text-muted hover:text-text-default',
              ].join(' ')}
            >
              {tab.label}
            </button>
          </li>
        ))}
      </ul>
    </nav>
  )
}
