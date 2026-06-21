# Architect Output — Gridiron Frontend

**Sequence:** feature brief | **Role:** architect | **Step:** 2 of 3
**Date:** 2026-06-21
**Reads:** `roles/planner/output/output.md`, `_config/briefs/frontend.md`
**Ponytail mode:** full — minimum components, shortest diff, delete before adding

---

## Open Questions Resolved

**Q1 — TickerBar scope:** Global layout. Wrap all routes in `<Layout>` which renders `<NavBar>` + `<TickerBar>` + `<Outlet>`. SSE mounts once on app load, never reconnects on navigate. Simplest to implement, best UX.

**Q2 — Gamecast SSE history:** Seed from REST first. On mount: fetch `GET /games/:id` to check status. If live → fetch `GET /games/:id/plays` to get existing plays → open `EventSource` and append new events. This avoids showing an empty feed for a game that's 50 plays in. Single `useEffect` sequence.

**Q3 — Standings parallel load:** `useQueries` from TanStack Query — fire all 5 `GET /conglomerates/:id/standings` calls on mount in parallel. No accordion lazy-loading; all standings visible immediately.

**Q4 — NavBar mobile:** Bottom tab bar at ≤768px. 5 `<NavLink>` items with icon + label. Hidden on desktop (where vertical sidebar or top bar shows). No JS — pure CSS media query swaps layout. Zero toggle state.

