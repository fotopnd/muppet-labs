import { Link } from 'react-router-dom'
import { useAllConglomerates } from '@/api/hooks'

export default function Home() {
  const { data, isLoading } = useAllConglomerates()

  if (isLoading) return <div className="p-6 text-text-muted">Loading...</div>

  return (
    <div className="p-4 md:p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-1">NAFCA</h1>
      <p className="text-text-muted text-sm mb-6">National Association of Fictional Collegiate Athletics</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {(data ?? []).map((conf) => (
          <Link
            key={conf.code}
            to={`/conference/${conf.code}`}
            className="flex items-center gap-4 bg-surface border border-border rounded-lg p-4 hover:border-accent/40 transition-colors"
          >
            <div
              className="w-1.5 self-stretch rounded-full shrink-0"
              style={{ backgroundColor: conf.primary_color }}
            />
            <div>
              <div className="font-semibold">{conf.full_name}</div>
              <div className="text-xs text-text-muted mt-0.5">{conf.network} · {conf.region}</div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
