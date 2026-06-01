import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes } from 'react-router-dom'

import { AuditLog } from '@/pages/AuditLog'
import { CaseDetail } from '@/pages/CaseDetail'
import { CaseQueue } from '@/pages/CaseQueue'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50">
          <nav className="border-b border-gray-200 bg-white px-4 py-3 shadow-sm">
            <span className="text-sm font-semibold text-gray-800">
              Safeguards · Case Review
            </span>
          </nav>
          <Routes>
            <Route path="/" element={<CaseQueue />} />
            <Route path="/cases/:id" element={<CaseDetail />} />
            <Route path="/audit" element={<AuditLog />} />
          </Routes>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
