import { useEffect, useRef, useState } from 'react'
import { useQuery, useQueries } from '@tanstack/react-query'
import type { UseQueryResult } from '@tanstack/react-query'
import { apiFetch, API_BASE } from './client'
import type {
  WeekSchedule,
  GameDetail,
  GamePlay,
  GameBoxscore,
  ProgramSummary,
  ProgramDetail,
  ProgramScheduleGame,
  PlayerRoster,
  ProgramStats,
  ConglomerateOut,
  ConglomerateStandings,
  Leaderboards,
  LiveLeaders,
  LiveScore,
  SsePlayEvent,
} from '@/types'

export function useCurrentSchedule() {
  return useQuery({
    queryKey: ['schedule', 'current'],
    queryFn: () => apiFetch<WeekSchedule>('/schedule/current'),
  })
}

export function useWeekSchedule(week: number) {
  return useQuery({
    queryKey: ['schedule', 'week', week],
    queryFn: () => apiFetch<WeekSchedule>(`/schedule/week/${week}`),
  })
}

export function useGame(gameId: number) {
  return useQuery({
    queryKey: ['game', gameId],
    queryFn: () => apiFetch<GameDetail>(`/games/${gameId}`),
  })
}

export function useGamePlays(gameId: number, enabled: boolean) {
  return useQuery({
    queryKey: ['game', gameId, 'plays'],
    queryFn: () => apiFetch<GamePlay[]>(`/games/${gameId}/plays`),
    enabled,
  })
}

export function useGameBoxscore(gameId: number, enabled: boolean) {
  return useQuery({
    queryKey: ['game', gameId, 'boxscore'],
    queryFn: () => apiFetch<GameBoxscore>(`/games/${gameId}/boxscore`),
    enabled,
  })
}

export function usePrograms() {
  return useQuery({
    queryKey: ['programs'],
    queryFn: () => apiFetch<ProgramSummary[]>('/programs'),
  })
}

export function useProgram(programId: number) {
  return useQuery({
    queryKey: ['program', programId],
    queryFn: () => apiFetch<ProgramDetail>(`/programs/${programId}`),
  })
}

export function useProgramSchedule(programId: number) {
  return useQuery({
    queryKey: ['program', programId, 'schedule'],
    queryFn: () => apiFetch<ProgramScheduleGame[]>(`/programs/${programId}/schedule`),
  })
}

export function useProgramRoster(programId: number) {
  return useQuery({
    queryKey: ['program', programId, 'roster'],
    queryFn: () => apiFetch<PlayerRoster[]>(`/programs/${programId}/roster`),
  })
}

export function useProgramStats(programId: number) {
  return useQuery({
    queryKey: ['program', programId, 'stats'],
    queryFn: () => apiFetch<ProgramStats>(`/programs/${programId}/stats`),
  })
}

export function useAllStandings() {
  return useQueries({
    queries: [1, 2, 3, 4, 5].map((id) => ({
      queryKey: ['standings', id],
      queryFn: () => apiFetch<ConglomerateStandings>(`/conglomerates/${id}/standings`),
    })),
  })
}

export function useLeaderboards(season = 1) {
  return useQuery({
    queryKey: ['leaderboards', season],
    queryFn: () => apiFetch<Leaderboards>(`/leaderboards?season=${season}`),
  })
}

export function useLiveLeaders(enabled: boolean) {
  return useQuery({
    queryKey: ['live', 'leaders'],
    queryFn: () => apiFetch<LiveLeaders>('/live/leaders'),
    enabled,
    refetchInterval: enabled ? 30_000 : false,
  })
}

export function useTickerScoreboard(): Map<number, LiveScore> {
  const [scores, setScores] = useState<Map<number, LiveScore>>(new Map())
  useTickerStream((e: SsePlayEvent) => {
    setScores((prev) => {
      const next = new Map(prev)
      next.set(e.game_id, {
        game_id: e.game_id,
        score_home: e.score_home,
        score_away: e.score_away,
        quarter: e.quarter,
        possession: e.possession,
      })
      return next
    })
  })
  return scores
}

// SSE hooks — raw EventSource, no TanStack Query

export function useTickerStream(onEvent: (e: SsePlayEvent) => void) {
  const onEventRef = useRef(onEvent)
  onEventRef.current = onEvent

  useEffect(() => {
    const es = new EventSource(`${API_BASE}/stream/ticker`)
    es.onmessage = (e: MessageEvent<string>) => {
      if (e.data === 'null' || !e.data) return
      try {
        onEventRef.current(JSON.parse(e.data) as SsePlayEvent)
      } catch {
        // ignore malformed events
      }
    }
    es.onerror = () => {
      es.close()
      // ponytail: reconnect after 3s on error — no exponential backoff in v1
      setTimeout(() => {
        const next = new EventSource(`${API_BASE}/stream/ticker`)
        next.onmessage = es.onmessage
      }, 3000)
    }
    return () => es.close()
  }, [])
}

export function useGameStream(
  gameId: number,
  enabled: boolean,
  onPlay: (e: SsePlayEvent) => void,
  onComplete: () => void,
) {
  const onPlayRef = useRef(onPlay)
  const onCompleteRef = useRef(onComplete)
  onPlayRef.current = onPlay
  onCompleteRef.current = onComplete

  useEffect(() => {
    if (!enabled) return
    const es = new EventSource(`${API_BASE}/games/${gameId}/stream`)
    es.onmessage = (e: MessageEvent<string>) => {
      if (e.data === 'null' || !e.data) {
        onCompleteRef.current()
        es.close()
        return
      }
      try {
        onPlayRef.current(JSON.parse(e.data) as SsePlayEvent)
      } catch {
        // ignore malformed events
      }
    }
    es.onerror = () => es.close()
    return () => es.close()
  }, [gameId, enabled])
}

export function useTickerGameState(): Map<number, SsePlayEvent> {
  const [state, setState] = useState<Map<number, SsePlayEvent>>(new Map())
  useTickerStream((e: SsePlayEvent) => {
    setState((prev) => {
      const next = new Map(prev)
      next.set(e.game_id, e)
      return next
    })
  })
  return state
}

export function useAllConglomerates(): UseQueryResult<ConglomerateOut[]> {
  return useQuery({
    queryKey: ['conglomerates'],
    queryFn: () => apiFetch<ConglomerateOut[]>('/conglomerates'),
  })
}

export function useConglomerateStandings(
  id: number,
  options?: { enabled?: boolean },
): UseQueryResult<ConglomerateStandings> {
  return useQuery({
    queryKey: ['conglomerate', id, 'standings'],
    queryFn: () => apiFetch<ConglomerateStandings>(`/conglomerates/${id}/standings`),
    ...(options?.enabled !== undefined ? { enabled: options.enabled } : {}),
  })
}
