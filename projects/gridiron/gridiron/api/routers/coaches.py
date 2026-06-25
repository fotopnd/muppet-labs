from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from gridiron.api.schemas import CoachDetail, CoachSeasonRow
from gridiron.database import get_db

router = APIRouter()


@router.get("/coaches/{coach_id}", response_model=CoachDetail)
async def get_coach(coach_id: int, db: AsyncSession = Depends(get_db)) -> CoachDetail:
    coach_row = (
        await db.execute(
            text("""
        SELECT c.id AS coach_id, c.first_name, c.last_name, c.role, c.rating,
               c.run_tendency, c.style, c.prestige,
               c.program_id, p.name AS program_name, p.emoji AS program_emoji,
               cg.code AS conglomerate_code
        FROM coaches c
        JOIN programs p ON p.id = c.program_id
        JOIN conglomerates cg ON cg.id = p.conglomerate_id
        WHERE c.id = :cid
    """),
            {"cid": coach_id},
        )
    ).mappings().one_or_none()

    if coach_row is None:
        raise HTTPException(status_code=404, detail="Coach not found")

    pid = coach_row["program_id"]

    season_rows = (
        await db.execute(
            text("""
        WITH coach_games AS (
            SELECT g.id AS game_id, g.season,
                   CASE WHEN g.home_program_id = :pid THEN 'home' ELSE 'away' END AS team_side,
                   CASE WHEN (g.home_program_id=:pid AND g.home_score > g.away_score)
                             OR (g.away_program_id=:pid AND g.away_score > g.home_score)
                        THEN 1 ELSE 0 END AS won,
                   CASE WHEN (g.home_program_id=:pid AND g.home_score < g.away_score)
                             OR (g.away_program_id=:pid AND g.away_score < g.home_score)
                        THEN 1 ELSE 0 END AS lost
            FROM games g
            WHERE (g.home_program_id = :pid OR g.away_program_id = :pid)
              AND g.status = 'complete'
        ),
        wl AS (
            SELECT season,
                   SUM(won)::int AS wins,
                   SUM(lost)::int AS losses,
                   COUNT(*)::int AS games_played
            FROM coach_games GROUP BY season
        ),
        play_stats AS (
            SELECT cg.season,
                COALESCE(SUM(CASE
                    WHEN pl.possession = cg.team_side
                      AND pl.play_type IN (
                          'RUSH','PASS_COMPLETE','TACKLE_FOR_LOSS','SACK','TOUCHDOWN'
                      ) THEN pl.yards_gained ELSE 0 END), 0)::int AS off_yards,
                COALESCE(SUM(CASE
                    WHEN pl.possession = cg.team_side AND pl.play_type = 'PASS_COMPLETE'
                    THEN pl.yards_gained ELSE 0 END), 0)::int AS pass_yards,
                COALESCE(SUM(CASE
                    WHEN pl.possession = cg.team_side
                      AND pl.play_type IN ('RUSH', 'TACKLE_FOR_LOSS')
                    THEN pl.yards_gained ELSE 0 END), 0)::int AS rush_yards,
                COALESCE(SUM(CASE
                    WHEN pl.possession != cg.team_side
                      AND pl.play_type IN (
                          'RUSH','PASS_COMPLETE','TACKLE_FOR_LOSS','SACK','TOUCHDOWN'
                      ) THEN pl.yards_gained ELSE 0 END), 0)::int AS def_yards_allowed,
                COUNT(CASE WHEN pl.possession != cg.team_side
                    AND pl.play_type = 'SACK' THEN 1 END)::int AS sacks,
                COUNT(CASE WHEN pl.possession != cg.team_side
                    AND pl.play_type = 'TURNOVER_INTERCEPTION' THEN 1 END)::int AS interceptions
            FROM coach_games cg
            LEFT JOIN play_log pl ON pl.game_id = cg.game_id
            GROUP BY cg.season
        ),
        points_cte AS (
            SELECT cg.season,
                SUM(CASE WHEN cg.team_side = 'home' THEN g.home_score ELSE g.away_score END)::int AS points_scored,
                SUM(CASE WHEN cg.team_side = 'home' THEN g.away_score ELSE g.home_score END)::int AS points_allowed
            FROM coach_games cg
            JOIN games g ON g.id = cg.game_id
            GROUP BY cg.season
        )
        SELECT wl.season, wl.wins, wl.losses, wl.games_played,
               ps.off_yards, ps.pass_yards, ps.rush_yards,
               ps.def_yards_allowed, ps.sacks, ps.interceptions,
               COALESCE(pt.points_scored, 0) AS points_scored,
               COALESCE(pt.points_allowed, 0) AS points_allowed
        FROM wl
        LEFT JOIN play_stats ps ON ps.season = wl.season
        LEFT JOIN points_cte pt ON pt.season = wl.season
        ORDER BY wl.season
    """),
            {"pid": pid},
        )
    ).mappings().all()

    seasons = [
        CoachSeasonRow(
            season=r["season"],
            program_name=coach_row["program_name"],
            program_emoji=coach_row["program_emoji"],
            wins=r["wins"],
            losses=r["losses"],
            win_pct=round(r["wins"] / r["games_played"], 3) if r["games_played"] else 0.0,
            off_yards=r["off_yards"],
            pass_yards=r["pass_yards"],
            rush_yards=r["rush_yards"],
            def_yards_allowed=r["def_yards_allowed"],
            sacks=r["sacks"],
            interceptions=r["interceptions"],
            games_played=r["games_played"],
            points_scored=r["points_scored"],
            points_allowed=r["points_allowed"],
        )
        for r in season_rows
    ]

    return CoachDetail(
        coach_id=coach_row["coach_id"],
        first_name=coach_row["first_name"],
        last_name=coach_row["last_name"],
        role=coach_row["role"],
        rating=coach_row["rating"],
        run_tendency=coach_row["run_tendency"],
        style=coach_row["style"],
        prestige=coach_row["prestige"],
        program_id=coach_row["program_id"],
        program_name=coach_row["program_name"],
        program_emoji=coach_row["program_emoji"],
        conglomerate_code=coach_row["conglomerate_code"],
        seasons=seasons,
    )
