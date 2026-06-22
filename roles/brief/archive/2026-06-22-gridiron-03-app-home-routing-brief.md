## Project Name
gridiron

## Description
Restore the full route tree in `web/src/App.tsx`, rewrite `web/src/pages/Home.tsx` as a conference selection hub (5 cards, one per NAFCA conference), and update `web/src/components/NavBar.tsx` to fix the schedule link. This is the final wiring unit that makes everything navigable.

## Language(s)
TypeScript / React / Tailwind

## Background / Current State

**App.tsx (current — broken):**
```tsx
export default function App() {
  return (
    <div className="min-h-screen bg-canvas text-text-primary">
      <TickerBar />
      <main>
        <Routes>
          <Route path="/games/:gameId" element={<Gamecast />} />
          <Route path="*" element={<Navigate to="/games/153" replace />} />
        </Routes>
      </main>
    </div>
  )
}
```
- `NavBar` is not rendered
- Only Gamecast is reachable; everything else redirects to game 153

**NavBar.tsx (current):**
- Has a "Schedule" link pointing to `/schedule`
- There is no route for `/schedule` (WeekSchedule is at `/schedule/week/:week`)

**Home.tsx (current):**
- Calls `useCurrentSchedule()` and renders a grid of `GameCard` — "wall of games"
- Must be replaced with conference hub

**All pages exist** and will be importable by the time this unit runs:
`Home` (rewritten), `WeekSchedule`, `ConferencePage` (new, from unit 02), `Standings`, `Programs`, `ProgramDetail`, `Leaderboards`, `Gamecast`

**New hook available (from unit 01a):** `useAllConglomerates()`

## Success Criteria

### `web/src/App.tsx` — full route tree

```tsx
import NavBar from '@/components/NavBar'
import TickerBar from '@/components/TickerBar'
import Home from '@/pages/Home'
import WeekSchedule from '@/pages/WeekSchedule'
import ConferencePage from '@/pages/ConferencePage'
import Standings from '@/pages/Standings'
import Programs from '@/pages/Programs'
import ProgramDetail from '@/pages/ProgramDetail'
import Leaderboards from '@/pages/Leaderboards'
import Gamecast from '@/pages/Gamecast'
import { Navigate, Route, Routes } from 'react-router-dom'

export default function App() {
  return (
    <div className="min-h-screen bg-canvas text-text-primary">
      <NavBar />
      <TickerBar />
      <main className="pb-16 md:pb-0">   {/* bottom padding for mobile nav bar */}
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/conference/:code" element={<ConferencePage />} />
          <Route path="/schedule/week/:week" element={<WeekSchedule />} />
          <Route path="/schedule" element={<Navigate to="/schedule/week/1" replace />} />
          <Route path="/standings" element={<Standings />} />
          <Route path="/programs" element={<Programs />} />
          <Route path="/programs/:programId" element={<ProgramDetail />} />
          <Route path="/leaderboards" element={<Leaderboards />} />
          <Route path="/games/:gameId" element={<Gamecast />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}
```

### `web/src/pages/Home.tsx` — conference hub

Replace the entire file:

```tsx
import { Link } from 'react-router-dom'
import { useAllConglomerates } from '@/api/hooks'

export default function Home() {
  const { data, isLoading } = useAllConglomerates()

  if (isLoading) return <div className="p-6 text-text-muted">Loading...</div>

  return (
    <div className="p-4 md:p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">NAFCA</h1>
      <p className="text-text-muted text-sm mb-6">National Association of Fictional Collegiate Athletics</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {(data ?? []).map((conf) => (
          <Link
            key={conf.code}
            to={`/conference/${conf.code}`}
            className="flex items-center gap-4 bg-surface border border-border rounded-lg p-4 hover:border-accent/40 transition-colors"
          >
            <div
              className="w-1.5 self-stretch rounded-full shrink-0"
              style={{ backgroundColor: conf.primary_color }}
            />
            <div>
              <div className="font-semibold">{conf.full_name}</div>
              <div className="text-xs text-text-muted mt-0.5">{conf.network} · {conf.region}</div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
```

### `web/src/components/NavBar.tsx` — fix schedule link

Change the LINKS array entry for Schedule:
```ts
// Before:
{ to: '/schedule', label: 'Schedule', icon: '📅' },
// After:
{ to: '/schedule/week/1', label: 'Schedule', icon: '📅' },
```
(App.tsx already handles `/schedule` → redirect to `/schedule/week/1`, but this avoids the redirect for direct nav clicks.)

## Constraints

- Do not modify any page component other than `Home.tsx`
- Do not modify `TickerBar.tsx`, `GameCard.tsx`, `ScoreboardWidget.tsx`, `hooks.ts`, or any API file
- The `<main>` wrapper needs `pb-16 md:pb-0` to account for the mobile bottom nav bar (NavBar renders a fixed bottom bar on mobile)
- `ConferencePage` is available as `@/pages/ConferencePage` (merged before this unit runs)
- `useAllConglomerates` is available from `@/api/hooks` (unit 01a — merged)

## Out of Scope

- `web/src/pages/ConferencePage.tsx` (unit 02 — already merged)
- `web/src/api/hooks.ts` (unit 01a — already merged)
- `web/src/components/ScoreboardWidget.tsx` (unit 01b — already merged)
- Updating the `ProgramDetail` page itself — route just needs to point to the existing component
- Changing the NavBar's "Home" link label (it correctly points to `/`)

## Assumptions

- `ProgramDetail.tsx` exists at `web/src/pages/ProgramDetail.tsx` and accepts `useParams<{ programId: string }>()` internally
- All page components compile without error (they were working before App.tsx was stripped)
- `'NAFCA'` is the correct league acronym for the branding string in Home

## Handoff

Commit to branch `sprint/gridiron/03-app-home-routing`.

After this unit merges to main, run `pnpm dev` in `projects/gridiron/web/` to verify the full site:
- `/` → 5 conference cards
- `/conference/ATLN` (or any conference code) → conference page with scoreboard and schedule
- All nav links resolve correctly
- `pnpm build` passes TypeScript checks
