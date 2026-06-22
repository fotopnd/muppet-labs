import { NavLink } from 'react-router-dom'

const LINKS = [
  { to: '/', label: 'Home', icon: '🏠' },
  { to: '/schedule/week/1', label: 'Schedule', icon: '📅' },
  { to: '/standings', label: 'Standings', icon: '🏆' },
  { to: '/programs', label: 'Programs', icon: '🎓' },
  { to: '/leaderboards', label: 'Leaders', icon: '📊' },
]

function linkClass({ isActive }: { isActive: boolean }) {
  return isActive
    ? 'text-accent font-semibold'
    : 'text-text-muted hover:text-text-primary transition-colors'
}

export default function NavBar() {
  return (
    <>
      {/* Desktop top bar */}
      <nav className="hidden md:flex items-center gap-6 px-6 py-3 border-b border-border bg-surface">
        <span className="text-text-primary font-bold tracking-wide mr-4">NAFCA</span>
        {LINKS.map(({ to, label }) => (
          <NavLink key={to} to={to} className={linkClass} end={to === '/'}>
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Mobile bottom bar */}
      <nav className="md:hidden fixed bottom-0 inset-x-0 z-50 flex border-t border-border bg-surface pb-safe">
        {LINKS.map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex-1 flex flex-col items-center py-2 text-xs gap-0.5 ${
                isActive ? 'text-accent' : 'text-text-muted'
              }`
            }
          >
            <span className="text-lg leading-none">{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>
    </>
  )
}
