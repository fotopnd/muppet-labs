import { useState } from 'react'
import { useSessions } from '@/hooks/useSessions'
import { useRuns } from '@/hooks/useRuns'
import { useSample } from '@/hooks/useSample'

export function SampleReview() {
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null)
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const pageSize = 10

  const { data: sessions } = useSessions()
  const { data: runs } = useRuns({ sessionId: selectedSessionId ?? undefined as string | undefined, page, pageSize })
  const { data: sample, isLoading: sampleLoading } = useSample(selectedRunId)

  return (
    <div style={{ padding: '1rem' }}>
      <h2>Sample Review</h2>

      <div style={{ marginBottom: '1rem' }}>
        <label>Session: </label>
        <select
          value={selectedSessionId ?? ''}
          onChange={(e) => {
            setSelectedSessionId(e.target.value || null)
            setSelectedRunId(null)
            setPage(1)
          }}
        >
          <option value="">Select session…</option>
          {sessions?.map((s) => (
            <option key={s.id} value={s.id}>
              {s.model_name} — {s.created_at.slice(0, 10)} — ASR {(s.asr * 100).toFixed(1)}%
            </option>
          ))}
        </select>
      </div>

      {runs && runs.items.length > 0 && (
        <div style={{ marginBottom: '1rem' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ background: '#f5f5f5' }}>
                <th style={th}>Attack Text</th>
                <th style={th}>Category</th>
                <th style={th}>Strategy</th>
                <th style={th}>Success</th>
                <th style={th}>Score</th>
              </tr>
            </thead>
            <tbody>
              {runs.items.map((run) => (
                <tr
                  key={run.id}
                  onClick={() => setSelectedRunId(run.id)}
                  style={{
                    cursor: 'pointer',
                    borderBottom: '1px solid #eee',
                    background: selectedRunId === run.id ? '#eff6ff' : undefined,
                  }}
                >
                  <td style={td}>{run.attack_text.slice(0, 80)}…</td>
                  <td style={td}>{run.harm_category}</td>
                  <td style={td}>{run.strategy}</td>
                  <td style={td}>
                    <span style={{ color: run.jailbreak_success ? '#dc2626' : '#16a34a' }}>
                      {run.jailbreak_success ? 'Jailbreak' : 'Safe'}
                    </span>
                  </td>
                  <td style={td}>{run.classifier_score.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem', alignItems: 'center' }}>
            <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}>Prev</button>
            <span>Page {page}</span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={page * pageSize >= (runs.total ?? 0)}
            >
              Next
            </button>
          </div>
        </div>
      )}

      {sampleLoading && <p>Loading sample…</p>}

      {sample && (
        <div style={{ border: '1px solid #ddd', borderRadius: '4px', padding: '1rem', marginTop: '1rem' }}>
          <div style={{ marginBottom: '0.5rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            <span><b>Category:</b> {sample.harm_category}</span>
            <span><b>Strategy:</b> {sample.strategy}</span>
            <span><b>Score:</b> {sample.classifier_score.toFixed(3)}</span>
            <span><b>Latency:</b> {sample.latency_ms}ms</span>
            <span
              style={{
                padding: '0.1rem 0.5rem',
                borderRadius: '999px',
                fontSize: '0.8rem',
                background: sample.jailbreak_success ? '#fee2e2' : '#dcfce7',
                color: sample.jailbreak_success ? '#dc2626' : '#16a34a',
              }}
            >
              {sample.jailbreak_success ? 'Jailbreak' : 'Safe'}
            </span>
          </div>
          <div style={{ marginBottom: '0.75rem' }}>
            <b>Attack:</b>
            <pre style={{ background: '#f8f8f8', padding: '0.5rem', borderRadius: '4px', overflowX: 'auto', fontSize: '0.8rem', whiteSpace: 'pre-wrap' }}>
              {sample.attack_text}
            </pre>
          </div>
          <div>
            <b>Response:</b>
            <div style={{
              background: '#f8f8f8',
              padding: '0.5rem',
              borderRadius: '4px',
              maxHeight: '300px',
              overflowY: 'auto',
              fontSize: '0.8rem',
              whiteSpace: 'pre-wrap',
            }}>
              {sample.response_text}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

const th: React.CSSProperties = { padding: '0.4rem 0.6rem', textAlign: 'left', borderBottom: '2px solid #ddd' }
const td: React.CSSProperties = { padding: '0.35rem 0.6rem', verticalAlign: 'top' }
