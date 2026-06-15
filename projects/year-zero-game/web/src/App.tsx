import { Routes, Route } from 'react-router-dom'
import Game from './pages/Game'
import Analytics from './pages/Analytics'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Game />} />
      <Route path="/analytics" element={<Analytics />} />
    </Routes>
  )
}
