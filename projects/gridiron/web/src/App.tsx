import { Navigate, Route, Routes } from 'react-router-dom'
import NavBar from '@/components/NavBar'
import TickerBar from '@/components/TickerBar'
import Home from '@/pages/Home'
import WeekSchedule from '@/pages/WeekSchedule'
import ConferencePage from '@/pages/ConferencePage'
import Standings from '@/pages/Standings'
import Programs from '@/pages/Programs'
import ProgramDetail from '@/pages/ProgramDetail'
import Leaderboards from '@/pages/Leaderboards'
import Gamecast from '@/pages/Gamecast'

export default function App() {
  return (
    <div className="min-h-screen bg-canvas text-text-primary">
      <NavBar />
      <TickerBar />
      <main className="pb-16 md:pb-0">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/conference/:code" element={<ConferencePage />} />
          <Route path="/schedule/week/:week" element={<WeekSchedule />} />
          <Route path="/schedule" element={<Navigate to="/schedule/week/1" replace />} />
          <Route path="/standings" element={<Standings />} />
          <Route path="/programs" element={<Programs />} />
          <Route path="/programs/:programId" element={<ProgramDetail />} />
          <Route path="/leaderboards" element={<Leaderboards />} />
          <Route path="/games/:gameId" element={<Gamecast />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}
