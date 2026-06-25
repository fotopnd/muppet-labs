"""assign_broadcast_slots.py — assign broadcast_slot to all season-1 games.

Usage:
    uv run scripts/assign_broadcast_slots.py
    uv run scripts/assign_broadcast_slots.py --dry-run

Rules (from sim-engine brief):
    prestige scale is 1–5; threshold 4+ = "high prestige" (≈ Tier 1 marquee)
    prime_time: max 5/week, 1 per conglomerate
    Tier 1 + high prestige: eligible for afternoon/prime_time
    Tier 1 + low prestige:  eligible for noon/afternoon/prime_time
    Tier 2 involved:        noon or late_night
    Rivalry wk 25-26 Tier1: afternoon/prime_time
    Rivalry wk 25-26 Tier2: noon/afternoon
    Postseason:             prime_time
"""
from __future__ import annotations

import argparse
import random
from collections import defaultdict

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from gridiron.config import settings

HIGH_PRESTIGE_THRESHOLD = 4  # ponytail: 1-5 scale; 4+ = marquee matchup
PRIME_TIME_PER_WEEK = 5
RIVALRY_WEEKS = {25, 26}


def _eligible_slots(game: dict, prime_count: int, prime_congloms: set[int]) -> list[str]:
    """Return eligible slots for a game, in priority order."""
    w = game["week"]
    is_postseason = game["is_postseason"]
    is_rivalry = game["is_rivalry"]
    both_tier1 = game["home_tier"] == 1 and game["away_tier"] == 1
    high_prestige = max(game["home_prestige"], game["away_prestige"]) >= HIGH_PRESTIGE_THRESHOLD
    congloms = {game["home_cong"], game["away_cong"]}
    prime_available = prime_count < PRIME_TIME_PER_WEEK and congloms.isdisjoint(prime_congloms)

    if is_postseason:
        return ["prime_time", "afternoon"] if prime_available else ["afternoon"]

    if is_rivalry and w in RIVALRY_WEEKS:
        if both_tier1:
            return (["prime_time", "afternoon"] if prime_available else ["afternoon"])
        else:
            return ["noon", "afternoon"]

    if both_tier1 and high_prestige:
        if prime_available:
            return ["prime_time", "afternoon"]
        return ["afternoon"]

    if both_tier1:
        if prime_available:
            return ["prime_time", "afternoon", "noon"]
        return ["afternoon", "noon"]

    # Tier 2 involved — spread ~1/3 to late_night (deterministic via game id)
    if game["id"] % 3 == 0:
        return ["late_night", "noon"]
    return ["noon", "late_night"]


def assign_slots(games: list[dict]) -> dict[int, str]:
    """Return {game_id: slot} for all games."""
    by_week: dict[int, list[dict]] = defaultdict(list)
    for g in games:
        by_week[g["week"]].append(g)

    result: dict[int, str] = {}

    for week in sorted(by_week):
        prime_count = 0
        prime_congloms: set[int] = set()

        # Priority sort: postseason > rivalry > tier1 high prestige > tier1 > tier2
        def priority(g: dict) -> int:
            if g["is_postseason"]:
                return 0
            if g["is_rivalry"]:
                return 1
            if g["home_tier"] == 1 and g["away_tier"] == 1:
                return 2 if max(g["home_prestige"], g["away_prestige"]) >= HIGH_PRESTIGE_THRESHOLD else 3
            return 4

        for game in sorted(by_week[week], key=priority):
            slots = _eligible_slots(game, prime_count, prime_congloms)
            slot = slots[0]
            if slot == "prime_time":
                prime_count += 1
                prime_congloms.update({game["home_cong"], game["away_cong"]})
            result[game["id"]] = slot

    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    engine = create_engine(settings.sync_database_url)
    with Session(engine) as session:
        conn = session.connection()
        rows = conn.execute(text("""
            SELECT
                g.id, g.week, g.is_rivalry, g.is_postseason,
                hp.tier  AS home_tier,  hp.prestige AS home_prestige, hp.conglomerate_id AS home_cong,
                ap.tier  AS away_tier,  ap.prestige AS away_prestige, ap.conglomerate_id AS away_cong
            FROM games g
            JOIN programs hp ON hp.id = g.home_program_id
            JOIN programs ap ON ap.id = g.away_program_id
            WHERE g.season = 1
            ORDER BY g.week, g.id
        """)).fetchall()

        games = [dict(r._mapping) for r in rows]
        slots = assign_slots(games)

        # Tally for reporting
        tally: dict[str, int] = defaultdict(int)
        for s in slots.values():
            tally[s] += 1

        print(f"Total games: {len(slots)}")
        for s in ["noon", "afternoon", "prime_time", "late_night"]:
            print(f"  {s:<14}: {tally.get(s, 0)}")

        if args.dry_run:
            print("Dry run — no DB writes.")
            return

        for game_id, slot in slots.items():
            conn.execute(
                text("UPDATE games SET broadcast_slot=:s WHERE id=:id"),
                {"s": slot, "id": game_id},
            )
        session.commit()
        print("Done.")


if __name__ == "__main__":
    main()
