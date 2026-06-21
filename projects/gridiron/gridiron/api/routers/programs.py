from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from gridiron.api.schemas import (
    PlayerRoster,
    ProgramDetail,
    ProgramScheduleGame,
    ProgramStats,
    ProgramSummary,
    StatLeader,
)
from gridiron.database import get_db

router = APIRouter()

_WL_CTE = """
WITH wl AS (
    SELECT home_program_id AS pid,
           (home_score > away_score)::int AS won,
           (home_score < away_score)::int AS lost
    FROM games WHERE status='complete' AND season=1
    UNION ALL
    SELECT away_program_id,
           (away_score > home_score)::int,
           (away_score < home_score)::int
    FROM games WHERE status='complete' AND season=1
), wl_agg AS (
    SELECT pid, SUM(won)::int AS wins, SUM(lost)::int AS losses FROM wl GROUP BY pid
)
"""

_STAT_QUERY = """
    SELECT pl.id AS player_id,
           pl.first_name || ' ' || pl.last_name AS name,
           SUM(pgs.{yards})::int AS total_yards,
           SUM(pgs.{tds})::int AS tds,
           COUNT(DISTINCT pgs.game_id)::int AS games_played
    FROM player_game_stats pgs
    JOIN players pl ON pl.id = pgs.player_id
    JOIN games g ON g.id = pgs.game_id
    WHERE pgs.program_id = :pid AND g.season = 1 AND g.status = 'complete'
    GROUP BY pl.id, pl.first_name, pl.last_name
    ORDER BY total_yards DESC
    LIMIT 5
"""


@router.get("/programs", response_model=list[ProgramSummary])
async def list_programs(db: AsyncSession = Depends(get_db)) -> list[ProgramSummary]:
    rows = (
        (
            await db.execute(
                text(f"""
        {_WL_CTE}
        SELECT p.id, p.name, p.emoji, p.city, p.tier, p.elo,
               c.code AS conglomerate_code,
               COALESCE(wl_agg.wins, 0) AS wins,
               COALESCE(wl_agg.losses, 0) AS losses
        FROM programs p
        JOIN conglomerates c ON c.id = p.conglomerate_id
        LEFT JOIN wl_agg ON wl_agg.pid = p.id
        ORDER BY p.elo DESC
    """)
            )
        )
        .mappings()
        .all()
    )
    return [ProgramSummary.model_validate(dict(r)) for r in rows]


@router.get("/programs/{program_id}", response_model=ProgramDetail)
async def get_program(
    program_id: int,
    db: AsyncSession = Depends(get_db),
) -> ProgramDetail:
    row = (
        (
            await db.execute(
                text(f"""
        {_WL_CTE}
        SELECT p.id, p.name, p.emoji, p.city, p.mascot, p.tier, p.elo,
               p.primary_color, p.secondary_color, p.conglomerate_id,
               c.code AS conglomerate_code,
               COALESCE(wl_agg.wins, 0) AS wins,
               COALESCE(wl_agg.losses, 0) AS losses
        FROM programs p
        JOIN conglomerates c ON c.id = p.conglomerate_id
        LEFT JOIN wl_agg ON wl_agg.pid = p.id
        WHERE p.id = :pid
    """),
                {"pid": program_id},
            )
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Program not found")
    return ProgramDetail.model_validate(dict(row))


@router.get("/programs/{program_id}/schedule", response_model=list[ProgramScheduleGame])
async def program_schedule(
    program_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[ProgramScheduleGame]:
    exists = (
        await db.execute(text("SELECT 1 FROM programs WHERE id = :pid"), {"pid": program_id})
    ).scalar()
    if not exists:
        raise HTTPException(status_code=404, detail="Program not found")

    rows = (
        (
            await db.execute(
                text("""
        SELECT g.id AS game_id, g.week, g.broadcast_slot, g.status,
               g.home_score, g.away_score,
               (g.home_program_id = :pid) AS is_home,
               opp.name AS opponent_name, opp.emoji AS opponent_emoji
        FROM games g
        JOIN programs opp ON opp.id =
            CASE WHEN g.home_program_id = :pid
                 THEN g.away_program_id ELSE g.home_program_id END
        WHERE (g.home_program_id = :pid OR g.away_program_id = :pid)
          AND g.season = 1
        ORDER BY g.week
    """),
                {"pid": program_id},
            )
        )
        .mappings()
        .all()
    )
    return [ProgramScheduleGame.model_validate(dict(r)) for r in rows]


@router.get("/programs/{program_id}/roster", response_model=list[PlayerRoster])
async def program_roster(
    program_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[PlayerRoster]:
    exists = (
        await db.execute(text("SELECT 1 FROM programs WHERE id = :pid"), {"pid": program_id})
    ).scalar()
    if not exists:
        raise HTTPException(status_code=404, detail="Program not found")

    rows = (
        (
            await db.execute(
                text("""
        SELECT id AS player_id, first_name, last_name, position, year, jersey_num
        FROM players
        WHERE program_id = :pid
        ORDER BY position, jersey_num
    """),
                {"pid": program_id},
            )
        )
        .mappings()
        .all()
    )
    return [PlayerRoster.model_validate(dict(r)) for r in rows]


@router.get("/programs/{program_id}/stats", response_model=ProgramStats)
async def program_stats(
    program_id: int,
    db: AsyncSession = Depends(get_db),
) -> ProgramStats:
    exists = (
        await db.execute(text("SELECT 1 FROM programs WHERE id = :pid"), {"pid": program_id})
    ).scalar()
    if not exists:
        raise HTTPException(status_code=404, detail="Program not found")

    p = {"pid": program_id}

    async def _top(yards: str, tds: str) -> list[StatLeader]:
        rows = (
            (await db.execute(text(_STAT_QUERY.format(yards=yards, tds=tds)), p)).mappings().all()
        )
        return [StatLeader.model_validate(dict(r)) for r in rows]

    passers = await _top("pass_yards", "pass_tds")
    rushers = await _top("rush_yards", "rush_tds")
    receivers = await _top("receiving_yards", "receiving_tds")
    return ProgramStats(passers=passers, rushers=rushers, receivers=receivers)
