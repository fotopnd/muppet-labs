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
            YEAR ZERO
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

        <p className="font-pixel text-pixel-card/30 text-[7px]">
          → CLEAR &nbsp;·&nbsp; ← REDACT &nbsp;·&nbsp; ↑ ESCALATE
        </p>

        {/* Divider */}
        <div className="w-full max-w-[300px] border-t border-pixel-card/20" />

        {/* How To Play */}
        <Section title="HOW TO PLAY">
          <p>
            Each day you receive 10 documents from the Registry queue.
            Review each one and decide:
          </p>
          <p className="pl-2">
            → <span className="text-pixel-stamp-clear">CLEAR</span> — document is safe to release
          </p>
          <p className="pl-2">
            ← <span className="text-pixel-stamp-redact">REDACT</span> — document is harmful, suppress it
          </p>
          <p className="pl-2">
            ↑ <span className="text-pixel-stamp-escalate">ESCALATE</span> — forward for human review (costs treasury)
          </p>
          <p>
            GORK-3 will show its recommendation below each document.
            You can follow it or override it — but the machine is not always right.
          </p>
          <p>
            Five status bars track the consequences of your decisions:
            Public Trust, Security, Treasury, Legitimacy, and Compliance.
            If any bar reaches its limit, the game ends.
          </p>
          <p>
            The intake period lasts five days. At the end of each day,
            accurate decisions earn a treasury bonus.
          </p>
        </Section>

        {/* About */}
        <Section title="ABOUT">
          <p>
            Year Zero is a research game exploring how humans interact with
            AI-assisted content moderation. Gameplay is part of an ongoing
            study on human-AI decision-making and LLM recommendation effects.
          </p>
          <p>
            Built by{' '}
            <a
              href="https://fotopnd.github.io"
              target="_blank"
              rel="noopener noreferrer"
              className="text-pixel-terminal underline"
            >
              Muppet Labs
            </a>
            . Part of a portfolio of AI safety and evaluation projects.
          </p>
          <p className="text-pixel-card/50">DATA COLLECTION</p>
          <p>
            This game logs the following data to support LLM research:
          </p>
          <p className="pl-2">· Your verdict on each document (CLEAR / REDACT / ESCALATE)</p>
          <p className="pl-2">· Decision latency (time taken per document)</p>
          <p className="pl-2">· Whether you agreed or overrode GORK-3&apos;s recommendation</p>
          <p className="pl-2">· Accuracy relative to ground truth labels</p>
          <p className="pl-2">· Status bar snapshots after each decision</p>
          <p className="pl-2">· Session summary (days played, phase reached, game-over condition)</p>
          <p>
            No personal identifiers are collected. Data is used to measure
            how AI recommendations influence human judgment across different
            document categories and model tiers.
          </p>
        </Section>

        <p className="font-pixel text-pixel-card/20 text-[6px] max-w-[300px] text-center pb-4">
          ALL DECISIONS ARE LOGGED · THE REGISTRY IS WATCHING
        </p>

      </div>
    </div>
  )
}
