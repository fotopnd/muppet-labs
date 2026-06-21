import { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { usePrograms } from '@/api/hooks'

export default function Programs() {
  const { data, isLoading, isError } = usePrograms()
  const [filterCode, setFilterCode] = useState('')

  // Derive conglomerate options from programs data — no extra fetch needed
  const congCodes = useMemo(() => {
    if (!data) return []
    return [...new Set(data.map((p) => p.conglomerate_code))].sort()
  }, [data])

  const filtered = useMemo(() => {
    if (!data) return []
    return filterCode ? data.filter((p) => p.conglomerate_code === filterCode) : data
  }, [data, filterCode])

  if (isLoading) return <div className="p-6 text-text-muted">Loading...</div>
  if (isError) return <div className="p-6 text-text-muted">Failed to load programs.</div>

  return (
    <div className="p-4 md:p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-4 gap-3">
        <h1 className="text-xl font-bold">Programs</h1>
        <select
          value={filterCode}
          onChange={(e) => setFilterCode(e.target.value)}
          className="bg-surface border border-border rounded px-2 py-1 text-sm text-text-primary"
        >
          <option value="">All conferences</option>
          {congCodes.map((code) => (
            <option key={code} value={code}>
              {code}
            </option>
          ))}
        </select>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-text-muted text-xs border-b border-border">
              <th className="text-left py-2 pr-3">#</th>
              <th className="text-left py-2 pr-3">Program</th>
              <th className="text-left py-2 pr-3 hidden sm:table-cell">City</th>
              <th className="text-left py-2 pr-3 hidden md:table-cell">Conf</th>
              <th className="text-right py-2 px-2">Elo</th>
              <th className="text-right py-2 pl-2">W-L</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((p, i) => (
              <tr key={p.id} className="border-b border-border/50 hover:bg-surface/60">
                <td className="py-2 pr-3 text-text-muted">{i + 1}</td>
                <td className="py-2 pr-3">
                  <Link
                    to={`/programs/${p.id}`}
                    className="hover:text-accent transition-colors flex items-center gap-1.5"
                  >
                    <span>{p.emoji}</span>
                    <span>{p.name}</span>
                  </Link>
                </td>
                <td className="py-2 pr-3 text-text-muted hidden sm:table-cell">{p.city}</td>
                <td className="py-2 pr-3 text-text-muted hidden md:table-cell">
                  {p.conglomerate_code}
                </td>
                <td className="py-2 px-2 text-right tabular-nums">{Math.round(p.elo)}</td>
                <td className="py-2 pl-2 text-right tabular-nums text-text-muted">
                  {p.wins}-{p.losses}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
