from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from gridiron.config import EMIT_INTERVAL
from gridiron.api.schemas import LeaderboardEntry, Leaderboards, LiveLeader, LiveLeaders
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


_LIVE_LEADER_QUERY = text("""
    SELECT pl.id AS player_id, pl.last_name AS name,
           pr.name AS program_name, pr.emoji AS program_emoji,
           pll.game_id,
           SUM(COALESCE(pll.yards_gained, 0))::int AS yards
    FROM play_log pll
    JOIN players pl ON pl.id = pll.primary_player_id
    JOIN programs pr ON pr.id = pl.program_id
    JOIN games g ON g.id = pll.game_id
    WHERE g.status = 'live'
      AND g.replay_started_at IS NOT NULL
      AND pll.play_type = :play_type
      AND pll.play_number <= FLOOR(
            EXTRACT(EPOCH FROM (NOW() - g.replay_started_at)) / :emit_interval
          )::int
    GROUP BY pl.id, pl.last_name, pr.name, pr.emoji, pll.game_id
    ORDER BY yards DESC
    LIMIT 5
""")


@router.get("/live/leaders", response_model=LiveLeaders)
async def live_leaders(db: AsyncSession = Depends(get_db)) -> LiveLeaders:
    p = {"emit_interval": EMIT_INTERVAL}

    async def _live_top(play_type: str) -> list[LiveLeader]:
        rows = (await db.execute(_LIVE_LEADER_QUERY, {**p, "play_type": play_type})).mappings().all()
        return [LiveLeader.model_validate(dict(r)) for r in rows]

    rushers = await _live_top("RUSH")
    receivers = await _live_top("PASS_COMPLETE")
    # Passing: credit PASS_COMPLETE yards to receivers here; QB approximation done client-side
    # ponytail: passers = receivers re-keyed would be wrong; skip QB pass leaders in v1
    return LiveLeaders(passers=[], rushers=rushers, receivers=receivers)
