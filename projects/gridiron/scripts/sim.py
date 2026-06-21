"""sim.py — dev/debug game runner.

Usage:
    uv run scripts/sim.py --game-id 1          # dry run, prints plays to stdout
    uv run scripts/sim.py --game-id 1 --db     # writes to DB
    uv run scripts/sim.py --week 1             # full week slate, writes to DB
"""
from __future__ import annotations

import argparse
import sys
import time

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from gridiron.config import settings
from gridiron.engine.game import GameEngine, GameResult


def run_game(game_id: int, write_db: bool) -> GameResult:
    engine = create_engine(settings.sync_database_url)
    with Session(engine) as session:
        conn = session.connection()
        if not write_db:
            # ponytail: savepoint lets us roll back without aborting the connection
            conn.execute(text("SAVEPOINT sim_dry_run"))
        result = GameEngine(game_id, conn).run()
        if write_db:
            session.commit()
        if not write_db:
            conn.execute(text("ROLLBACK TO SAVEPOINT sim_dry_run"))
            print(f"[dry-run] game {game_id}: {result.final_score_home}–{result.final_score_away} "
                  f"({result.play_count} plays)")
            # Print last 10 plays from in-memory list
            rows = conn.execute(
                text("SELECT play_number, play_type, description FROM play_log "
                     "WHERE game_id=:gid ORDER BY play_number"),
                {"gid": game_id},
            ).fetchall()
            for r in rows[-15:]:
                print(f"  {r[0]:>3}  {r[1]:<28}  {r[2]}")
        return result


def run_week(week: int) -> None:
    engine = create_engine(settings.sync_database_url)
    with Session(engine) as session:
        conn = session.connection()
        game_ids = [
            r[0] for r in conn.execute(
                text("SELECT id FROM games WHERE week=:w AND status='scheduled' ORDER BY id"),
                {"w": week},
            ).fetchall()
        ]
    if not game_ids:
        print(f"No scheduled games found for week {week}.")
        sys.exit(1)

    print(f"Week {week}: {len(game_ids)} games")
    t0 = time.perf_counter()
    for gid in game_ids:
        engine2 = create_engine(settings.sync_database_url)
        with Session(engine2) as session:
            conn = session.connection()
            result = GameEngine(gid, conn).run()
            session.commit()
            print(f"  game {gid}: {result.final_score_home}–{result.final_score_away} "
                  f"({result.play_count} plays)")
    elapsed = time.perf_counter() - t0
    print(f"Done in {elapsed:.1f}s")


def main() -> None:
    parser = argparse.ArgumentParser(description="Gridiron sim runner")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--game-id", type=int)
    group.add_argument("--week", type=int)
    parser.add_argument("--db", action="store_true", help="Write to DB (game-id mode only)")
    args = parser.parse_args()

    if args.game_id:
        run_game(args.game_id, args.db)
    else:
        run_week(args.week)


if __name__ == "__main__":
    main()
