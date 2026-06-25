import { NavLink } from 'react-router-dom'
import { useAllConglomerates } from '@/api/hooks'

function linkClass({ isActive }: { isActive: boolean }) {
  return `text-sm px-2 py-1.5 rounded shrink-0 transition-colors ${
    isActive ? 'text-accent font-semibold' : 'text-text-muted hover:text-text-primary'
  }`
}

export default function NavBar() {
  const { data: conglomerates } = useAllConglomerates()

  return (
    <nav className="border-b border-border bg-surface">
      <div className="flex items-center gap-1 px-4 py-1.5 overflow-x-auto">
        <NavLink
          to="/"
          end
          className={({ isActive }) =>
            `text-sm px-2 py-1.5 rounded shrink-0 font-bold transition-colors ${
              isActive ? 'text-accent' : 'text-text-primary hover:text-accent'
            }`
          }
        >
          NAFCA
        </NavLink>
        <span className="text-border/60 mx-1 shrink-0 select-none">|</span>
        {(conglomerates ?? []).map(c => (
          <NavLink key={c.code} to={`/conference/${c.code}`} className={linkClass}>
            {c.code}
          </NavLink>
        ))}
        <span className="flex-1 min-w-2" />
        <NavLink to="/stats" className={linkClass}>Stats</NavLink>
        <NavLink to="/leaderboard" className={linkClass}>Leaderboard</NavLink>
      </div>
    </nav>
  )
}
