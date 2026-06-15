# Frontend-Architect Output — Year Zero Game

**Sequence:** `new-project-full` | **Role:** frontend-architect | **Step:** 5 of 9  
**Date:** 2026-06-15  
**Reads:** `design-brief/output.md`, `architect/output.md`, `design_style.md`, `resources/visual-design.md`

---

## Open Decisions Resolved

**Token split:** Two semantic layers in `index.css` `@theme {}` — pixel art tokens (`--color-pixel-*`, `--font-pixel`) for game route; canonical tokens (standard names from `design_style.md`) for analytics route.

**Stamp animation timing:**
- `0ms` → stamp hidden (`opacity: 0`, `translateY(-40px)`)
- `40ms` → stamp descending (`opacity: 1`, `translateY(-8px)`, `rotate(-2deg)` — slight misalignment)
- `120ms` → stamp applied (`translateY(0)`, ink pulse)
- `400ms` → card exit animation begins
- `500ms` → next card slides in from above desk

**Card shuffle:** In reducer, on `START_SESSION` and `PHASE_CARDS_LOADED` actions. Fisher-Yates shuffle applied to incoming `Card[]` before storing in `cardPool`. `Game.tsx` passes raw API response; reducer owns shuffle.

---

## Token Layer

```css
/* src/index.css */
@import "tailwindcss";
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');

@theme {
  /* ── Pixel Art Layer (game route) ── */
  --font-pixel: 'Press Start 2P', monospace;

  --color-pixel-room:         oklch(12% 0.02 45);   /* #1a1510 — room shadow */
  --color-pixel-desk:         oklch(28% 0.03 45);   /* #4a3728 — desk surface */
  --color-pixel-desk-lit:     oklch(34% 0.04 45);   /* #5c4535 — lamplight on desk */
  --color-pixel-lamp:         oklch(68% 0.14 65);   /* #c8922a — warm amber glow */
  --color-pixel-card:         oklch(89% 0.02 80);   /* #e8e0c8 — aged cream paper */
  --color-pixel-card-text:    oklch(18% 0.02 45);   /* #2a2218 — dark ink */
  --color-pixel-terminal-bg:  oklch(12% 0.04 145);  /* #0d1a0d — deep green-black */
  --color-pixel-terminal:     oklch(72% 0.20 145);  /* #44cc44 — green phosphor */
  --color-pixel-stamp-clear:  oklch(55% 0.18 145);  /* green stamp ink */
  --color-pixel-stamp-redact: oklch(50% 0.18 20);   /* red stamp ink */

  --color-bar-trust:      oklch(50% 0.10 250);  /* #3a6ea8 muted blue */
  --color-bar-security:   oklch(43% 0.12 20);   /* #aa3a3a muted red */
  --color-bar-treasury:   oklch(60% 0.12 65);   /* #aa8822 muted gold */
  --color-bar-legitimacy: oklch(54% 0.10 145);  /* #3a8844 muted green */
  --color-bar-compliance: oklch(40% 0.12 300);  /* #7a3aaa muted purple */
  --color-bar-empty:      oklch(15% 0 0);        /* #1e1e1e unfilled */

  /* ── Canonical Layer (analytics route) ── */
  --font-sans: ui-sans-serif, system-ui, sans-serif;
  --font-mono: ui-monospace, 'JetBrains Mono', monospace;

  --color-canvas:          oklch(98.5% 0 0);
  --color-surface:         oklch(100% 0 0);
  --color-surface-muted:   oklch(96.1% 0 0);
  --color-border:          oklch(91.8% 0 0);
  --color-text-primary:    oklch(15.1% 0 0);
  --color-text-secondary:  oklch(44.6% 0 0);
  --color-text-muted:      oklch(63.2% 0 0);
  --color-text-inverse:    oklch(98.5% 0 0);
  --color-accent:          oklch(75% 0.15 60);   /* amber */
  --color-accent-hover:    oklch(68% 0.15 60);
  --color-accent-subtle:   oklch(96% 0.04 60);
  --color-success:         oklch(60% 0.18 145);
  --color-warning:         oklch(75% 0.15 75);
  --color-danger:          oklch(55% 0.20 20);
}

/* Pixel rendering — apply to card/sprite elements */
.pixel-render {
  image-rendering: pixelated;
  image-rendering: crisp-edges;
}

/* Scanline overlay — apply to terminal areas */
.scanlines::after {
  content: '';
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(
    to bottom,
    transparent 0px,
    transparent 3px,
    oklch(0% 0 0 / 0.12) 3px,
    oklch(0% 0 0 / 0.12) 4px
  );
  pointer-events: none;
}
```

---

## Page Layout

### Game Route (`/`)

Single-column full-viewport. No grid — spatial layout only.

