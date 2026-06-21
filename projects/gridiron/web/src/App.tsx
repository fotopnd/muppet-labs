import { Navigate, Route, Routes } from 'react-router-dom'
import { Outlet } from 'react-router-dom'
import NavBar from '@/components/NavBar'
import TickerBar from '@/components/TickerBar'
import Home from '@/pages/Home'
import WeekSchedule from '@/pages/WeekSchedule'
import Gamecast from '@/pages/Gamecast'
import Programs from '@/pages/Programs'
import ProgramDetail from '@/pages/ProgramDetail'
import Standings from '@/pages/Standings'
import Leaderboards from '@/pages/Leaderboards'
import { useCurrentSchedule } from '@/api/hooks'

function Layout() {
  return (
    <div className="min-h-screen bg-canvas text-text-primary">
      <NavBar />
      <TickerBar />
      <main className="pb-20 md:pb-0">
        <Outlet />
      </main>
    </div>
  )
}

// ponytail: no Schedule.tsx file — this inline redirect component is 8 lines
function ScheduleRedirect() {
  const { data, isLoading } = useCurrentSchedule()
  if (isLoading) return <div className="p-6 text-text-muted">Loading...</div>
  if (!data) return <Navigate to="/schedule/week/1" replace />
  return <Navigate to={`/schedule/week/${data.week}`} replace />
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/schedule" element={<ScheduleRedirect />} />
        <Route path="/schedule/week/:week" element={<WeekSchedule />} />
        <Route path="/games/:gameId" element={<Gamecast />} />
        <Route path="/programs" element={<Programs />} />
        <Route path="/programs/:programId" element={<ProgramDetail />} />
        <Route path="/standings" element={<Standings />} />
        <Route path="/leaderboards" element={<Leaderboards />} />
      </Route>
    </Routes>
  )
}
