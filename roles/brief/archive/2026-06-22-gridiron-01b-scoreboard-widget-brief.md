## Project Name
gridiron

## Description
Create a new compact scoreboard widget component at `web/src/components/ScoreboardWidget.tsx`. This replaces the static `GameCard` for live games on the conference page — it shows a single-line field graphic with ball position, live score, an approximate derived clock, and the last play result.

## Language(s)
TypeScript / React / Tailwind / inline SVG

## Background / Current State

`GameCard.tsx` is the only game card component. It shows a static boxscore (home/away emoji + score text) and a status badge. It has no field graphic and no play-by-play line.

`Gamecast.tsx` has a `DrivePanel` component that renders a full SVG football field with play arrows — but it's multi-row and too large for a scoreboard tile. The colour helpers (`schoolColor`, `isNearFieldGreen`, `ezColor`, `arrowColor`, `hslParts`) live inline in `Gamecast.tsx` and are not exported.

The `SsePlayEvent` type already carries everything needed: `play_number`, `quarter`, `down`, `distance`, `field_pos_before`, `field_pos_after`, `score_home`, `score_away`, `possession`, `description`, `play_type`, `yards_gained`.

## Success Criteria

A new file `web/src/components/ScoreboardWidget.tsx` that:

**Props:**
```ts
type Props = {
  game: ScheduleGame
  liveState?: SsePlayEvent
}
```

**Renders a card that links to `/games/{game.game_id}`:**

1. **Field strip SVG** (height ≈ 10px, full card width):
   - Left end zone: home team school color (use `ezColor(game.home_program_id)`)
   - Right end zone: away team school color (use `ezColor(game.away_program_id)`)
   - Green playing field in between
   - When `liveState` is present: white filled circle at ball position `fx(liveState.field_pos_after ?? 50)`; small triangle arrow indicating `liveState.possession` direction (pointing right if home has ball, left if away)
   - When no `liveState`: no ball marker (static field)

2. **Score row** (one line):
   - `{homeEmoji} {homeName abbreviated to ~10 chars}  14 — 7  {awayName abbreviated} {awayEmoji}`
   - Use `liveState.score_home/score_away` when live, else `game.home_score/game.away_score`

3. **Status line** (one line below score):
   - **Live with liveState**: `Q{quarter} {derivedClock} · {down && distance ? `${ordinal(down)} & ${distance}` : ''} · {truncate(description, 40)}`
   - **Complete**: `FINAL`
   - **Scheduled**: broadcast slot formatted (replace `_` with space, capitalize)

**Derived clock formula** (live only):
```ts
const PLAYS_PER_QUARTER = 34
const SECS_PER_PLAY = 4.44
const playsIntoQ = (liveState.play_number - 1) - (liveState.quarter - 1) * PLAYS_PER_QUARTER
const secsLeft = Math.max(0, (PLAYS_PER_QUARTER - playsIntoQ) * SECS_PER_PLAY)
const mins = Math.floor(secsLeft / 60)
const secs = String(Math.floor(secsLeft % 60)).padStart(2, '0')
// Display: `${mins}:${secs}`
```

**SVG helpers** (copy from `Gamecast.tsx` — do not import, inline in this file):
- `function fx(pos: number): number` — maps 0–100 field position to SVG x coordinate
- `function schoolColor(id: number): string`
- `function hslParts(c: string): [number, number, number] | null`
- `function isNearFieldGreen(c: string): boolean`
- `function ezColor(id: number): string`

**Card styling:** Use the same `bg-surface border border-border rounded-lg` pattern as `GameCard`. Make the entire card a `<Link to={href}>` from react-router-dom.

## Constraints

- No new npm packages
- Do not import from `Gamecast.tsx` — copy the 5 SVG helper functions inline
- Do not import `useTickerGameState` — the parent passes `liveState` as a prop (stateless component)
- SVG field strip height: aim for 10–12px rendered height (set `viewBox="0 0 100 10"` + `style={{ height: '12px', width: '100%' }}`)

## Out of Scope

- `web/src/api/hooks.ts` (unit 01a)
- `web/src/pages/ConferencePage.tsx` (unit 02)
- `web/src/App.tsx` (unit 03)
- `web/src/pages/Home.tsx` (unit 03)
- Possession arrow on field strip beyond a simple triangle — no line of scrimmage marker needed in this compact view
- Modifying or replacing `GameCard.tsx` — it continues to be used for non-live games

## Assumptions

- `ScheduleGame` has `home_program_id`, `away_program_id`, `home_emoji`, `away_emoji`, `home_name`, `away_name`, `home_score`, `away_score`, `status`, `broadcast_slot` (confirmed from types/index.ts)
- `SsePlayEvent.possession` is `'home'` or `'away'` string (confirmed)
- `SsePlayEvent.field_pos_after` may be `null` — default to 50 when null
- School color hashing is acceptable for end zone colours; no per-program DB colours needed

## Handoff

Commit to branch `sprint/gridiron/01b-scoreboard-widget`.

The conference page (unit 02) imports `ScoreboardWidget` from `@/components/ScoreboardWidget` and renders it for each live game, passing `liveState={tickerState.get(game.game_id)}`.
