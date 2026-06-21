import { useEffect, useRef } from 'react'
import { useQuery, useQueries } from '@tanstack/react-query'
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
  ConglomerateStandings,
  Leaderboards,
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
