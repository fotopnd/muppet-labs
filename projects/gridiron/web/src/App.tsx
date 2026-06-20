import { Routes, Route } from 'react-router-dom'

// Pages registered here by the implementer role.

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<div>Gridiron</div>} />
    </Routes>
  )
}
