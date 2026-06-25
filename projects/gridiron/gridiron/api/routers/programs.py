from __future__ import annotations

import random

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from gridiron.api.schemas import (
    PlayerDetail,
    PlayerRoster,
    ProgramCoach,
    ProgramDetail,
    ProgramScheduleGame,
    ProgramStats,
    ProgramSummary,
    StatLeader,
)
from gridiron.database import get_db

_TOWNS = [
    ("Springfield", "IL"), ("Columbus", "OH"), ("Memphis", "TN"), ("Richmond", "VA"),
    ("Baton Rouge", "LA"), ("Tulsa", "OK"), ("Fresno", "CA"), ("Omaha", "NE"),
    ("Raleigh", "NC"), ("Mesa", "AZ"), ("Bakersfield", "CA"), ("Tampa", "FL"),
    ("Aurora", "CO"), ("Corpus Christi", "TX"), ("Lexington", "KY"), ("St. Paul", "MN"),
    ("Pittsburgh", "PA"), ("Stockton", "CA"), ("Cincinnati", "OH"), ("St. Louis", "MO"),
    ("Toledo", "OH"), ("Greensboro", "NC"), ("Newark", "NJ"), ("Plano", "TX"),
    ("Henderson", "NV"), ("Lincoln", "NE"), ("Buffalo", "NY"), ("Fort Wayne", "IN"),
    ("Orlando", "FL"), ("St. Petersburg", "FL"), ("Norfolk", "VA"), ("Laredo", "TX"),
    ("Madison", "WI"), ("Durham", "NC"), ("Lubbock", "TX"), ("Garland", "TX"),
    ("Glendale", "AZ"), ("Hialeah", "FL"), ("Reno", "NV"), ("Irvine", "CA"),
    ("Chesapeake", "VA"), ("Scottsdale", "AZ"), ("Fremont", "CA"), ("Gilbert", "AZ"),
    ("San Bernardino", "CA"), ("Boise", "ID"), ("Birmingham", "AL"), ("Rochester", "NY"),
    ("Spokane", "WA"), ("Des Moines", "IA"), ("Montgomery", "AL"), ("Modesto", "CA"),
    ("Fayetteville", "NC"), ("Tacoma", "WA"), ("Shreveport", "LA"), ("Akron", "OH"),
    ("Huntington Beach", "CA"), ("Little Rock", "AR"), ("Augusta", "GA"),
    ("Grand Rapids", "MI"), ("Salt Lake City", "UT"), ("Tallahassee", "FL"),
    ("Huntsville", "AL"), ("Worcester", "MA"), ("Knoxville", "TN"), ("Providence", "RI"),
    ("Brownsville", "TX"), ("Newport News", "VA"), ("Fort Lauderdale", "FL"),
    ("Mobile", "AL"), ("Chattanooga", "TN"), ("Tempe", "AZ"), ("Eugene", "OR"),
    ("Vancouver", "WA"), ("Peoria", "IL"), ("Salem", "OR"), ("Fort Collins", "CO"),
    ("McKinney", "TX"), ("Clarksville", "TN"), ("Killeen", "TX"), ("Cedar Rapids", "IA"),
]

_HEIGHT: dict[str, tuple[int, int]] = {
    "QB": (72, 77), "WR": (70, 76), "RB": (68, 73), "TE": (74, 78),
    "OL": (74, 78), "DL": (73, 78), "LB": (71, 75), "DB": (69, 74),
    "S": (69, 74), "CB": (69, 74), "K": (70, 75), "P": (70, 75),
}
_WEIGHT: dict[str, tuple[int, int]] = {
    "QB": (205, 235), "WR": (170, 210), "RB": (185, 225), "TE": (235, 265),
    "OL": (280, 330), "DL": (270, 325), "LB": (225, 255), "DB": (185, 210),
    "S": (190, 215), "CB": (180, 205), "K": (175, 210), "P": (175, 210),
}


def _generate_bio(player_id: int, position: str) -> dict:
    rng = random.Random(player_id * 31337)
    h_lo, h_hi = _HEIGHT.get(position, (70, 76))
    w_lo, w_hi = _WEIGHT.get(position, (190, 220))
    total_in = rng.randint(h_lo, h_hi)
    hometown, state = _TOWNS[rng.randrange(len(_TOWNS))]
    return {
        "height_ft": total_in // 12,
        "height_in": total_in % 12,
        "weight_lbs": rng.randint(w_lo, w_hi),
        "hometown": hometown,
        "state": state,
    }

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