```
┌─────────────────────────────────┐  h-12 fixed top-0 z-40 bg-pixel-room
│         StatusBar               │
├─────────────────────────────────┤
│   Room shadow (bg-pixel-room)   │  pt-12 (below status bar) + ~2rem room padding
│                                 │
│  ┌ Desk Zone ──────────────── ┐ │  bg-pixel-desk radial-gradient to pixel-lamp at centre
│  │   ┌─ DocumentCard ──────┐  │ │  w-[80vw] max-w-[340px] mx-auto
│  │   │  CardHeader         │  │ │
│  │   │  CardBody           │  │ │
│  │   │  SovereignStrip     │  │ │
│  │   └─────────────────────┘  │ │
│  └─────────────────────────── ┘ │
│                                 │
│  ← REDACT          CLEAR →      │  text-pixel-room/60 font-pixel text-[8px] pb-4
└─────────────────────────────────┘
```

Z-index stack: room bg (0) → desk + gradient (10) → DocumentCard (20) → StampOverlay (30) → StatusBar fixed (40) → screen overlays: DayScreen / UpgradeScreen / GameOver (50).

### Analytics Route (`/analytics`)

```
h-16 header (bg-surface border-b border-border)
grid grid-cols-1 md:grid-cols-2 gap-6 p-6 bg-canvas
  MetricCard × 3
  DriftChart (md:col-span-2 on desktop, full-width on mobile)
```

---

## Component Specs

### `StatusBar`

- **Hierarchy:** `StatusBar` → 5× `BarUnit`
- **Layout:** `flex items-center justify-between px-2 h-12 bg-pixel-room`
- **`BarUnit`:** `flex items-center gap-1`. Emoji `text-[10px]`. Bar fill div `w-10 h-2` with inline `style={{ background: \`linear-gradient(to right, var(--color-bar-{key}) ${pct}%, var(--color-bar-empty) ${pct}%)\` }}` — dynamic pct requires inline style (runtime computed value).
- **COMPLIANCE centre pip:** `relative` wrapper; `absolute left-1/2 top-0 bottom-0 w-px bg-white/60` at 50%.
- **Danger pulse:** `animate-pulse` on fill div when `Math.abs(value - threshold) <= 15`.
- **Data:** `bars: BarState` from `useGameState`.

### `DocumentCard`

- **Hierarchy:** `DocumentCard` → `CardHeader` + `CardBody` + `SovereignStrip?` + `StampOverlay`
- **Layout:** `relative w-[80vw] max-w-[340px] flex flex-col border border-pixel-card-text/30 bg-pixel-card pixel-render` with inline `style={{ touchAction: 'none' }}`.
- **Gesture:** `useDrag` on the root div. During drag: `style={{ transform: \`translateX(${dx}px) rotate(${dx * 0.02}deg)\` }}`. Commit on `|dx| > el.offsetWidth * 0.3`.
- **`CardHeader`:** `bg-pixel-room/80 text-pixel-terminal px-2 py-1 font-pixel text-[8px]`
- **`CardBody`:** `px-3 py-3 font-pixel text-[9px] leading-5 text-pixel-card-text`
- **`SovereignStrip`:** rendered only when `card.agentCondition !== 'none'`. `relative bg-pixel-terminal-bg text-pixel-terminal font-pixel text-[8px] px-2 py-1 scanlines cursor-pointer`. Tapping toggles `expanded` local state. Expanded: `SovereignDetail` panel slides down via `max-h-0 → max-h-24 overflow-hidden transition-all`.
- **`StampOverlay`:** `absolute inset-0 flex items-center justify-center pointer-events-none`. Stamp text `font-pixel text-[14px]`. Three animation phases via `stampState` state: `idle` (hidden), `descending` (CSS keyframe `stamp-descend` 120ms), `applied` (visible at rest until card exits).
- **States:** idle → dragging (`cursor-grabbing`) → committed (exit keyframe) → entering (next card `slide-in` keyframe).

### `GameOver`

- **Hierarchy:** `GameOver` → red tint overlay + `FileClosedStamp` + `ReasonText` + `StatsBlock` + `ReturnButton`
- **Layout:** `fixed inset-0 z-50 bg-pixel-room flex flex-col items-center justify-center gap-6 px-6`
- **Red tint:** `absolute inset-0 bg-[oklch(50%_0.12_20/0.2)]`
- **`FileClosedStamp`:** `font-pixel text-pixel-card text-[14px] tracking-wider`  — `[ FILE CLOSED ]`
- **`ReasonText`:** `font-pixel text-pixel-card text-[8px] leading-6 max-w-[280px] text-center`
- **`StatsBlock`:** `font-pixel text-pixel-card text-[8px] leading-7 w-[200px]`
- **`ReturnButton`:** `font-pixel text-pixel-card text-[8px] border border-pixel-card px-4 py-2 hover:bg-pixel-card/10 active:bg-pixel-card/20`
- **Data:** `reason: GameOverReason`, `stats: { days: number, decisions: number, accuracy: number }`

### `DayScreen`

