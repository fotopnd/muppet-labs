import { NavLink, useParams } from 'react-router-dom'

const SUB_LINKS = [
  { suffix: '', label: 'Scoreboard', end: true },
  { suffix: '/schedule', label: 'Schedule', end: false },
  { suffix: '/standings', label: 'Standings', end: false },
  { suffix: '/programs', label: 'Programs', end: false },
  { suffix: '/stats', label: 'Stats', end: false },
]

export default function ConferenceNav() {
  const { code } = useParams<{ code: string }>()
  const base = `/conference/${code}`

  return (
    <div className="border-b border-border bg-surface/50 overflow-x-auto">
      <div className="flex items-center px-4">
        {SUB_LINKS.map(({ suffix, label, end }) => (
          <NavLink
            key={label}
            to={`${base}${suffix}`}
            end={end}
            className={({ isActive }) =>
              `text-sm px-3 py-2 border-b-2 transition-colors shrink-0 ${
                isActive
                  ? 'border-accent text-accent font-semibold'
                  : 'border-transparent text-text-muted hover:text-text-primary'
              }`
            }
          >
            {label}
          </NavLink>
        ))}
      </div>
    </div>
  )
}
