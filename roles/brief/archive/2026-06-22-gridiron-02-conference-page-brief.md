## Project Name
gridiron

## Description
Create a new conference landing page at `web/src/pages/ConferencePage.tsx`. Each of the 5 NAFCA conferences gets its own page at `/conference/:code`, styled in the conference's brand colours. The page shows live scoreboards (using `ScoreboardWidget`) and upcoming/recent game cards split by tier (Tier 1 / Tier 2), filtered to only games involving teams from that conference.

## Language(s)
TypeScript / React / Tailwind

## Background / Current State

The conference data API (`GET /conglomerates`, `GET /conglomerates/{id}/standings`) is fully implemented. The standings endpoint returns `{ conglomerate: ConglomerateOut, tier1: ProgramStanding[], tier2: ProgramStanding[] }`. `ConglomerateOut` has `id, code, full_name, network, region, primary_color, secondary_color` (colors are CSS hex strings e.g. `#3B82F6`).

**New hooks available (from unit 01a — these will be merged before this unit runs):**
- `useTickerGameState(): Map<number, SsePlayEvent>` — full last SSE event per game_id
- `useAllConglomerates(): UseQueryResult<ConglomerateOut[]>`
- `useConglomerateStandings(id, { enabled }): UseQueryResult<ConglomerateStandings>`

**New component available (from unit 01b — merged before this unit runs):**
- `ScoreboardWidget` from `@/components/ScoreboardWidget` — takes `game: ScheduleGame` + `liveState?: SsePlayEvent`

**Existing hooks available:**
- `useCurrentSchedule()` — returns `WeekSchedule` (`{ week, games: ScheduleGame[] }`)
- `useWeekSchedule(week)` — same but for a specific week

**Existing component available:**
- `GameCard` from `@/components/GameCard` — takes `game, liveScore?, revealed?, onReveal?`
- `useTickerScoreboard()` — `Map<gameId, LiveScore>` (for GameCard `liveScore` prop)

## Success Criteria

**Route:** `/conference/:code`

**Data loading:**
```ts
const { code } = useParams<{ code: string }>()
const { data: allConglomerates } = useAllConglomerates()
const conglomerate = allConglomerates?.find(c => c.code === code)
const { data: standings } = useConglomerateStandings(conglomerate?.id ?? 0, { enabled: !!conglomerate })
const { data: schedule } = useCurrentSchedule()
const tickerState = useTickerGameState()
const scoreboard = useTickerScoreboard()   // for GameCard liveScore prop
const [revealedGames, setRevealedGames] = useState<Set<number>>(new Set())
```

**Conference game filtering (client-side — no backend change needed):**
```ts
const tier1Ids = new Set(standings?.tier1.map(p => p.id) ?? [])
const tier2Ids = new Set(standings?.tier2.map(p => p.id) ?? [])
const allIds = new Set([...tier1Ids, ...tier2Ids])

const conferenceGames = schedule?.games.filter(
  g => allIds.has(g.home_program_id) || allIds.has(g.away_program_id)
) ?? []

// A game is Tier 1 if either team is Tier 1; otherwise Tier 2
function gameTier(g: ScheduleGame): 1 | 2 {
  return tier1Ids.has(g.home_program_id) || tier1Ids.has(g.away_program_id) ? 1 : 2
}

const tier1Games = conferenceGames.filter(g => gameTier(g) === 1)
const tier2Games = conferenceGames.filter(g => gameTier(g) === 2)
```

**Page layout (from top to bottom):**

1. **Conference header bar** (full-width, coloured background):
   ```
   [primary_color background, secondary_color text or white]
   NAFCA · {code}
   {full_name}
   {network} · {region}
   ```
   Use inline `style={{ backgroundColor: conglomerate.primary_color, color: conglomerate.secondary_color }}` on the header div. If the secondary color is too light/dark to read, fall back to white — check luminance or just always use white text and only background in primary.

2. **Tier 1 section** (`## TIER 1` heading):
   - **Live subsection** (only when any tier1Games are live):
     `ScoreboardWidget` grid for each `g.status === 'live'` tier1 game
     Pass `liveState={tickerState.get(g.game_id)}`
   - **Schedule subsection** (upcoming + complete):
     `GameCard` grid for non-live tier1 games
     Pass `liveScore={scoreboard.get(g.game_id)}` (always undefined for non-live, but consistent)
     Pass `revealed={g.status !== 'complete' || revealedGames.has(g.game_id)}`
     Pass `onReveal={() => setRevealedGames(prev => new Set([...prev, g.game_id]))}`

3. **Tier 2 section** (`## TIER 2` heading) — same structure as Tier 1

4. **Footer links** (bottom of page):
   - `→ Full Standings` (links to `/standings`)
   - `→ Season Leaders` (links to `/leaderboards`)

**Loading/error states:**
- While conglomerate data loading: `<div className="p-6 text-text-muted">Loading...</div>`
- If `code` doesn't match any conglomerate: `<div className="p-6 text-text-muted">Conference not found.</div>`
- If schedule loading: show header and sections but with empty game grids

**Grid layout:** `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3` (matches existing GameCard grids)

## Constraints

- No new npm packages
- Do not modify `GameCard.tsx`, `ScoreboardWidget.tsx`, or `hooks.ts`
- No backend changes — all filtering is client-side using program ID sets from standings
- Use `primary_color` from API for header background; always use white (`#ffffff`) text for header to avoid contrast issues (simpler than luminance check)
- `useConglomerateStandings` must use `enabled: !!conglomerate?.id` to avoid fetching with id=0

## Out of Scope

- `web/src/api/hooks.ts` (unit 01a — already merged)
- `web/src/components/ScoreboardWidget.tsx` (unit 01b — already merged)
- `web/src/App.tsx` — this unit does NOT wire the route; unit 03 does that
- `web/src/pages/Home.tsx` (unit 03)
- Cross-conference games (games where home and away are from different conferences): show on both conference pages if a team appears — the filter `allIds.has(home) || allIds.has(away)` handles this naturally
- Per-program DB colours for end zones in ScoreboardWidget (that widget uses hashed colours; those are unit 01b's concern)
- Historical week navigation — current week schedule only; WeekSchedule page handles history

## Assumptions

- `ConglomerateOut.code` uniquely identifies a conference (confirmed — 5 conglomerates, unique codes)
- After units 01a and 01b are merged to main, the worktree for this unit will have access to `useTickerGameState`, `useAllConglomerates`, `useConglomerateStandings`, and `ScoreboardWidget`
- `ScheduleGame.home_program_id` and `away_program_id` match the `id` field in `ProgramStanding` (confirmed — both come from the `programs` table primary key)

## Handoff

Commit to branch `sprint/gridiron/02-conference-page`.

Unit 03 (`App.tsx` + `Home.tsx` + `NavBar.tsx`) will import `ConferencePage` and add the `/conference/:code` route.
