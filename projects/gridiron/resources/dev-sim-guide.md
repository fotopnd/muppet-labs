# Dev Sim Guide — Starting and Stopping

Working directory for all commands: `/Users/fotopnd/Documents/muppet-labs/projects/gridiron`

---

## Quick start — demo game (recommended for QA)

Streams a single fixed game (🏯 Reading vs 🌱 Savannah, game 153) from play 1.
Always use this for QA and live tester runs.

**Step 1 — reset the demo game:**
```zsh
uv run python3 -c "
from sqlalchemy import create_engine, text
from gridiron.config import settings
e = create_engine(settings.sync_database_url)
with e.connect() as c:
    c.execute(text(\"UPDATE games SET status='scheduled', replay_started_at=NULL WHERE id=153\"))
    c.commit()
    print('game 153 reset')
"
```

> Do NOT delete play_log — the API streams from existing play data.

**Step 2 — start both servers (two terminal tabs):**

Tab 1:
```zsh
uv run uvicorn gridiron.api.main:app --port 8006 --reload
```

Tab 2:
```zsh
cd web && pnpm dev --port 5177
```

**Step 3 — open the game:**
```
http://localhost:5177/games/153
```

Plays stream in every ~4 seconds. Game lasts ~10 minutes.
To replay: kill the API (Ctrl-C), run Step 1, restart the API.

---

## Full season sim (not needed for QA)

Remove `DEV_REPLAY_GAME_ID` from `.env` or set it to empty, then start both servers as above.
The orchestrator runs all weeks in sequence.

---

## Stop

Kill both servers with Ctrl-C in each tab.

Or kill by port:
```zsh
lsof -ti :8006 | xargs kill -9
lsof -ti :5177 | xargs kill -9
```

---

## Check which games are live

```zsh
curl -s http://localhost:8006/schedule/current | python3 -c "
import sys, json
d = json.load(sys.stdin)
live = [g for g in d['games'] if g['status']=='live']
print(f'Week {d[\"week\"]} — {len(live)} live games')
for g in live: print(f'  {g[\"game_id\"]:>4}  {g[\"home_emoji\"]} {g[\"home_name\"]} vs {g[\"away_emoji\"]} {g[\"away_name\"]}')
"
```

---

## Reset a stuck live game to complete

```zsh
uv run python3 -c "
from sqlalchemy import create_engine, text
from gridiron.config import settings
e = create_engine(settings.sync_database_url)
with e.connect() as c:
    r = c.execute(text(\"UPDATE games SET status='complete', replay_started_at=NULL WHERE status='live'\"))
    c.commit()
    print(f'reset {r.rowcount} games')
"
```

---

## Ports

| Service | Port |
|---|---|
| API (FastAPI) | 8006 |
| Web (Vite) | 5177 |
| Database (Postgres) | 5438 |
