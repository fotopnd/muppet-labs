from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from gridiron.api.schemas import LeaderboardEntry, Leaderboards
from gridiron.database import get_db

router = APIRouter()

_LEADER_QUERY = """
    SELECT pl.id AS player_id,
           pl.first_name || ' ' || pl.last_name AS name,
           pr.name AS program_name,
           SUM(pgs.{yards})::int AS total_yards,
           SUM(pgs.{tds})::int AS tds,
           COUNT(DISTINCT pgs.game_id)::int AS games_played
    FROM player_game_stats pgs
    JOIN players pl ON pl.id = pgs.player_id
    JOIN programs pr ON pr.id = pgs.program_id
    JOIN games g ON g.id = pgs.game_id
    WHERE g.season = :season AND g.status = 'complete'
    GROUP BY pl.id, pl.first_name, pl.last_name, pr.name
    ORDER BY total_yards DESC
    LIMIT 10
"""


@router.get("/leaderboards", response_model=Leaderboards)
async def leaderboards(
    season: int = Query(default=1),
    db: AsyncSession = Depends(get_db),
) -> Leaderboards:
    p = {"season": season}

    async def _top(yards: str, tds: str) -> list[LeaderboardEntry]:
        rows = (
            (await db.execute(text(_LEADER_QUERY.format(yards=yards, tds=tds)), p)).mappings().all()
        )
        return [LeaderboardEntry.model_validate(dict(r)) for r in rows]

    passers = await _top("pass_yards", "pass_tds")
    rushers = await _top("rush_yards", "rush_tds")
    receivers = await _top("receiving_yards", "receiving_tds")
    return Leaderboards(passers=passers, rushers=rushers, receivers=receivers)
