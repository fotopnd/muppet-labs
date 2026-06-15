# Design Brief Output — Year Zero Game

**Sequence:** `new-project-full` | **Role:** design-brief | **Step:** 4 of 9  
**Date:** 2026-06-15

---

## Interface Context

**Two distinct contexts apply — one per route.**

**`/` (game):** Outside the three standard contexts. The visual design is fully specified in `resources/visual-design.md` (16-bit pixel art, Papers Please aesthetic, warm amber lamplight palette). The canonical `design_style.md` token system does not govern the game surface — it is overridden by the pixel art palette defined in visual-design.md. The frontend-architect treats visual-design.md as the authoritative style contract for game components and ignores design_style.md for this route.

**`/analytics` (live dashboard):** **Application Dashboard** context. High data density, live Recharts charts, SSE-driven updates. Canonical `design_style.md` tokens apply. Accent hue: amber (`oklch(0.75 0.15 60)`) — matches the lamplight warmth of the game without clashing.

---

## Primary Interaction

**Swipe a card left (REDACT) or right (CLEAR).** Everything else — bar state, phase progression, day structure, session submission — is in service of this single gesture. The interface must make the swipe feel physical and decisive. The document card is the game.

---

## Key Visual Components

**Game route (`/`):**

1. **`DocumentCard`** — centrepiece of the game. Occupies ~80% viewport width on 375px mobile. Shows header strip (DAY · SECTOR · DOC), body text (2–4 sentences, pixel serif font), and Sovereign-9 readout strip at the bottom (dark terminal background, green phosphor text). Handles swipe gesture (`useDrag`). On commit: card slides off-screen with slight rotation; stamp animation overlays (`APPROVED` green right, `REDACTED` red left); next card slides in from top. No-agent cards omit the Sovereign-9 strip entirely.

2. **`StatusBar`** — five pixel bars fixed at top of viewport. Each bar: emoji icon + pixel fill bar (~40px wide, 8px tall). Fill uses bar colour; unfilled uses `#1e1e1e`. COMPLIANCE bar has a white centre pip at the 50-point mark. Bars within 15 points of game-over threshold pulse at 1Hz. No numeric labels during play.

3. **`GameOver`** — full-screen takeover. Dark red tint. `FILE CLOSED` header in pixel font. Game-over reason text (narrative sentence from mechanics spec). Stats: days survived, documents processed, accuracy %. Single button: `RETURN TO REGISTRY`. Replaces all other UI when triggered.

4. **`DayScreen`** — overlay after every 10 cards. Shows day number, correct count / 10, one Ministry flavour line (hardcoded rotation of ~10 phrases). `CONTINUE` button advances to next day. Styled as a printed memo — cream paper background, dark ink, slightly worn edges (same aesthetic as Lore page).

5. **`UpgradeScreen`** — full-screen terminal takeover on category tier upgrade. Dark green-black background, bright green phosphor text. Shows category name, old tier → new tier, and a one-line description of what changed. `PRESS ANY KEY` (or tap) to dismiss.

**Analytics route (`/analytics`):**

6. **`AnalyticsPage`** — four Recharts panels in a 2×2 grid (desktop) / stacked (mobile): sessions today (number card), global FP/FN rate (number cards), avg latency (number card), system drift error rate by session date (LineChart). All panels update live via SSE. Uses canonical `design_style.md` tokens.

---

## Done Criteria

**Game route:**

1. Start screen renders with title `PROJECT REDACTED: YEAR ZERO` in pixel font, two-line hook text, `PRESS START` (primary, larger) and `READ THE LORE` (secondary, smaller) buttons — matching the visual-design.md start screen mockup.
2. `DocumentCard` renders at ~80% viewport width on 375px with header strip, body text in pixel serif, and Sovereign-9 strip at bottom. Tapping the strip expands the full reasoning panel.
3. No-agent cards omit the Sovereign-9 strip — the card bottom edge ends cleanly with no empty strip placeholder.
4. Swiping right past 30% threshold commits CLEAR: card exits right with ~5° rotation, green stamp animation plays, next card enters from top.
5. Swiping left past 30% threshold commits REDACT: card exits left with ~5° rotation, red stamp animation plays, next card enters from top.
6. Cards below threshold snap back to centre on release.
7. `StatusBar` shows all 5 bars with correct emoji labels; COMPLIANCE bar has visible centre pip at 50%; bars update immediately after each swipe.
8. A bar within 15 points of its game-over threshold visibly pulses (colour or opacity change at ~1Hz).
9. `DayScreen` appears after card 10 of each day, shows correct count, advances on tap.
10. `UpgradeScreen` appears on category tier upgrade, shows old → new tier, dismisses on tap/keypress.
11. `GameOver` screen renders with correct game-over condition text and stats on any bar hitting its threshold.
12. `LorePage` is accessible from start screen; `BEGIN REGISTRY DUTY` returns to start.
13. No horizontal scroll at 375px viewport width.
14. `touch-action: none` on swipe zone — no browser scroll interference during card swipe.

**Analytics route:**

15. `/analytics` renders four data panels with live values from SSE.
16. SSE connection is established on mount; panels update without page refresh when a new session batch is submitted.
17. If SSE is disconnected, panels show last-known values (no blank/error state during brief reconnect).
18. Charts use `ResponsiveContainer` — no fixed pixel widths.
19. Analytics page uses canonical `design_style.md` tokens (amber accent, canvas/surface backgrounds).

**Build quality:**

20. `pnpm build` produces `dist/` with zero TypeScript errors and zero lint errors.
21. Each game component has at least one vitest test verifying it renders without throwing.

---

## Handoff

The frontend-architect reads this file alongside `architect/output.md` and `resources/visual-design.md`.

**Open decisions for frontend-architect:**

- **Token split:** define two token layers in `index.css`. Layer 1: pixel art tokens (`--color-room`, `--color-desk`, `--color-card-bg`, `--color-terminal-bg`, `--color-terminal-text`, `--font-pixel`, `--font-pixel-body`, bar colours). Layer 2: canonical analytics tokens (`--color-canvas`, `--color-surface`, etc. with amber accent). Game components use pixel tokens; analytics components use canonical tokens. Frontend-architect defines exact OKLCH values matching visual-design.md hex palette.

- **Stamp animation implementation:** 3-frame CSS `@keyframes` on an overlay `div`. Architect specifies exact keyframe timings (suggest: 0ms → stamp hidden, 40ms → stamp descending, 120ms → stamp applied, 400ms → card exit begins).

- **Card pool draw order:** `DocumentCard` draws from `cardPool` in `useGameState`. The pool is shuffled on load — architect specifies whether shuffle happens in the reducer (`START_SESSION`, `PHASE_CARDS_LOADED` actions) or in `Game.tsx` before dispatching.

- **Flavour lines for `DayScreen`:** A hardcoded array of ~10 Ministry messages in `constants.ts`, cycled by `gameDay % lines.length`. Frontend-architect includes the array.
