"""
Sandbox simulation runner — gridiron-sim-tuner role.

Hard isolation contract:
- Never imports gridiron.database, gridiron.config, or gridiron.api
- Never connects to PostgreSQL
- Never touches app.state or SSE infrastructure
- Reads from gridiron.engine only
- Writes to scripts/sandbox.db (SQLite) and roles/sim-tuner/output/output.md
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

SANDBOX_DB = Path(__file__).parent / "sandbox.db"
OUTPUT_MD = Path(__file__).parent.parent / "roles" / "sim-tuner" / "output" / "output.md"

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS games (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    season      INTEGER NOT NULL,
    week        INTEGER NOT NULL,
    home_team   TEXT NOT NULL,
    away_team   TEXT NOT NULL,
    home_score  INTEGER NOT NULL,
    away_score  INTEGER NOT NULL,
    home_elo    REAL NOT NULL,
    away_elo    REAL NOT NULL,
    window      TEXT NOT NULL DEFAULT 'regular',  -- regular | rivalry | postseason
    seed        INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS plays (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id     INTEGER NOT NULL REFERENCES games(id),
    play_type   TEXT NOT NULL,
    yards       INTEGER,
    is_scoring  INTEGER NOT NULL DEFAULT 0,
    is_turnover INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS elo_snapshots (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    season      INTEGER NOT NULL,
    team        TEXT NOT NULL,
    conglomerate TEXT NOT NULL,
    tier        INTEGER NOT NULL,
    elo         REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS promotions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    season        INTEGER NOT NULL,
    conglomerate  TEXT NOT NULL,
    team          TEXT NOT NULL,
    direction     TEXT NOT NULL  -- promoted | relegated
);
"""


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


# ---------------------------------------------------------------------------
# Engine import guard
# ---------------------------------------------------------------------------

def check_engine() -> str:
    """Confirm gridiron.engine is importable. Returns version string."""
    try:
        import gridiron.engine as engine  # noqa: F401
        version = getattr(engine, "__version__", "unknown")
        return version
    except ImportError as exc:
        print(f"ERROR: gridiron.engine is not importable: {exc}", file=sys.stderr)
        print("Engine has not been implemented yet. Stop here.", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Stub simulation — replaced once engine is implemented
# ---------------------------------------------------------------------------

def _run_seasons_stub(
    conn: sqlite3.Connection,
    n_seasons: int,
    seed: int,
    quiet: bool,
) -> None:
    """
    Placeholder that exercises the DB schema without a real engine.
    Remove this function once gridiron.engine is implemented.
    """
    import random
    rng = random.Random(seed)

    CONGLOMERATES = [f"Conglomerate {i}" for i in range(1, 6)]
    TEAMS = [f"Team_{c}_{i}" for c in range(1, 6) for i in range(1, 27)]
    PLAY_TYPES = [
        "RUSH", "RUSH", "RUSH",
        "PASS_COMPLETE", "PASS_COMPLETE", "PASS_INCOMPLETE",
        "PASS_DEFLECTION", "TOUCHDOWN", "TURNOVER_INTERCEPTION",
        "TURNOVER_FUMBLE", "SACK", "TACKLE_FOR_LOSS",
        "FIELD_GOAL_ATTEMPT", "PUNT", "KICKOFF", "PENALTY",
        "PAT_CONVERSION", "TWO_POINT_CONVERSION", "SAFETY",
    ]

    elo: dict[str, float] = {t: 1500.0 for t in TEAMS}

    for season in range(1, n_seasons + 1):
        if not quiet:
            print(f"  Season {season}/{n_seasons}...")

        # Regular season: 26 weeks × 60 games
        for week in range(1, 27):
            window = "rivalry" if week >= 25 else "regular"
            pairs = [(TEAMS[i], TEAMS[i + 1]) for i in range(0, min(120, len(TEAMS) - 1), 2)]
            for home, away in pairs:
                n_plays = rng.randint(120, 150)
                home_score = rng.randint(10, 45)
                away_score = rng.randint(10, 45)
                cur = conn.execute(
                    "INSERT INTO games (season, week, home_team, away_team, "
                    "home_score, away_score, home_elo, away_elo, window, seed) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (season, week, home, away, home_score, away_score,
                     elo[home], elo[away], window, seed),
                )
                game_id = cur.lastrowid
                for _ in range(n_plays):
                    pt = rng.choice(PLAY_TYPES)
                    conn.execute(
                        "INSERT INTO plays (game_id, play_type, yards, is_scoring, is_turnover) "
                        "VALUES (?,?,?,?,?)",
                        (game_id, pt, rng.randint(-5, 40),
                         1 if pt == "TOUCHDOWN" else 0,
                         1 if pt in ("TURNOVER_INTERCEPTION", "TURNOVER_FUMBLE") else 0),
                    )

        # Elo snapshots
        for t in TEAMS:
            c_idx = int(t.split("_")[1]) - 1
            tier = 1 if int(t.split("_")[2]) <= 13 else 2
            conn.execute(
                "INSERT INTO elo_snapshots (season, team, conglomerate, tier, elo) VALUES (?,?,?,?,?)",
                (season, t, CONGLOMERATES[c_idx], tier, elo[t] + rng.gauss(0, 30)),
            )

        # Boardroom Swap: bottom 2 Tier 1 ↔ top 2 Tier 2 per conglomerate
        for c in CONGLOMERATES:
            for direction in ("relegated", "promoted"):
                conn.execute(
                    "INSERT INTO promotions (season, conglomerate, team, direction) VALUES (?,?,?,?)",
                    (season, c, rng.choice(TEAMS), direction),
                )
                conn.execute(
                    "INSERT INTO promotions (season, conglomerate, team, direction) VALUES (?,?,?,?)",
                    (season, c, rng.choice(TEAMS), direction),
                )

        conn.commit()


