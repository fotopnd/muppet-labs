import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, NavLink, Route, Routes } from 'react-router-dom'

import { AuditLog } from '@/pages/AuditLog'
import { CaseDetail } from '@/pages/CaseDetail'
import { CaseQueue } from '@/pages/CaseQueue'
import { StreamDashboard } from '@/pages/StreamDashboard'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
  },
})

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  `text-sm ${isActive ? 'text-gray-900 font-medium' : 'text-gray-500 hover:text-gray-700'}`

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50">
          <nav className="border-b border-gray-200 bg-white px-4 py-3 shadow-sm flex items-center gap-6">
            <span className="text-sm font-semibold text-gray-800">
              Safeguards · Case Review
            </span>
            <NavLink to="/" end className={navLinkClass}>Cases</NavLink>
            <NavLink to="/audit-log" className={navLinkClass}>Audit Log</NavLink>
            <NavLink to="/stream" className={navLinkClass}>Stream</NavLink>
          </nav>
          <Routes>
            <Route path="/" element={<CaseQueue />} />
            <Route path="/cases/:id" element={<CaseDetail />} />
            <Route path="/audit-log" element={<AuditLog />} />
            <Route path="/stream" element={<StreamDashboard />} />
          </Routes>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
