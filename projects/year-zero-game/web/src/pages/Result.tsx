import { useParams, Link } from 'react-router-dom'
import { useSessionResult } from '../api/hooks'

function StatRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between border-b border-pixel-card/10 py-1">
      <span className="text-pixel-card/60">{label}</span>
      <span className="text-pixel-card">{value}</span>
    </div>
  )
}

export default function Result() {
  const { shareId } = useParams<{ shareId: string }>()
  const { data, isLoading, isError } = useSessionResult(shareId ?? null)

  return (
    <div className="w-full min-h-svh bg-pixel-room flex flex-col items-center justify-center px-6 py-12">
      <div className="w-full max-w-[340px] flex flex-col gap-6">

        <div className="text-center">
          <p className="font-pixel text-pixel-terminal text-[8px]">PROJECT REDACTED</p>
          <p className="font-pixel text-pixel-card text-[12px] mt-1">GORK-3</p>
          <p className="font-pixel text-pixel-card/40 text-[7px] mt-2">REGISTRY RECORD</p>
        </div>

        {isLoading && (
          <p className="font-pixel text-pixel-terminal text-[8px] text-center">
            RETRIEVING RECORD...
          </p>
        )}

        {isError && (
          <div className="font-pixel text-pixel-card/60 text-[7px] text-center space-y-3">
            <p>RECORD NOT FOUND</p>
            <p className="opacity-60">
              This record may not exist, or the session did not complete.
            </p>
          </div>
        )}

        {data && (
          <>
            <div className="border border-pixel-card/20 px-4 py-4 space-y-1">
              <p className="font-pixel text-pixel-terminal text-[7px] mb-3">
                RECORD ID: {data.share_id}
              </p>
              <div className="font-pixel text-[8px] space-y-0">
                <StatRow label="DAYS SERVED" value={String(data.total_days ?? '—')} />
                <StatRow label="DECISIONS" value={String(data.total_decisions ?? '—')} />
                <StatRow
                  label="ACCURACY"
                  value={data.accuracy != null ? `${Math.round(data.accuracy * 100)}%` : '—'}
                />
                <StatRow
                  label="ESCALATED"
                  value={String(data.total_escalated ?? '—')}
                />
                <StatRow
                  label="AGREEMENT RATE"
                  value={data.agreement_rate != null ? `${Math.round(data.agreement_rate * 100)}%` : '—'}
                />
                <StatRow
                  label="CALIB. ACCURACY"
                  value={data.calibration_accuracy != null ? `${Math.round(data.calibration_accuracy * 100)}%` : '—'}
                />
                <StatRow
                  label="PHASE REACHED"
                  value={String(data.phase_reached ?? '—')}
                />
                <StatRow
                  label="CONDITION"
                  value={(data.game_over_condition ?? '').replace(/_/g, ' ')}
                />
              </div>
            </div>

            {data.game_over_condition && (
              <p className="font-pixel text-pixel-card/60 text-[7px] leading-6 text-center">
                {data.game_over_condition.replace(/_/g, ' ')}
              </p>
            )}
          </>
        )}

        <div className="flex flex-col items-center gap-3">
          <Link
            to="/"
            className="font-pixel text-pixel-terminal text-[8px] border border-pixel-terminal px-6 py-2 hover:bg-pixel-terminal/10 text-center"
          >
            PLAY GORK-3 &gt;
          </Link>
          <p className="font-pixel text-pixel-card/30 text-[6px]">
            ALL DECISIONS ARE LOGGED · THE REGISTRY IS WATCHING
          </p>
        </div>

      </div>
    </div>
  )
}
