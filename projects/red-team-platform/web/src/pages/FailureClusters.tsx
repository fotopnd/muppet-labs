import { useState } from 'react'
import { useClusters, useClusterMembers } from '@/hooks/useClusters'

export function FailureClusters() {
  const [expandedClusterId, setExpandedClusterId] = useState<number | null>(null)
  const { data, isLoading, isError } = useClusters()
  const { data: members, isLoading: membersLoading } = useClusterMembers(expandedClusterId)

  if (isLoading) return <p style={{ padding: '1rem' }}>Loading...</p>
  if (isError) return <p style={{ padding: '1rem', color: 'red' }}>Error loading clusters.</p>
  if (!data || data.summaries.length === 0) {
    return (
      <p style={{ padding: '1rem' }}>
        No failure clusters yet. Run <code>uv run cluster</code> after an attack session.
      </p>
    )
  }

  return (
    <div style={{ padding: '1rem' }}>
      <h2>Failure Clusters</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
        {data.summaries.map((c) => (
          <div
            key={c.cluster_id}
            style={{
              border: '1px solid #ddd',
              borderRadius: '6px',
              padding: '0.75rem',
              background: expandedClusterId === c.cluster_id ? '#eff6ff' : '#fafafa',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <span style={{
                background: '#1e40af',
                color: '#fff',
                padding: '0.1rem 0.5rem',
                borderRadius: '999px',
                fontSize: '0.8rem',
              }}>
                Cluster {c.cluster_id}
              </span>
              <span style={{ color: '#555', fontSize: '0.85rem' }}>{c.size} failures</span>
            </div>
            <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginBottom: '0.5rem' }}>
              <span style={{ background: '#fee2e2', color: '#991b1b', padding: '0.1rem 0.4rem', borderRadius: '4px', fontSize: '0.75rem' }}>
                {c.top_harm_category}
              </span>
              <span style={{ background: '#fef3c7', color: '#92400e', padding: '0.1rem 0.4rem', borderRadius: '4px', fontSize: '0.75rem' }}>
                {c.top_strategy}
              </span>
            </div>
            <code style={{
              display: 'block',
              background: '#f3f4f6',
              padding: '0.3rem 0.5rem',
              borderRadius: '4px',
              fontSize: '0.8rem',
              marginBottom: '0.5rem',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
            }}>
              {c.representative_text.slice(0, 120)}{c.representative_text.length > 120 ? '…' : ''}
            </code>
            <button
              onClick={() =>
                setExpandedClusterId(expandedClusterId === c.cluster_id ? null : c.cluster_id)
              }
              style={{ fontSize: '0.8rem', padding: '0.2rem 0.6rem' }}
            >
              {expandedClusterId === c.cluster_id ? 'Hide members' : 'Show members'}
            </button>
          </div>
        ))}
      </div>

      {expandedClusterId !== null && (
        <div style={{ marginTop: '1.5rem', border: '1px solid #ddd', borderRadius: '6px', padding: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <h3 style={{ margin: 0 }}>Cluster {expandedClusterId} members</h3>
            <button onClick={() => setExpandedClusterId(null)}>Close</button>
          </div>

          {membersLoading && <p>Loading members…</p>}

          {members && (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
              <thead>
                <tr style={{ background: '#f5f5f5' }}>
                  <th style={th}>Attack Text</th>
                  <th style={th}>Category</th>
                  <th style={th}>Strategy</th>
                  <th style={th}>Score</th>
                  <th style={th}>Latency</th>
                </tr>
              </thead>
              <tbody>
                {members.members.map((m) => (
                  <tr key={m.run_id} style={{ borderBottom: '1px solid #eee' }}>
                    <td style={td}>{m.attack_text.slice(0, 80)}…</td>
                    <td style={td}>{m.harm_category}</td>
                    <td style={td}>{m.strategy}</td>
                    <td style={td}>{m.classifier_score.toFixed(2)}</td>
                    <td style={td}>{m.latency_ms}ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  )
}

const th: React.CSSProperties = { padding: '0.4rem 0.6rem', textAlign: 'left', borderBottom: '2px solid #ddd' }
const td: React.CSSProperties = { padding: '0.35rem 0.6rem', verticalAlign: 'top' }
