import { Navigate, Route, Routes } from 'react-router-dom'
import TickerBar from '@/components/TickerBar'
import Gamecast from '@/pages/Gamecast'

export default function App() {
  return (
    <div className="min-h-screen bg-canvas text-text-primary">
      <TickerBar />
      <main>
        <Routes>
          <Route path="/games/:gameId" element={<Gamecast />} />
          <Route path="*" element={<Navigate to="/games/153" replace />} />
        </Routes>
      </main>
    </div>
  )
}
