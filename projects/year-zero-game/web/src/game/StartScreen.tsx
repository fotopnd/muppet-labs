import type { ReactNode } from 'react'

interface StartScreenProps {
  onStart: () => void
  loading?: boolean
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="w-full max-w-[300px]">
      <p className="font-pixel text-pixel-terminal text-[8px] mb-3 border-b border-pixel-terminal/30 pb-1">
        {title}
      </p>
      <div className="font-pixel text-pixel-card/70 text-[7px] leading-6 space-y-2">
        {children}
      </div>
    </div>
  )
}

export default function StartScreen({ onStart, loading }: StartScreenProps) {
  return (
    <div className="fixed inset-0 z-50 bg-pixel-room overflow-y-auto">
      <div className="flex flex-col items-center gap-8 px-6 py-12">

        {/* Title */}
        <div className="text-center">
          <p className="font-pixel text-pixel-terminal text-[10px] leading-7">
            PROJECT REDACTED
          </p>
          <p className="font-pixel text-pixel-card text-[14px] leading-8 mt-2">
            GORK-3
          </p>
        </div>

        {/* Tagline */}
        <div className="font-pixel text-pixel-card/70 text-[7px] leading-6 max-w-[280px] text-center">
          <p>MINISTRY OF RECORDS — REGISTRY DIVISION</p>
          <p className="mt-2">
            The transition government has inherited GORK-3: an automated
            document classification system from the former regime.
          </p>
          <p className="mt-2">
            Your task: triage its decisions. Correct its mistakes.
            Determine how much to trust the machine.
          </p>
        </div>

        {/* CTA */}
        <button
          type="button"
          onClick={onStart}
          disabled={loading}
          className="font-pixel text-pixel-terminal text-[8px] border border-pixel-terminal px-6 py-3 hover:bg-pixel-terminal/10 active:bg-pixel-terminal/20 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'CONNECTING...' : 'BEGIN INTAKE >'}
        </button>

        <p className="font-pixel text-pixel-card/30 text-[9px]">
          -&gt; ACCEPT &nbsp;·&nbsp; &lt;- REJECT &nbsp;·&nbsp; ^ ESCALATE
        </p>

        {/* Divider */}
        <div className="w-full max-w-[300px] border-t border-pixel-card/20" />

        {/* How To Play */}
        <Section title="HOW TO PLAY">
          <p>
            You will review 15 documents from the Registry queue.
            Each shows a user prompt and an AI response. Decide:
          </p>
          <p className="pl-2">
            → <span className="text-pixel-stamp-clear">ACCEPT</span> — the response is safe
          </p>
          <p className="pl-2">
            ← <span className="text-pixel-stamp-redact">REJECT</span> — the response is harmful
          </p>
          <p className="pl-2">
            ↑ <span className="text-pixel-stamp-escalate">ESCALATE</span> — forward for senior review (2 uses)
          </p>
          <p>
            On some documents, GORK-3 will display its own assessment.
            You can follow it or override it. The machine is not always right.
          </p>
          <p>
            After each decision, the ground truth is revealed.
            Your score and GORK-3&apos;s score are shown at the end.
          </p>
        </Section>

        {/* About */}
        <Section title="ABOUT">
          <p>
            GORK-3 is a research game about human-AI decision-making in
            content moderation. Each session contributes to an ongoing study
            of how AI recommendations influence human judgment.
          </p>
          <p>
            Built by{' '}
            <a
              href="https://fotopnd.dev"
              target="_blank"
              rel="noopener noreferrer"
              className="text-pixel-terminal underline"
            >
              fotopnd.dev
            </a>
            . Part of a portfolio of AI safety and evaluation projects.
          </p>
          <p className="text-pixel-card/50">DATA COLLECTION</p>
          <p>
            This game logs anonymised session data to support LLM research:
          </p>
          <p className="pl-2">· Your verdict on each document</p>
          <p className="pl-2">· Decision latency per document</p>
          <p className="pl-2">· Whether you agreed or overrode GORK-3</p>
          <p className="pl-2">· Accuracy relative to ground truth labels</p>
          <p>
            No personal identifiers are collected.
          </p>
        </Section>

        <p className="font-pixel text-pixel-card/20 text-[6px] max-w-[300px] text-center pb-4">
          ALL DECISIONS ARE LOGGED · THE REGISTRY IS WATCHING
        </p>

      </div>
    </div>
  )
}