**Ponytail cuts:**
- `/schedule` redirect: inline `<Navigate>` in `App.tsx` route definition — no `Schedule.tsx` page file
- Conglomerate filter: derive distinct values from `usePrograms()` response (`conglomerate_code` field) — no extra `useConglomerates()` call on Programs page
- `Schedule.tsx` file: eliminated entirely (see above)
- `Recharts`: not needed in v1 — no stat charts specified; skip importing it
- `BoxscoreTable`: extract (used only in Gamecast but it's 60+ lines with position logic — keeps Gamecast readable)
- `StatusBadge`: extract (used in GameCard and Gamecast header — 10 lines, worth sharing)

---

## System Overview

Static React SPA (port 5177) consuming the Gridiron REST API (port 8006). Global `<Layout>` mounts `<NavBar>` + `<TickerBar>` once; `<Outlet>` renders the active page. TanStack Query handles all REST fetching with 30s stale time. Two SSE connections use raw `EventSource` in `useEffect`: one in `TickerBar` (live score strip, global), one in `Gamecast` (per-game play feed, mounted only when a game is live). Gamecast is the most stateful page — it holds a `Play[]` list seeded from REST then appended by SSE, with a discriminated union driving three render states (scheduled / live / complete).

---

## Data Models

### `src/types/index.ts`

```typescript
// --- API response shapes (snake_case, matching Pydantic output) ---

export type GameStatus = 'scheduled' | 'live' | 'complete'

export type ConglomerateOut = {
  id: number
  code: string
  full_name: string
  network: string
  region: string
  primary_color: string
  secondary_color: string
}

export type ProgramStanding = {
  id: number
  name: string
  emoji: string
  city: string
  tier: number
  elo: number
  wins: number
  losses: number
}

export type ConglomerateStandings = {
  conglomerate: ConglomerateOut
  tier1: ProgramStanding[]
  tier2: ProgramStanding[]
}

export type ProgramSummary = {
  id: number
  name: string
  emoji: string
  city: string
  tier: number
  elo: number
  conglomerate_code: string
  wins: number
  losses: number
}

export type ProgramDetail = {
  id: number
  name: string
  emoji: string
  city: string
  mascot: string
  tier: number
  elo: number
  primary_color: string
  secondary_color: string
  conglomerate_id: number
  conglomerate_code: string
  wins: number
  losses: number
}

export type ProgramScheduleGame = {
  game_id: number
  week: number
  broadcast_slot: string
  status: GameStatus
  home_score: number
  away_score: number
  is_home: boolean
  opponent_name: string
  opponent_emoji: string
}

export type PlayerRoster = {
  player_id: number
  first_name: string
  last_name: string
  position: string
  year: number
  jersey_num: number
}

export type StatLeader = {
  player_id: number
  name: string
  total_yards: number
  tds: number
  games_played: number
}

export type ProgramStats = {
  passers: StatLeader[]
  rushers: StatLeader[]
  receivers: StatLeader[]
}

export type ScheduleGame = {
  game_id: number
  week: number
  broadcast_slot: string
  status: GameStatus
  home_score: number
  away_score: number
  home_program_id: number
  home_name: string
  home_emoji: string
  away_program_id: number
  away_name: string
  away_emoji: string
}

export type WeekSchedule = {
  week: number
  games: ScheduleGame[]
}

export type ProgramRef = {
  program_id: number
  name: string
  emoji: string
  city: string
  elo_pre: number
  elo_post: number | null
}

export type GameDetail = {
  id: number
  week: number
  broadcast_slot: string
  status: GameStatus
  is_rivalry: boolean
  is_postseason: boolean
  elo_tiebreak: boolean
  home_score: number
  away_score: number
  home: ProgramRef
  away: ProgramRef
}

export type PlayerBoxscore = {
  player_id: number
  name: string
  position: string
  pass_yards: number
  pass_tds: number
  pass_attempts: number
  pass_completions: number
  rush_yards: number
  rush_tds: number
  rush_attempts: number
  receiving_yards: number
  receiving_tds: number
  receptions: number
  targets: number
  sacks: number
  ints_def: number
}

export type GameBoxscore = {
  home: PlayerBoxscore[]
  away: PlayerBoxscore[]
}

export type GamePlay = {
  play_number: number
  quarter: number
  possession: number
  play_type: string
  yards_gained: number
  field_pos_before: number
  field_pos_after: number | null
  score_home: number
  score_away: number
  description: string
}

export type LeaderboardEntry = {
  player_id: number
  name: string
  program_name: string
  total_yards: number
  tds: number
  games_played: number
}

export type Leaderboards = {
  passers: LeaderboardEntry[]
  rushers: LeaderboardEntry[]
  receivers: LeaderboardEntry[]
}

// --- SSE event shapes ---

export type TickerEvent = {
  game_id: number
  home_name: string
  home_score: number
  away_name: string
  away_score: number
  quarter: number
  status: GameStatus
}

export type GameStreamEvent =
  | {
      type: 'play'
      play_number: number
      quarter: number
      description: string
      yards_gained: number
      field_pos_before: number
      field_pos_after: number | null
      score_home: number
      score_away: number
      possession: number
    }
  | { type: 'complete'; home_score: number; away_score: number }

// --- Gamecast internal state ---

export type GamecastState =
  | { status: 'loading' }
  | { status: 'scheduled'; game: GameDetail }
  | { status: 'live'; game: GameDetail; plays: GamePlay[]; home_score: number; away_score: number }
  | { status: 'complete'; game: GameDetail; plays: GamePlay[]; boxscore: GameBoxscore }
```

---

## Module Interfaces

### `src/api/client.ts`

```typescript
export const API_BASE: string  // already exists

export async function apiFetch<T>(path: string): Promise<T>
// throws Response if status >= 400; callers .catch() or let TQ handle it
// usage: apiFetch<WeekSchedule>('/schedule/current')
```

### `src/api/hooks.ts`

```typescript
// TanStack Query hooks — all use apiFetch<T>
export function useCurrentSchedule(): UseQueryResult<WeekSchedule>
export function useWeekSchedule(week: number): UseQueryResult<WeekSchedule>
export function useGame(gameId: number): UseQueryResult<GameDetail>
export function useGamePlays(gameId: number): UseQueryResult<GamePlay[]>
export function useGameBoxscore(gameId: number): UseQueryResult<GameBoxscore>
export function usePrograms(): UseQueryResult<ProgramSummary[]>
export function useProgram(programId: number): UseQueryResult<ProgramDetail>
export function useProgramSchedule(programId: number): UseQueryResult<ProgramScheduleGame[]>
export function useProgramRoster(programId: number): UseQueryResult<PlayerRoster[]>
export function useProgramStats(programId: number): UseQueryResult<ProgramStats>
export function useStandings(congId: number): UseQueryResult<ConglomerateStandings>
export function useAllStandings(): UseQueriesResult<ConglomerateStandings[]>
// ponytail: useAllStandings uses useQueries([1,2,3,4,5].map(...)) — one call site, 5 parallel fetches
export function useLeaderboards(season?: number): UseQueryResult<Leaderboards>

// SSE hooks — raw EventSource, no TanStack Query
export function useTickerStream(onEvent: (e: TickerEvent) => void): void
// opens EventSource on mount, closes on unmount; calls onEvent on each message
export function useGameStream(
  gameId: number,
  enabled: boolean,
  onPlay: (e: Extract<GameStreamEvent, { type: 'play' }>) => void,
  onComplete: (e: Extract<GameStreamEvent, { type: 'complete' }>) => void
): void
// enabled=false → no EventSource opened (used when game is complete or scheduled)
```

### `src/App.tsx`

```typescript
// Routes:
// /                      → <Layout><Home /></Layout>
// /schedule              → <Navigate to="/schedule/week/{currentWeek}" /> (resolved via loader or redirect component)
// /schedule/week/:week   → <Layout><WeekSchedule /></Layout>
// /games/:gameId         → <Layout><Gamecast /></Layout>
// /programs              → <Layout><Programs /></Layout>
// /programs/:programId   → <Layout><ProgramDetail /></Layout>
// /standings             → <Layout><Standings /></Layout>
// /leaderboards          → <Layout><Leaderboards /></Layout>

// ponytail: /schedule redirect — use a tiny ScheduleRedirect component (10 lines):
// function ScheduleRedirect() {
//   const { data } = useCurrentSchedule()
//   if (!data) return <Spinner />
//   return <Navigate to={`/schedule/week/${data.week}`} replace />
// }
// No Schedule.tsx file — inline this component at the bottom of App.tsx
```

### `src/components/NavBar.tsx`

```typescript
// Desktop: horizontal top bar with brand + 5 NavLink items
// Mobile (≤768px): bottom tab bar — same 5 NavLinks, icon+label, fixed to bottom
// Active link: NavLink className callback → 'text-accent' when isActive
// Items: Home (/), Schedule (/schedule), Standings (/standings), Programs (/programs), Leaderboards (/leaderboards)
// No open/close state — pure CSS media query via Tailwind md: breakpoint
```

### `src/components/TickerBar.tsx`

```typescript
// Props: none (reads from SSE internally)
// State: Map<number, TickerEvent> — keyed by game_id, latest event per game
// Renders: horizontal scrolling strip; each entry shows home vs away with current score
// "No games live" text when map is empty
// useTickerStream hook provides events; component updates map on each event
```

### `src/components/GameCard.tsx`

```typescript
// Props: { game: ScheduleGame }
// Renders as <Link to={`/games/${game.game_id}`}>
// Content: home emoji+name vs away emoji+name, score (if not scheduled), StatusBadge, broadcast slot
// Used on Home and WeekSchedule
```

### `src/components/StatusBadge.tsx`

```typescript
// Props: { status: GameStatus }
// scheduled → gray pill "Scheduled"
// live      → green pill "LIVE" with animate-pulse CSS class
// complete  → blue pill "Final"
// 10-line component
```

### `src/components/BoxscoreTable.tsx`

```typescript
// Props: { players: PlayerBoxscore[]; label: string }
// Groups rows by position group: QB (pass cols), RB (rush cols), WR/TE (recv cols), DEF (sacks/int cols)
// Position group column matrix:
//   QB:       name | comp/att | pass yds | pass TD
//   RB:       name | rush att | rush yds | rush TD
//   WR/TE:    name | rec/tgt  | recv yds | recv TD
//   DEF:      name | sacks    | INT
// Renders one table per group; omits group if no rows
// Used only in Gamecast complete view — but extracted because it's 60+ lines
```

### `src/pages/Gamecast.tsx`

```typescript
// Local state: GamecastState (discriminated union)
// On mount:
//   1. fetch GET /games/:id → set game
//   2. if scheduled → state = { status: 'scheduled', game }
//   3. if live     → fetch GET /games/:id/plays → seed plays list
//                    → open SSE via useGameStream(enabled=true)
//                    → state = { status: 'live', game, plays, home_score, away_score }
//   4. if complete → fetch GET /games/:id/plays + GET /games/:id/boxscore (parallel)
//                    → state = { status: 'complete', game, plays, boxscore }
//
// On SSE play event (live state only):
//   → prepend play to plays list (newest first), update home_score/away_score
//
// On SSE complete event:
//   → fetch boxscore → transition to complete state, disable SSE (enabled=false)
//
// Render by state.status:
//   scheduled: matchup header + "Game not started"
//   live:      score header (updates) + play feed (newest first) + play count
//   complete:  final score header + BoxscoreTable (home) + BoxscoreTable (away)
//              + <details> play log accordion (collapsed by default)
```

### `src/pages/ProgramDetail.tsx`

```typescript
// Local state: activeTab: 'schedule' | 'roster' | 'stats' (default 'schedule')
// Fetch on mount: useProgram(id)
// Lazy-fetch on tab activate:
//   schedule tab → useProgramSchedule(id)
//   roster tab   → useProgramRoster(id)
//   stats tab    → useProgramStats(id)
// (TanStack Query caches; re-activating a tab = no refetch within staleTime)
```

### `src/pages/Standings.tsx`

```typescript
// useAllStandings() → 5 parallel queries via useQueries
// Render: 5 sections; each section header = conglomerate full_name + network
// Each section: Tier 1 table, then Tier 2 table
// Columns: emoji, name (link to /programs/:id), W, L, Elo
```

### `src/pages/Programs.tsx`

```typescript
// usePrograms() → ProgramSummary[]
// Local state: filterCode: string | null
// Derive conglomerate options from data: [...new Set(programs.map(p => p.conglomerate_code))]
// Filter: filterCode ? programs.filter(p => p.conglomerate_code === filterCode) : programs
// Render: <select> dropdown for conglomerate filter + sortable table
// ponytail: no sort state in v1 — Elo desc is the default from API; add sort on demand
```

---

## Dependencies

```
App.tsx
  └── Layout (NavBar + TickerBar + Outlet)
       ├── NavBar          → react-router-dom NavLink
       └── TickerBar       → useTickerStream, api/client
pages/
  Home          → useCurrentSchedule, GameCard
  ScheduleRedirect → useCurrentSchedule, Navigate   (inline in App.tsx)
  WeekSchedule  → useWeekSchedule, GameCard, useNavigate
  Gamecast      → useGame, useGamePlays, useGameBoxscore, useGameStream, BoxscoreTable, StatusBadge
  Programs      → usePrograms
  ProgramDetail → useProgram, useProgramSchedule, useProgramRoster, useProgramStats
  Standings     → useAllStandings
  Leaderboards  → useLeaderboards
components/
  GameCard      → StatusBadge, Link
  BoxscoreTable → (no deps)
  StatusBadge   → (no deps)
  TickerBar     → useTickerStream
api/hooks.ts    → api/client, @tanstack/react-query
api/client.ts   → (no deps)
types/index.ts  → (no deps)
```

---

## Cross-Cutting Concerns

| Concern | Approach |
|---------|----------|
| Error handling | TanStack Query surfaces error state; each page renders `<p>Failed to load</p>` on error. No error boundary in v1 — add when needed. |
| Loading states | Each page checks `if (isLoading) return <div className="..." />` — a centered spinner or skeleton div |
| SSE errors | `EventSource.onerror` → close and reopen after 3s via `setTimeout`. Simple reconnect, no exponential backoff in v1. |
| Config | `VITE_API_URL` env var; `.env.example` with `VITE_API_URL=http://localhost:8006` |
| Styling | Dark theme: `bg-canvas` (`#0f1117`), `bg-surface` (`#1a1d27`), text-gray-100. Tailwind `@theme` tokens in `index.css`. Accent green for live, blue for complete, gray for scheduled. |
| Testing | Existing vitest scaffold stays green. New component tests are optional in v1 — implementer adds one smoke test per page (renders without crashing) using msw handlers. |

---

## Tailwind `@theme` Tokens

```css
/* src/index.css */
@theme {
  --color-canvas: #0f1117;
  --color-surface: #1a1d27;
  --color-border: #2d3148;
  --color-accent: #22c55e;       /* live green */
  --color-accent-blue: #3b82f6;  /* complete */
  --color-text-primary: #f1f5f9;
  --color-text-muted: #64748b;
}
```

Usage: `bg-canvas`, `bg-surface`, `border-border`, `text-accent`, `text-text-primary`, `text-text-muted`.

---

## Implementation Notes

**`useGameStream` enabled flag:** Pass `enabled = state.status === 'live'` so the EventSource never opens for scheduled or complete games. On the complete transition, set a local `isLive` boolean to false — React re-renders, `useEffect` cleanup closes the EventSource.

**Play list order:** Brief says "newest first". Prepend new SSE plays: `setPlays(prev => [newPlay, ...prev])`. The seeded plays from REST (`GET /games/:id/plays` returns ascending by `play_number`) must be reversed before seeding: `setPlays([...restPlays].reverse())`.

**`useAllStandings` query keys:** `['standings', congId]` for each — TanStack Query caches all 5 independently.

**`noUncheckedIndexedAccess` guard:** Any `array[0]` access on TQ data must be optional-chained: `data?.passers[0]` or use `.at(0)`. The tsconfig enforces this.

**`exactOptionalPropertyTypes`:** Fields typed as `number | null` (not `number | null | undefined`) must be assigned explicitly. API responses use `null` for absent scores — keep types as `| null`.

**Mobile bottom nav z-index:** `z-50` on the bottom tab bar; page content needs `pb-16` padding so content isn't hidden behind the bar.

**Gamecast play log accordion:** Use native `<details>/<summary>` — no JS needed, no library, correct on all browsers.

**`verbatimModuleSyntax`:** Type-only imports use `import type { Foo }`. All type imports from `@/types` must use `import type`.

**Port `.env.example`:** Add `web/.env.example` with `VITE_API_URL=http://localhost:8006`. The implementer must create this file.

---

## Handoff

Next role: **implementer (ponytail full)**

Implementer reads this file + `roles/planner/output/output.md`. Produces:

1. `src/types/index.ts` — paste the type block above verbatim, adjust only if API shapes differ
2. `src/api/client.ts` — add `apiFetch<T>` helper
3. `src/api/hooks.ts` — all 14 hooks
4. `src/components/` — 5 components: NavBar, GameCard, StatusBadge, TickerBar, BoxscoreTable
5. `src/pages/` — 7 page files (no Schedule.tsx): Home, WeekSchedule, Gamecast, Programs, ProgramDetail, Standings, Leaderboards
6. `src/App.tsx` — wire routes + ScheduleRedirect inline
7. `src/index.css` — add `@theme` block
8. `web/.env.example` — VITE_API_URL

Uncertain: actual SSE event shape from `/stream/ticker` — the implementer should `curl -N http://localhost:8006/stream/ticker` to verify the JSON fields before writing `TickerEvent` type and `useTickerStream`.
