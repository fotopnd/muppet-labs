## Live Tester Report — 2026-06-21 14:35

**Sim state:** Week 2, 10 live games (fresh replay, ~Q1 play 30 at time of testing)

---

### Passed

- **Schedule page**: 60 games loaded (10 live, 50 complete). Live cards and complete cards both present.
- **Live play stream (T3)**: Plays grew 9 → 10 → 32+ across checks spaced 6–8 seconds apart. Not dumped all at once. Streaming gate confirmed working.
- **Score updates via ticker (T4)**: Ticker delivered play-by-play events for all 10 games. Observed FG score update: score 0-0 → 0-3 on FIELD_GOAL_ATTEMPT. Quarter (Q1) present on each event.
- **Progressive stats / stats panel (T6)**: At Q1 play 21, QB White had 4/4 49yds. Game's final score is 41-12 so these are clearly partial stats, not full-game totals. Stats counting up correctly.
- **Scoring plays identifiable (T7 data)**: play_log contains `play_type` field; scoring plays (TOUCHDOWN, FIELD_GOAL_ATTEMPT, PAT_CONVERSION) are present and filterable. Saw correct score transitions. Frontend toggle needs visual verification.
- **Multi-game independent (T8)**: Games 153, 441, 1017 all at Q1 ~32 plays simultaneously, each with different latest play types. Three concurrent SSE streams confirmed independent.
- **Live leaders (T10)**: `/live/leaders` returns 5 rush leaders and 5 rec leaders with program emoji, name, and yards. Top rusher: 💨 Pugh 35y. Top receiver: 🚢 Yacoub 88y.
- **Per-game SSE stream**: `/games/<id>/stream` confirmed delivering new plays live (received 2 events in ~6s).

---

### Failed

- **Drive panel (T5)**: Cannot verify visually — no browser. API supplies `field_pos_before`, `field_pos_after`, `possession`, `x_coord`, `y_coord` on every play event. Component render is untested.
- **Play log toggle (T7 UI)**: Cannot verify the "Scoring Plays" button filter without browser. Data is correct; toggle behavior untested.
- **Multi-game switch (T8 UI)**: Cannot verify both tabs continue streaming when switching between them. API is confirmed correct.
- **Game completion transition (T9)**: Games are ~Q1 at time of report (~8 minutes until completion). Could not observe game-complete transition.

---

### Warnings

- **"FINAL · reveal" vs "FINAL · tap to reveal"**: GameCard.tsx renders `FINAL · reveal` (not `FINAL · tap to reveal` as the test checklist says). Functionally correct — tap intercepts and reveals — but label text differs from spec.
- **Live games carry final scores in DB**: `games.home_score` is written by the engine before replay starts (e.g. game 153: 41-12 in DB while Q1 is streaming). GameCard correctly uses ticker `liveScore` for live cards, not `game.home_score`, so no spoiler leak. But if `liveScore` is ever missing (SSE not yet connected), the score block shows nothing — the card will show blank score briefly on load. Acceptable but worth noting.
- **Spoiler reveal text (T2)**: Could not visually confirm "FINAL · tap to reveal" renders and navigates. Code review shows logic is correct (intercept tap → reveal → navigate). Needs browser verification.

---

### Bugs fixed during this session (not for implementer — already resolved)

1. **Sentinel bug**: `orchestrator.py` line 99 referenced undefined `game_queues` local variable instead of `app.state.game_queues.get(game_id, [])`. Games were never marked `complete` after replay finished. **Fixed.**
2. **play_log doubling on dev reset**: Re-running the engine without clearing old play_log entries doubled all rows (278 rows instead of 140 for a single game), causing interleaved plays from two different simulations. **Fixed** by adding `DELETE FROM play_log WHERE game_id=:gid` in `_run_game_sync` before `GameEngine.run()`.

---

### Bugs to fix (implementer)

1. **Complete game card label mismatch**: Card renders "FINAL · reveal" but test spec and likely intended UX says "FINAL · tap to reveal". `GameCard.tsx` span text should be updated.
2. **No browser verification for drive panel, scoring plays toggle, multi-game tab switching, game completion transition**: These require a browser session to confirm. Schedule a browser-based follow-up pass once QA tooling is available.
