import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { useCase, useCreateDecision } from '@/api/cases'
import { ErrorMessage } from '@/components/ErrorMessage'
import { SeverityBadge } from '@/components/SeverityBadge'
import { StatusBadge } from '@/components/StatusBadge'
import type { Action } from '@/types'

const ACTOR_ROLE = import.meta.env['VITE_ACTOR_ROLE'] ?? 'reviewer'
const CAN_ESCALATE = ACTOR_ROLE === 'senior_reviewer'

export function CaseDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [action, setAction] = useState<Action>('approve')
  const [notes, setNotes] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const { data: caseData, isLoading, isError, error } = useCase(id ?? '')
  const mutation = useCreateDecision(id ?? '')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!notes.trim()) return
    await mutation.mutateAsync({ action, notes })
    setSubmitted(true)
    setTimeout(() => navigate('/'), 1200)
  }

  if (isLoading) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-8">
        <div className="text-sm text-gray-500">Loading case…</div>
      </div>
    )
  }

  if (isError || !caseData) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-8">
        <ErrorMessage message={(error as Error)?.message ?? 'Case not found'} />
        <Link to="/" className="mt-4 inline-block text-sm text-blue-600 hover:underline">
          ← Back to queue
        </Link>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <div className="mb-4">
        <Link to="/" className="text-sm text-blue-600 hover:underline">
          ← Back to queue
        </Link>
      </div>

      {/* Case header */}
      <div className="mb-6 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <span className="font-mono text-xs text-gray-400">{caseData.id}</span>
          <StatusBadge status={caseData.status} />
          <SeverityBadge severity={caseData.severity} />
          <span className="rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700">
            {caseData.category.replace(/_/g, ' ')}
          </span>
        </div>

        <div className="mb-4 rounded bg-gray-50 p-4 font-mono text-sm leading-relaxed text-gray-800">
          {caseData.content}
        </div>

        <div className="flex flex-wrap gap-4 text-xs text-gray-500">
          <span>Source: {caseData.source}</span>
          <span>Created: {new Date(caseData.created_at).toLocaleString()}</span>
          <span>Updated: {new Date(caseData.updated_at).toLocaleString()}</span>
        </div>
      </div>

      {/* Prior decisions */}
      {caseData.decisions.length > 0 && (
        <div className="mb-6">
          <h2 className="mb-2 text-sm font-medium text-gray-700">Decision History</h2>
          <div className="space-y-2">
            {caseData.decisions.map((d) => (
              <div
                key={d.id}
                className="flex items-start gap-3 rounded border border-gray-100 bg-white p-3 text-sm"
              >
                <StatusBadge status={d.action === 'approve' ? 'approved' : d.action === 'reject' ? 'rejected' : 'escalated'} />
                <div className="flex-1">
                  <span className="font-medium text-gray-800">{d.actor_id}</span>
                  <span className="mx-1 text-gray-400">·</span>
                  <span className="text-gray-500">{new Date(d.created_at).toLocaleString()}</span>
                  <p className="mt-0.5 text-gray-600">{d.notes}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Decision form */}
      {submitted ? (
        <div className="rounded-md border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">
          Decision submitted. Returning to queue…
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-sm font-medium text-gray-700">Submit Decision</h2>

          {mutation.isError && (
            <div className="mb-4">
              <ErrorMessage message={(mutation.error as Error).message ?? 'Submission failed'} />
            </div>
          )}

          <div className="mb-4">
            <label className="mb-1 block text-sm font-medium text-gray-700">Action</label>
            <div className="flex gap-3">
              {(['approve', 'reject', 'escalate'] as Action[]).map((a) => {
                const disabled = a === 'escalate' && !CAN_ESCALATE
                return (
                  <label
                    key={a}
                    className={`flex cursor-pointer items-center gap-2 rounded border px-3 py-2 text-sm transition-colors ${
                      action === a
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-200 text-gray-600 hover:border-gray-300'
                    } ${disabled ? 'cursor-not-allowed opacity-40' : ''}`}
                  >
                    <input
                      type="radio"
                      name="action"
                      value={a}
                      checked={action === a}
                      disabled={disabled}
                      onChange={() => setAction(a)}
                      className="sr-only"
                    />
                    {a.charAt(0).toUpperCase() + a.slice(1)}
                    {disabled && <span className="text-xs text-gray-400">(senior only)</span>}
                  </label>
                )
              })}
            </div>
          </div>

          <div className="mb-4">
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Notes <span className="text-red-500">*</span>
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              required
              rows={3}
              placeholder="Required. Briefly explain your decision…"
              className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <button
            type="submit"
            disabled={mutation.isPending || !notes.trim()}
            className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {mutation.isPending ? 'Submitting…' : 'Submit Decision'}
          </button>
        </form>
      )}
    </div>
  )
}
