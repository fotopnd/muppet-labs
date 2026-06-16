import { Routes, Route } from 'react-router-dom'
import Game from './pages/Game'
import Analytics from './pages/Analytics'
import Result from './pages/Result'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Game />} />
      <Route path="/analytics" element={<Analytics />} />
      <Route path="/result/:shareId" element={<Result />} />
    </Routes>
  )
}
