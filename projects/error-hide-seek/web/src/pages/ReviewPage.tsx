import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'

import { AnnotatedAbstract } from '@/components/AnnotatedAbstract'
import { CompletionBanner } from '@/components/CompletionBanner'
import { DetectionList } from '@/components/DetectionList'
import { PaperHeader } from '@/components/PaperHeader'
import { SelectionFloater } from '@/components/SelectionFloater'
import { useSession } from '@/hooks/useSession'
import { useSubmitReview } from '@/hooks/useSubmitReview'
import type { DetectionIn } from '@/types'

export function ReviewPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const id = sessionId ? parseInt(sessionId, 10) : null
  const { data: session, isLoading, isError } = useSession(id)

  const [detections, setDetections] = useState<DetectionIn[]>([])
  const [floaterPos, setFloaterPos] = useState<{ top: number; left: number } | null>(null)
  const [pendingExcerpt, setPendingExcerpt] = useState<string | null>(null)

  const submitMutation = useSubmitReview(session)

  useEffect(() => {
    function onMouseDown(e: MouseEvent) {
      const target = e.target as HTMLElement
      if (!target.closest('[data-floater]')) {
        setFloaterPos(null)
        setPendingExcerpt(null)
      }
    }
    document.addEventListener('mousedown', onMouseDown)
    return () => document.removeEventListener('mousedown', onMouseDown)
  }, [])

  function handleMouseUp() {
    const sel = window.getSelection()
    const text = sel?.toString().trim() ?? ''
    if (text.length >= 15) {
      const rect = sel!.getRangeAt(0).getBoundingClientRect()
      setFloaterPos({ top: rect.bottom + 8, left: rect.left })
      setPendingExcerpt(text)
    } else {
      setFloaterPos(null)
      setPendingExcerpt(null)
    }
  }

  function handleFlag(excerpt: string) {
    setDetections((prev) => [...prev, { text_excerpt: excerpt, note: null }])
    window.getSelection()?.removeAllRanges()
    setFloaterPos(null)
    setPendingExcerpt(null)
  }

  function handleRemove(index: number) {
    setDetections((prev) => prev.filter((_, i) => i !== index))
  }

  function handleNoteChange(index: number, note: string) {
    setDetections((prev) => prev.map((d, i) => (i === index ? { ...d, note: note || null } : d)))
  }

  function handleSubmit() {
    if (!session) return
    submitMutation.mutate({ session_id: session.session_id, detections })
  }

  if (isLoading) {
    return (
      <main className="max-w-3xl mx-auto px-6 py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-slate-200 rounded w-3/4" />
          <div className="h-48 bg-slate-200 rounded" />
        </div>
      </main>
    )
  }

  if (isError || !session) {
    return (
      <main className="max-w-3xl mx-auto px-6 py-8">
        <p className="font-interface text-sm text-danger">
          Session unavailable — check API
        </p>
      </main>
    )
  }

  return (
    <main className="max-w-3xl mx-auto px-6 py-8 flex flex-col gap-6">
      <PaperHeader session={session} />

      <div onMouseUp={handleMouseUp}>
        <AnnotatedAbstract abstract={session.abstract_text} annotations={session.annotations} />
      </div>

      <SelectionFloater
        floaterPos={floaterPos}
        pendingExcerpt={pendingExcerpt}
        onFlag={handleFlag}
      />

      {session.status === 'completed' ? (
        <CompletionBanner />
      ) : (
        <DetectionList
          detections={detections}
          onRemove={handleRemove}
          onNoteChange={handleNoteChange}
          onSubmit={handleSubmit}
          submitting={submitMutation.isPending}
        />
      )}
    </main>
  )
}
