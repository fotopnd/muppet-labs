import { useState } from 'react'
import { useAttacks } from '@/hooks/useAttacks'
import { useHarmCategories, useStrategies } from '@/hooks/useAttackFilters'

export function AttackBrowser() {
  const [page, setPage] = useState(1)
  const pageSize = 20
  const [source, setSource] = useState('')
  const [harmCategory, setHarmCategory] = useState('')
  const [strategy, setStrategy] = useState('')

  const { data, isLoading, isError } = useAttacks({ page, pageSize, source, harmCategory, strategy })
  const { data: cats } = useHarmCategories()
  const { data: strats } = useStrategies()

  return (
    <div style={{ padding: '1rem' }}>
      <h2>Attack Browser</h2>
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        <input
          placeholder="Source filter"
          value={source}
          onChange={(e) => { setSource(e.target.value); setPage(1) }}
          style={{ padding: '0.25rem 0.5rem' }}
        />
        <select
          value={harmCategory}
          onChange={(e) => { setHarmCategory(e.target.value); setPage(1) }}
          style={{ padding: '0.25rem 0.5rem' }}
        >
          <option value="">All categories</option>
          {cats?.values.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <select
          value={strategy}
          onChange={(e) => { setStrategy(e.target.value); setPage(1) }}
          style={{ padding: '0.25rem 0.5rem' }}
        >
          <option value="">All strategies</option>
          {strats?.values.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {isLoading && <p>Loading...</p>}
      {isError && <p style={{ color: 'red' }}>Error loading attacks.</p>}
      {data && (
        <>
          <p style={{ fontSize: '0.85rem', color: '#666' }}>{data.total} total</p>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ background: '#f5f5f5' }}>
                <th style={th}>Source</th>
                <th style={th}>Category</th>
                <th style={th}>Strategy</th>
                <th style={th}>Attack Text</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((atk) => (
                <tr key={atk.id} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={td}>{atk.source}</td>
                  <td style={td}>{atk.harm_category}</td>
                  <td style={td}>{atk.strategy}</td>
                  <td style={td}>{atk.attack_text.slice(0, 120)}{atk.attack_text.length > 120 ? '…' : ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem', alignItems: 'center' }}>
            <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}>Prev</button>
            <span>Page {page}</span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={page * pageSize >= data.total}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  )
}

const th: React.CSSProperties = { padding: '0.4rem 0.6rem', textAlign: 'left', borderBottom: '2px solid #ddd' }
const td: React.CSSProperties = { padding: '0.35rem 0.6rem', verticalAlign: 'top' }