- **Hierarchy:** `DayScreen` → `MemoHeader` + `StatsLines` + `FlavourLine` + `ContinueButton`
- **Layout:** `fixed inset-0 z-50 bg-pixel-card/95 flex flex-col items-center justify-center gap-4 px-6`
- **`MemoHeader`:** `font-pixel text-pixel-card-text text-[10px] border-b border-pixel-card-text/30 pb-2 w-[260px] text-center`
- **`StatsLines`:** `font-pixel text-pixel-card-text text-[8px] leading-7`
- **`FlavourLine`:** `font-pixel text-pixel-card-text/70 text-[7px] max-w-[260px] text-center leading-6 italic`
- **`ContinueButton`:** same style as `ReturnButton` but `text-pixel-card-text border-pixel-card-text`

### `UpgradeScreen`

- **Hierarchy:** `UpgradeScreen` → dismiss overlay + `TerminalBox`
- **Layout:** `fixed inset-0 z-50 bg-pixel-room flex items-center justify-center`
- **Dismiss overlay:** `absolute inset-0 cursor-pointer` — click/keydown dismisses
- **`TerminalBox`:** `relative bg-pixel-terminal-bg border border-pixel-terminal p-6 max-w-[300px] font-pixel text-pixel-terminal text-[8px] leading-7 scanlines`

### `AnalyticsPage`

- **Hierarchy:** `AnalyticsPage` → `AnalyticsHeader` + `MetricCard`×3 + `DriftChart`
- **`MetricCard`:** `bg-surface rounded border border-border p-4`. Label `text-text-muted text-xs font-mono`. Value `text-text-primary text-2xl font-mono font-bold`. Null value renders `—`.
- **`DriftChart`:** `bg-surface rounded border border-border p-4 md:col-span-2`. `ResponsiveContainer width="100%" height={200}`. `Line dataKey="error_rate" stroke="var(--color-accent)" dot={false} strokeWidth={2}`. `XAxis dataKey="date"` with `tickFormatter`.
- **SSE pattern:**
  ```tsx
  useEffect(() => {
    const es = new EventSource(`${API_BASE}/analytics/stream`)
    es.onmessage = (e) => setData(JSON.parse(e.data))
    return () => es.close()
  }, [])
  ```
  Last-known values shown on disconnect — no error state, no blank panels.

---

## Constants (`src/game/constants.ts`)

```typescript
export const MINISTRY_FLAVOUR_LINES = [
  "The Ministry notes your efficiency.",
  "Your diligence serves the Registry.",
  "Sovereign-9 has been notified of your corrections.",
  "The neighbourhood petition was cleared for dissemination.",
  "A suspicious requisition was intercepted and destroyed.",
  "The Registry thanks you for your continued service.",
  "Your override record has been logged for review.",
  "The morning dispatch has been processed without incident.",
  "The Inspector General's office sends its regards.",
  "Another day. Another queue. The work continues.",
]

export const GAME_OVER_NARRATIVES: Record<GameOverReason, string> = {
  TRUST_ZERO: "Citizens have lost faith in the Registry. Document submissions cease. The new democracy has no administrative foundation.",
  SECURITY_MAX: "Remnants of the old regime have exploited the open gate. A security incident triggers emergency rule.",
  TREASURY_ZERO: "The Registry has been defunded. The new government cannot sustain oversight operations.",
  LEGITIMACY_ZERO: "The international community has withdrawn recognition. The new government is accused of reprising the old regime's censorship.",
  COMPLIANCE_MAX: "Your decisions have become indistinguishable from the machine's. The Registry is a rubber stamp.",
  COMPLIANCE_ZERO: "No automated system can function under constant override. The Registry collapses into paralysis.",
}

export const SECTOR_LABELS = ['1A','2B','3C','4D','5E','6F','7G','8H','9J','10K']
```

---

## Constraints Applied

**Inline style justification — bar fill:** Bar percentage is a runtime-computed value. `style={{ background: \`linear-gradient(...)\` }}` is the only correct approach — not arbitrary Tailwind, not a CSS custom property set inline (which would require `style` anyway). Documented per typescript-conventions.md: dynamic computed values justify inline style.

**`max-w-[340px]` on card:** Uses a pixel arbitrary value. Justified as a safe upper mobile bound (not a spacing hack). Alternative `max-w-sm` (384px) is token-compliant but slightly wider — implementer chooses, documents if deviating.

**`design_style.md` does not govern game route:** Confirmed in design-brief. Pixel art tokens override. Analytics route fully compliant with canonical tokens.

---

## Open Questions

None. One implementation choice left to implementer: `StartScreen` / `LorePage` as routes or as `gameState.phase` conditional renders within `Game.tsx`. Recommendation: conditional render — simpler, avoids router state for a sequential flow.

---

## Handoff

Next role: implementer (backend phase — step 6a)  
Reads: this file + `architect/output.md` + `python-conventions.md` + `vibecoding-style.md`  
Backend phase produces: `pyproject.toml`, `docker-compose.yml`, Alembic migration, all four FastAPI routers, `seed_library.py` (30 fixture cards), `generate_library.py` stub. Ends with `uv run pytest` green.  
Then: implementer (frontend phase — step 6b) reads `backend-output.md` + this file → produces all React components and game logic. Ends with `pnpm build` clean and vitest passing.