# ---------------------------------------------------------------------------
# Real simulation dispatch — calls engine once it exists
# ---------------------------------------------------------------------------

def run_seasons(
    conn: sqlite3.Connection,
    n_seasons: int,
    seed: int,
    quiet: bool,
) -> None:
    try:
        from gridiron.engine import simulate_season  # type: ignore[import]
        for season in range(1, n_seasons + 1):
            if not quiet:
                print(f"  Season {season}/{n_seasons}...")
            simulate_season(conn=conn, season=season, seed=seed + season)
        conn.commit()
    except ImportError:
        if not quiet:
            print("  gridiron.engine.simulate_season not found — running stub simulation.")
        _run_seasons_stub(conn, n_seasons, seed, quiet)


# ---------------------------------------------------------------------------
# Analysis queries
# ---------------------------------------------------------------------------

def print_summary(conn: sqlite3.Connection) -> None:
    print("\n--- Score Distribution ---")
    rows = conn.execute("""
        SELECT
            season,
            COUNT(*) as games,
            ROUND(AVG(home_score + away_score), 1) as avg_total,
            ROUND(AVG(ABS(home_score - away_score)), 1) as avg_margin
        FROM games
        GROUP BY season ORDER BY season
    """).fetchall()
    print(f"{'Season':>6}  {'Games':>6}  {'Avg Total':>10}  {'Avg Margin':>10}")
    for r in rows:
        print(f"{r[0]:>6}  {r[1]:>6}  {r[2]:>10}  {r[3]:>10}")

    print("\n--- Play Type Mix (non-ST) ---")
    total = conn.execute(
        "SELECT COUNT(*) FROM plays WHERE play_type NOT IN ('KICKOFF','PUNT')"
    ).fetchone()[0]
    rush = conn.execute(
        "SELECT COUNT(*) FROM plays WHERE play_type = 'RUSH'"
    ).fetchone()[0]
    pass_plays = conn.execute(
        "SELECT COUNT(*) FROM plays WHERE play_type IN "
        "('PASS_COMPLETE','PASS_INCOMPLETE','PASS_DEFLECTION')"
    ).fetchone()[0]
    turnovers = conn.execute(
        "SELECT COUNT(*) FROM plays WHERE is_turnover = 1"
    ).fetchone()[0]
    games_total = conn.execute("SELECT COUNT(*) FROM games").fetchone()[0]
    if total and games_total:
        print(f"  Rush:     {rush / total * 100:.1f}%  (target 40–50%)")
        print(f"  Pass:     {pass_plays / total * 100:.1f}%  (target 50–60%)")
        print(f"  Turnovers/game: {turnovers / games_total:.2f}  (target 2.0–3.5)")

    print("\n--- Elo Health ---")
    rows = conn.execute("""
        SELECT season,
               ROUND(MAX(elo) - MIN(elo), 1) as spread
        FROM elo_snapshots GROUP BY season ORDER BY season
    """).fetchall()
    for r in rows:
        flag = "✓" if r[1] > 200 else "✗"
        print(f"  Season {r[0]}: spread {r[1]}  {flag}")

    print("\n--- Boardroom Swap ---")
    rows = conn.execute("""
        SELECT season, conglomerate, COUNT(*) as n
        FROM promotions WHERE direction = 'relegated'
        GROUP BY season, conglomerate ORDER BY season, conglomerate
    """).fetchall()
    for r in rows:
        flag = "✓" if r[2] == 2 else "✗"
        print(f"  Season {r[0]} {r[1]}: {r[2]} relegated  {flag}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gridiron sandbox simulation runner (no production dependencies)"
    )
    parser.add_argument("--check", action="store_true",
                        help="Confirm engine is importable then exit")
    parser.add_argument("--seasons", type=int, default=1,
                        help="Number of seasons to simulate (default: 1)")
    parser.add_argument("--seed", type=int, default=42,
                        help="RNG seed for reproducibility (default: 42)")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress per-season progress output")
    parser.add_argument("--reset", action="store_true",
                        help="Drop and recreate sandbox.db before running")
    args = parser.parse_args()

    if args.check:
        version = check_engine()
        print(f"gridiron.engine OK — version: {version}")
        sys.exit(0)

    if args.reset and SANDBOX_DB.exists():
        SANDBOX_DB.unlink()
        print(f"Cleared {SANDBOX_DB}")

    conn = sqlite3.connect(SANDBOX_DB)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    init_db(conn)

    if not args.quiet:
        print(f"Sandbox DB: {SANDBOX_DB}")
        print(f"Running {args.seasons} season(s) with seed={args.seed}...")

    run_seasons(conn, args.seasons, args.seed, args.quiet)

    if not args.quiet:
        print_summary(conn)
        print(f"\nDone. Query further with: sqlite3 {SANDBOX_DB}")

    conn.close()


if __name__ == "__main__":
    main()
