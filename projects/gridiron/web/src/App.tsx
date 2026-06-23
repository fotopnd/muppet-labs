import { Navigate, Route, Routes } from 'react-router-dom'
import NavBar from '@/components/NavBar'
import TickerBar from '@/components/TickerBar'
import ConferenceLayout from '@/layouts/ConferenceLayout'
import Home from '@/pages/Home'
import ConferencePage from '@/pages/ConferencePage'
import ConferenceSchedule from '@/pages/ConferenceSchedule'
import ConferenceStandings from '@/pages/ConferenceStandings'
import ConferencePrograms from '@/pages/ConferencePrograms'
import ConferenceStats from '@/pages/ConferenceStats'
import NafcaLeaderboard from '@/pages/NafcaLeaderboard'
import NafcaStats from '@/pages/NafcaStats'
import ProgramDetail from '@/pages/ProgramDetail'
import Gamecast from '@/pages/Gamecast'
import PlayerPage from '@/pages/PlayerPage'

export default function App() {
  return (
    <div className="min-h-screen bg-canvas text-text-primary">
      <NavBar />
      <TickerBar />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/conference/:code" element={<ConferenceLayout />}>
            <Route index element={<ConferencePage />} />
            <Route path="schedule" element={<ConferenceSchedule />} />
            <Route path="schedule/week/:week" element={<ConferenceSchedule />} />
            <Route path="standings" element={<ConferenceStandings />} />
            <Route path="programs" element={<ConferencePrograms />} />
            <Route path="programs/:programId" element={<ProgramDetail />} />
            <Route path="stats" element={<ConferenceStats />} />
          </Route>
          <Route path="/stats" element={<NafcaStats />} />
          <Route path="/leaderboard" element={<NafcaLeaderboard />} />
          <Route path="/games/:gameId" element={<Gamecast />} />
          <Route path="/players/:playerId" element={<PlayerPage />} />
          {/* legacy redirects */}
          <Route path="/standings" element={<Navigate to="/" replace />} />
          <Route path="/schedule/*" element={<Navigate to="/" replace />} />
          <Route path="/programs/*" element={<Navigate to="/" replace />} />
          <Route path="/leaderboards" element={<Navigate to="/leaderboard" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}
