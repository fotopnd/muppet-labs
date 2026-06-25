## Sprint Manifest — gridiron — 2026-06-22

**Feature set:** Conference home pages with live scoreboards + compact scoreboard widget; full app routing restored
**Total units:** 4 (after ponytail pass)
**Parallelism:** 01a + 01b run simultaneously; 02 after both; 03 after 02

---

### Ponytail report

| Decision | What | Why |
|---|---|---|
| DISCARDED | gridiron-live-stats-broadcast brief | All 3 features were already implemented or superseded by this sprint |
| CUT | Backend schedule enrichment (add conglomerate_code to ScheduleGame) | Client-side filtering via program ID sets from standings achieves the same result with no backend change |
| CUT | Shared colour utility file | Only 2 components need school colour helpers; copy cost < abstraction cost |
| CUT | Derived clock as a separate hook | 3-line inline formula in ScoreboardWidget; no abstraction needed |
| SEQUENTIAL | 02 after 01a+01b | ConferencePage imports useTickerGameState (01a) and ScoreboardWidget (01b) |
| SEQUENTIAL | 03 after 02 | App.tsx imports ConferencePage |
| MERGED | NavBar fix into 03 | One-liner; not worth its own agent run |

---

### Units

| ID | Slug | Branch | Brief | Files owned | Status | Depends on | Parallel-safe with |
|---|---|---|---|---|---|---|---|
| 01a | ticker-and-conglomerate-hooks | sprint/gridiron/01a-ticker-and-conglomerate-hooks | roles/brief/archive/2026-06-22-gridiron-01a-ticker-and-conglomerate-hooks-brief.md | `web/src/api/hooks.ts` | complete | — | 01b |
| 01b | scoreboard-widget | sprint/gridiron/01b-scoreboard-widget | roles/brief/archive/2026-06-22-gridiron-01b-scoreboard-widget-brief.md | `web/src/components/ScoreboardWidget.tsx` | complete | — | 01a |
| 02 | conference-page | sprint/gridiron/02-conference-page | roles/brief/archive/2026-06-22-gridiron-02-conference-page-brief.md | `web/src/pages/ConferencePage.tsx` | complete | 01a, 01b | — |
| 03 | app-home-routing | sprint/gridiron/03-app-home-routing | roles/brief/archive/2026-06-22-gridiron-03-app-home-routing-brief.md | `web/src/App.tsx`, `web/src/pages/Home.tsx`, `web/src/components/NavBar.tsx` | complete | 02 | — |

---

### Execution guide

See `skills/sprint-agent-handoff.md` for agent spawn + merge procedure.

**Merge order:**
1. Spawn 01a + 01b in parallel → merge both → push main
2. Spawn 02 → merge → push main
3. Spawn 03 → merge → push main

**Verification (after 03 merges):**
```bash
cd /Users/fotopnd/Documents/muppet-labs/projects/gridiron/web
pnpm dev
# localhost:5177 (or configured port)
# / → 5 conference cards
# /conference/ATLN → conference page with coloured header, tier 1 + tier 2 sections
# ScoreboardWidget shows field strip + derived clock when game 153 is live
# pnpm build → no TypeScript errors
```

**No deploy to fotopnd.dev — localhost only until further notice.**