@router.get("/programs/{program_id}/coaches", response_model=list[ProgramCoach])
async def program_coaches(
    program_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[ProgramCoach]:
    exists = (
        await db.execute(text("SELECT 1 FROM programs WHERE id = :pid"), {"pid": program_id})
    ).scalar()
    if not exists:
        raise HTTPException(status_code=404, detail="Program not found")

    rows = (
        (
            await db.execute(
                text("""
        SELECT id AS coach_id, first_name, last_name,
               first_name || ' ' || last_name AS full_name, role, rating, prestige
        FROM coaches
        WHERE program_id = :pid
        ORDER BY role
    """),
                {"pid": program_id},
            )
        )
        .mappings()
        .all()
    )
    return [ProgramCoach.model_validate(dict(r)) for r in rows]


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


@router.get("/players/{player_id}", response_model=PlayerDetail)
async def get_player(player_id: int, db: AsyncSession = Depends(get_db)) -> PlayerDetail:
    row = (
        await db.execute(
            text("""
        SELECT pl.id AS player_id, pl.first_name, pl.last_name, pl.position,
               pl.year, pl.jersey_num, pl.program_id,
               pr.name AS program_name, pr.emoji AS program_emoji,
               c.code AS conglomerate_code,
               COALESCE(st.pass_attempts, 0)    AS pass_attempts,
               COALESCE(st.pass_completions, 0) AS pass_completions,
               COALESCE(st.pass_yards, 0)       AS pass_yards,
               COALESCE(st.pass_tds, 0)         AS pass_tds,
               COALESCE(st.interceptions, 0)    AS interceptions,
               COALESCE(st.rush_attempts, 0)    AS rush_attempts,
               COALESCE(st.rush_yards, 0)       AS rush_yards,
               COALESCE(st.rush_tds, 0)         AS rush_tds,
               COALESCE(st.targets, 0)          AS targets,
               COALESCE(st.receptions, 0)       AS receptions,
               COALESCE(st.receiving_yards, 0)  AS receiving_yards,
               COALESCE(st.receiving_tds, 0)    AS receiving_tds,
               COALESCE(st.tackles, 0)          AS tackles,
               COALESCE(st.sacks, 0)            AS sacks,
               COALESCE(st.ints_def, 0)         AS ints_def,
               COALESCE(st.forced_fumbles, 0)   AS forced_fumbles,
               COALESCE(st.fg_attempts, 0)      AS fg_attempts,
               COALESCE(st.fg_made, 0)          AS fg_made,
               COALESCE(st.games_played, 0)     AS games_played
        FROM players pl
        JOIN programs pr ON pr.id = pl.program_id
        JOIN conglomerates c ON c.id = pr.conglomerate_id
        LEFT JOIN (
            SELECT pgs.player_id,
                   SUM(pgs.pass_attempts)::int    AS pass_attempts,
                   SUM(pgs.pass_completions)::int AS pass_completions,
                   SUM(pgs.pass_yards)::int       AS pass_yards,
                   SUM(pgs.pass_tds)::int         AS pass_tds,
                   SUM(pgs.interceptions)::int    AS interceptions,
                   SUM(pgs.rush_attempts)::int    AS rush_attempts,
                   SUM(pgs.rush_yards)::int       AS rush_yards,
                   SUM(pgs.rush_tds)::int         AS rush_tds,
                   SUM(pgs.targets)::int          AS targets,
                   SUM(pgs.receptions)::int       AS receptions,
                   SUM(pgs.receiving_yards)::int  AS receiving_yards,
                   SUM(pgs.receiving_tds)::int    AS receiving_tds,
                   SUM(pgs.tackles)::int          AS tackles,
                   SUM(pgs.sacks)::int            AS sacks,
                   SUM(pgs.ints_def)::int         AS ints_def,
                   SUM(pgs.forced_fumbles)::int   AS forced_fumbles,
                   SUM(pgs.fg_attempts)::int      AS fg_attempts,
                   SUM(pgs.fg_made)::int          AS fg_made,
                   COUNT(DISTINCT pgs.game_id)::int AS games_played
            FROM player_game_stats pgs
            JOIN games g ON g.id = pgs.game_id
            WHERE g.season = 1 AND g.status = 'complete'
            GROUP BY pgs.player_id
        ) st ON st.player_id = pl.id
        WHERE pl.id = :pid
    """),
            {"pid": player_id},
        )
    ).mappings().one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Player not found")
    d = dict(row)
    d.update(_generate_bio(player_id, d["position"]))
    return PlayerDetail.model_validate(d)
