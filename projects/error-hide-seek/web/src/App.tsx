import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { HomePage } from '@/pages/HomePage'
import { ReviewPage } from '@/pages/ReviewPage'

const queryClient = new QueryClient()

function Shell() {
  return (
    <div className="min-h-screen bg-background font-interface">
      <header className="h-14 bg-surface border-b border-border flex items-center justify-between px-6">
        <span className="font-interface text-sm font-semibold text-text-intense">
          Error-Hide-Seek Testbed
        </span>
        <a
          href="https://www.fotopnd.dev"
          className="font-interface text-xs text-text-muted hover:text-text-intense transition-colors"
        >
          ← Portfolio
        </a>
      </header>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/review/:sessionId" element={<ReviewPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
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
