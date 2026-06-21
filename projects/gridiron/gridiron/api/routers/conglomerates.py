from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from gridiron.api.schemas import ConglomerateOut, ConglomerateStandings, ProgramStanding
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


@router.get("/conglomerates", response_model=list[ConglomerateOut])
async def list_conglomerates(db: AsyncSession = Depends(get_db)) -> list[ConglomerateOut]:
    rows = (
        (
            await db.execute(
                text(
                    "SELECT id, code, full_name, network, region, primary_color, secondary_color "
                    "FROM conglomerates ORDER BY id"
                )
            )
        )
        .mappings()
        .all()
    )
    return [ConglomerateOut.model_validate(dict(r)) for r in rows]


@router.get("/conglomerates/{conglomerate_id}/standings", response_model=ConglomerateStandings)
async def conglomerate_standings(
    conglomerate_id: int,
    db: AsyncSession = Depends(get_db),
) -> ConglomerateStandings:
    cong_row = (
        (
            await db.execute(
                text(
                    "SELECT id, code, full_name, network, region, primary_color, secondary_color "
                    "FROM conglomerates WHERE id = :cid"
                ),
                {"cid": conglomerate_id},
            )
        )
        .mappings()
        .one_or_none()
    )
    if cong_row is None:
        raise HTTPException(status_code=404, detail="Conglomerate not found")

    rows = (
        (
            await db.execute(
                text(f"""
            {_WL_CTE}
            SELECT p.id, p.name, p.emoji, p.city, p.tier, p.elo,
                   COALESCE(wl_agg.wins, 0) AS wins,
                   COALESCE(wl_agg.losses, 0) AS losses
            FROM programs p
            LEFT JOIN wl_agg ON wl_agg.pid = p.id
            WHERE p.conglomerate_id = :cid
            ORDER BY p.tier, p.elo DESC
        """),
                {"cid": conglomerate_id},
            )
        )
        .mappings()
        .all()
    )

    tier1 = [ProgramStanding.model_validate(dict(r)) for r in rows if r["tier"] == 1]
    tier2 = [ProgramStanding.model_validate(dict(r)) for r in rows if r["tier"] == 2]
    return ConglomerateStandings(
        conglomerate=ConglomerateOut.model_validate(dict(cong_row)),
        tier1=tier1,
        tier2=tier2,
    )
