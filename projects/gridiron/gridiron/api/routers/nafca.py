from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from gridiron.api.schemas import NafcaLeaderboard, ProgramEloRank
from gridiron.database import get_db

router = APIRouter()

_ELO_RANK_QUERY = text("""
WITH first_game AS (
    SELECT program_id, pre_elo
    FROM (
        SELECT home_program_id AS program_id, home_elo_pre AS pre_elo,
               ROW_NUMBER() OVER (PARTITION BY home_program_id ORDER BY week ASC) AS rn
        FROM games WHERE season = 1 AND home_elo_pre IS NOT NULL
        UNION ALL
        SELECT away_program_id, away_elo_pre,
               ROW_NUMBER() OVER (PARTITION BY away_program_id ORDER BY week ASC) AS rn
        FROM games WHERE season = 1 AND away_elo_pre IS NOT NULL
    ) t WHERE rn = 1
)
SELECT p.id, p.name, p.emoji, p.conglomerate_id, p.tier, p.elo,
       COALESCE(fg.pre_elo, p.elo) AS pre_season_elo,
       p.elo - COALESCE(fg.pre_elo, p.elo) AS season_delta
FROM programs p
LEFT JOIN first_game fg ON fg.program_id = p.id
ORDER BY p.elo DESC
""")


@router.get("/nafca/leaderboard", response_model=NafcaLeaderboard)
async def nafca_leaderboard(db: AsyncSession = Depends(get_db)) -> NafcaLeaderboard:
    rows = (await db.execute(_ELO_RANK_QUERY)).mappings().all()
    programs = [ProgramEloRank.model_validate(dict(r)) for r in rows]
    lifetime = sorted(programs, key=lambda p: p.elo, reverse=True)
    season = sorted(programs, key=lambda p: p.season_delta, reverse=True)
    return NafcaLeaderboard(lifetime=lifetime, season=season)
