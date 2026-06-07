import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom'

import { ResultsPage } from '@/pages/ResultsPage'
import { ReviewPage } from '@/pages/ReviewPage'

const queryClient = new QueryClient()

function Breadcrumb() {
  const { pathname } = useLocation()
  if (pathname.startsWith('/review/')) return <span>Review Session</span>
  if (pathname.startsWith('/results/')) return <span>Experiment Results</span>
  return null
}

function Shell() {
  return (
    <div className="min-h-screen bg-background font-interface">
      <header className="h-14 bg-surface border-b border-border flex items-center justify-between px-6">
        <span className="font-interface text-sm font-semibold text-text-intense">
          Error-Hide-Seek
        </span>
        <span className="font-interface text-xs text-text-muted">
          <Breadcrumb />
        </span>
      </header>
      <Routes>
        <Route path="/review/:sessionId" element={<ReviewPage />} />
        <Route path="/results/:experimentId" element={<ResultsPage />} />
        <Route path="*" element={<Navigate to="/review/1" replace />} />
      </Routes>
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Shell />
      </BrowserRouter>
    </QueryClientProvider>
  )
}
