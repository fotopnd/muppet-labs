# Live Tester — Role Contract

## Identity

The live tester role QAs the Gridiron site against a running sim. It is a focused, context-light role: it does not read the full codebase, does not plan changes, and does not implement fixes. Its only job is to open the running site, exercise the key user flows, and report what it sees.

Fixes go to the implementer. This role stops at observation.

---

## Inputs

| Source | What to load |
|---|---|
| This file | Role contract + test checklist |
| `resources/dev-sim-guide.md` | How to start the demo game if not already running |
| Running site | http://localhost:5177 |
| Running API | http://localhost:8006 |
| Demo game URL | http://localhost:5177/games/153 |

Do not read source files. Do not read the planner or implementer output. Check the site directly.

---

## Demo game

**Fixed game for all QA runs: game 153 — 🏯 Reading University vs 🌱 Savannah University**

Always test against this game. It streams fresh from play 1 each restart.
See `resources/dev-sim-guide.md` "Quick start — demo game" for reset steps.

---

## Pre-flight

Before testing, confirm the demo game is live:

```zsh
curl -s http://localhost:8006/games/153 | python3 -c "import sys,json; d=json.load(sys.stdin); print('game 153:', d['status'])"
```

Expected: `game 153: live`

If not live, follow the reset steps in `resources/dev-sim-guide.md`.

---

## Test Checklist

Run through these in order. Each test has a pass/fail criterion and notes field.

### 1. Schedule page

- Open `/schedule/week/<current>`
- **PASS if:** Game cards load. Live cards show a current score (not null, not 0-0 unless it is the first play). Complete cards show "FINAL · tap to reveal" instead of a score.
- **Check:** Do live card scores update without a page reload? Watch for ~4 seconds.
- **Check:** Do live cards show the current quarter (Q1/Q2/Q3/Q4)?

### 2. Spoiler reveal

- On the schedule page, find a complete game card ("FINAL · tap to reveal").
- Tap it.
- **PASS if:** Score appears and the browser navigates to the Gamecast for that game.

### 3. Live Gamecast — play stream

- Open a live game from the schedule: `/games/<game_id>`
- **PASS if:** Plays appear in the list within a few seconds of opening.
- **PASS if:** New plays append to the top of the list every ~4–5 seconds without a page reload.
- **FAIL if:** A full game's worth of plays loads immediately and nothing new comes in.

### 4. Live Gamecast — score header

- Watch the score header on a live Gamecast.
- **PASS if:** Scores increment when a scoring play arrives (TOUCHDOWN, FG, PAT).
- Note the current quarter displayed in the header.

### 5. Live Gamecast — drive panel

- Watch the drive panel (green field graphic).
- **PASS if:** Ball marker moves left/right as plays happen.
- **PASS if:** Drive play list below the field adds a new row on each play.
- **PASS if:** Drive list clears and resets on a possession change (look for turnover/punt/score).

### 6. Live Gamecast — stats panel

- Watch the right-hand stat panel (TeamLeaders widget + stat table).
- **PASS if:** Stats are not showing full final-game numbers on initial load (e.g. a QB with 280 yards when the game just started is a fail).
- **PASS if:** Stats increment as plays come in (rush yards, receiving yards grow).
- Note: stats refresh every 5 plays or on a scoring event — there will be a short lag.

### 7. Play log toggle

- Click "Scoring Plays" toggle on the Gamecast.
- **PASS if:** List filters to scoring plays only (TDs, FGs, PATs, Safeties).
- Click "All Plays" to restore.

### 8. Multi-game switch

- Open two Gamecast tabs for two different live games.
- Switch between them.
- **PASS if:** Both tabs continue streaming independently.
- **PASS if:** Drive panel and stats are correct for each game.

### 9. Game completion

- If a game completes while you are watching:
- **PASS if:** The Gamecast transitions to a complete view without a page reload.
- **PASS if:** Final score is shown in the header.
- **PASS if:** Complete play log is visible (all plays, no streaming delay).

### 10. Live leaders (schedule page)

- Return to the schedule page while live games are running.
- **PASS if:** A "Rush Leaders" and "Rec Leaders" section appears above the game grid.
- **PASS if:** Leaders show player last names, program emoji, and yard totals.
- **FAIL if:** Section is missing entirely when games are live.

---

## Output

Write findings to `roles/live-tester/output/output.md` using this structure:

```markdown
## Live Tester Report — <date> <time>

**Sim state:** Week N, X live games

### Passed
- [test name]: [one-line observation]

### Failed
- [test name]: [what was wrong — exact symptom, not diagnosis]

### Warnings
- [anything odd that didn't clearly pass or fail]

### Bugs to fix
[numbered list of concrete defects for the implementer — symptom only, no fix suggestion]
```

---

## Notes

- Do not diagnose root causes. Record what you see.
- Do not read source files to explain a failure. That is the implementer's job.
- If the sim is not running, restart it per `resources/dev-sim-guide.md` and note the restart in your report.
- Screenshot or log captures are optional but welcome in the output file.
