import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { useCase, useCreateDecision } from '@/api/cases'
import { ErrorMessage } from '@/components/ErrorMessage'
import { SeverityBadge } from '@/components/SeverityBadge'
import { StatusBadge } from '@/components/StatusBadge'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
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
        <div className="text-sm text-muted-foreground">Loading case…</div>
      </div>
    )
  }

  if (isError || !caseData) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-8">
        <ErrorMessage message={(error as Error)?.message ?? 'Case not found'} />
        <Link to="/" className="mt-4 inline-block text-sm text-primary hover:underline">
          ← Back to queue
        </Link>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <div className="mb-4">
        <Link to="/" className="text-sm text-primary hover:underline">
          ← Back to queue
        </Link>
      </div>

      <Card className="mb-6">
        <CardHeader>
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-xs text-muted-foreground">{caseData.id}</span>
            <StatusBadge status={caseData.status} />
            <SeverityBadge severity={caseData.severity} />
            <Badge className="border-transparent bg-blue-50 text-blue-700 hover:bg-blue-50">
              {caseData.category.replace(/_/g, ' ')}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-md bg-muted px-4 py-3 font-mono text-sm leading-relaxed text-foreground">
            {caseData.content}
          </div>
          <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
            <span>Source: {caseData.source}</span>
            <span>Created: {new Date(caseData.created_at).toLocaleString()}</span>
            <span>Updated: {new Date(caseData.updated_at).toLocaleString()}</span>
          </div>
        </CardContent>
      </Card>

      {caseData.decisions.length > 0 && (
        <div className="mb-6">
          <h2 className="mb-2 text-sm font-medium text-foreground">Decision History</h2>
          <div className="space-y-2">
            {caseData.decisions.map((d) => (
              <div
                key={d.id}
                className="flex items-start gap-3 rounded-lg border bg-card p-3 text-sm"
              >
                <StatusBadge
                  status={
                    d.action === 'approve' ? 'approved' : d.action === 'reject' ? 'rejected' : 'escalated'
                  }
                />
                <div className="flex-1">
                  <span className="font-medium text-foreground">{d.actor_id}</span>
                  <span className="mx-1 text-muted-foreground">·</span>
                  <span className="text-muted-foreground">
                    {new Date(d.created_at).toLocaleString()}
                  </span>
                  <p className="mt-0.5 text-muted-foreground">{d.notes}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {submitted ? (
        <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">
          Decision submitted. Returning to queue…
        </div>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Submit Decision</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {mutation.isError && (
                <ErrorMessage message={(mutation.error as Error).message ?? 'Submission failed'} />
              )}

              <div>
                <Label className="mb-2">Action</Label>
                <div className="flex gap-3">
                  {(['approve', 'reject', 'escalate'] as Action[]).map((a) => {
                    const disabled = a === 'escalate' && !CAN_ESCALATE
                    return (
                      <label
                        key={a}
                        className={`flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-sm transition-colors ${
                          action === a
                            ? 'border-ring bg-secondary text-foreground'
                            : 'border-border bg-background text-muted-foreground hover:border-input'
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
                        {disabled && (
                          <span className="text-xs text-muted-foreground">(senior only)</span>
                        )}
                      </label>
                    )
                  })}
                </div>
              </div>

              <div>
                <Label htmlFor="notes" className="mb-2">
                  Notes <span className="text-destructive">*</span>
                </Label>
                <Textarea
                  id="notes"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  required
                  rows={3}
                  placeholder="Required. Briefly explain your decision…"
                />
              </div>

              <Button type="submit" disabled={mutation.isPending || !notes.trim()}>
                {mutation.isPending ? 'Submitting…' : 'Submit Decision'}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
