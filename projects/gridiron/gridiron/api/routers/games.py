from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from gridiron.config import EMIT_INTERVAL

from gridiron.api.schemas import (
    GameBoxscore,
    GameDetail,
    GameList,
    GameSummary,
    PlayerBoxscore,
    ProgramRef,
)
from gridiron.database import get_db

router = APIRouter()


@router.get("/games", response_model=GameList)
async def list_games(
    status: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> GameList:
    # ponytail: conditional WHERE string is safe — branch on a literal, value parameterised
    _w = "AND g.status = :status" if status else ""
    params: dict = {"limit": limit, "offset": offset}
    if status:
        params["status"] = status

    total = (
        await db.execute(text(f"SELECT COUNT(*) FROM games g WHERE g.season=1 {_w}"), params)
    ).scalar() or 0

    rows = (
        (
            await db.execute(
                text(f"""
        SELECT g.id AS game_id, g.week, g.broadcast_slot, g.status,
               g.home_score, g.away_score,
               hp.name AS home_name, ap.name AS away_name
        FROM games g
        JOIN programs hp ON hp.id = g.home_program_id
        JOIN programs ap ON ap.id = g.away_program_id
        WHERE g.season=1 {_w}
        ORDER BY g.week DESC, g.id DESC
        LIMIT :limit OFFSET :offset
    """),
                params,
            )
        )
        .mappings()
        .all()
    )

    return GameList(
        total=int(total),
        games=[GameSummary.model_validate(dict(r)) for r in rows],
    )


@router.get("/games/{game_id}", response_model=GameDetail)
async def get_game(game_id: int, db: AsyncSession = Depends(get_db)) -> GameDetail:
    row = (
        (
            await db.execute(
                text("""
        SELECT g.id, g.week, g.broadcast_slot, g.status,
               g.is_rivalry, g.is_postseason, g.elo_tiebreak,
               g.home_score, g.away_score,
               g.home_program_id, hp.name AS home_name, hp.emoji AS home_emoji,
               hp.city AS home_city, g.home_elo_pre, g.home_elo_post,
               g.away_program_id, ap.name AS away_name, ap.emoji AS away_emoji,
               ap.city AS away_city, g.away_elo_pre, g.away_elo_post
        FROM games g
        JOIN programs hp ON hp.id = g.home_program_id
        JOIN programs ap ON ap.id = g.away_program_id
        WHERE g.id = :gid
    """),
                {"gid": game_id},
            )
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Game not found")

    return GameDetail(
        id=row["id"],
        week=row["week"],
        broadcast_slot=row["broadcast_slot"],
        status=row["status"],
        is_rivalry=row["is_rivalry"],
        is_postseason=row["is_postseason"],
        elo_tiebreak=row["elo_tiebreak"],
        home_score=row["home_score"],
        away_score=row["away_score"],
        home=ProgramRef(
            program_id=row["home_program_id"],
            name=row["home_name"],
            emoji=row["home_emoji"],
            city=row["home_city"],
            elo_pre=row["home_elo_pre"],
            elo_post=row["home_elo_post"],
        ),
        away=ProgramRef(
            program_id=row["away_program_id"],
            name=row["away_name"],
            emoji=row["away_emoji"],
            city=row["away_city"],
            elo_pre=row["away_elo_pre"],
            elo_post=row["away_elo_post"],
        ),
    )


@router.get("/games/{game_id}/plays")
async def game_plays(game_id: int, db: AsyncSession = Depends(get_db)) -> list[dict]:
    exists = (
        await db.execute(text("SELECT 1 FROM games WHERE id = :gid"), {"gid": game_id})
    ).scalar()
    if not exists:
        raise HTTPException(status_code=404, detail="Game not found")

    game_row = (
        await db.execute(
            text("SELECT status, replay_started_at FROM games WHERE id=:gid"),
            {"gid": game_id},
        )
    ).fetchone()

    max_play: int | None = None
    if game_row and game_row[0] == "live" and game_row[1] is not None:
        elapsed = (datetime.now(timezone.utc) - game_row[1]).total_seconds()
        max_play = max(0, int(elapsed / EMIT_INTERVAL))

    rows = (
        (
            await db.execute(
                text("""
        SELECT play_number, quarter, possession, play_type,
               yards_gained, field_pos_before, field_pos_after,
               score_home, score_away, description, down, distance
        FROM play_log
        WHERE game_id = :gid
          AND (CAST(:max_play AS INTEGER) IS NULL OR play_number <= CAST(:max_play AS INTEGER))
        ORDER BY play_number
    """),
                {"gid": game_id, "max_play": max_play},
            )
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]


@router.get("/games/{game_id}/boxscore", response_model=GameBoxscore)
async def game_boxscore(game_id: int, db: AsyncSession = Depends(get_db)) -> GameBoxscore:
    game_row = (
        (
            await db.execute(
                text("""
        SELECT id, home_program_id, away_program_id, status, replay_started_at
        FROM games WHERE id = :gid
    """),
                {"gid": game_id},
            )
        )
        .mappings()
        .one_or_none()
    )
    if game_row is None:
        raise HTTPException(status_code=404, detail="Game not found")

    # Live games: compute from play_log up to the time-gated max_play
    if game_row["status"] == "live" and game_row["replay_started_at"] is not None:
        return await _live_boxscore(
            game_id,
            game_row["home_program_id"],
            game_row["away_program_id"],
            game_row["replay_started_at"],
            db,
        )

    # Complete (or fallback): read from player_game_stats
    rows = (
        (
            await db.execute(
                text("""
        SELECT pgs.player_id, pgs.program_id,
               pl.first_name || ' ' || pl.last_name AS name, pl.position,
               pgs.pass_yards, pgs.pass_tds, pgs.pass_attempts, pgs.pass_completions,
               pgs.rush_yards, pgs.rush_tds, pgs.rush_attempts,
               pgs.receiving_yards, pgs.receiving_tds, pgs.receptions, pgs.targets,
               pgs.sacks, pgs.ints_def
        FROM player_game_stats pgs
        JOIN players pl ON pl.id = pgs.player_id
        WHERE pgs.game_id = :gid
          AND (pgs.pass_yards > 0 OR pgs.rush_yards > 0 OR pgs.receiving_yards > 0
               OR pgs.sacks > 0 OR pgs.ints_def > 0)
        ORDER BY pgs.program_id, pl.position, pl.id
    """),
                {"gid": game_id},
            )
        )
        .mappings()
        .all()
    )

    home_id = game_row["home_program_id"]
    away_id = game_row["away_program_id"]
    home: list[PlayerBoxscore] = []
    away: list[PlayerBoxscore] = []
    for r in rows:
        stat = PlayerBoxscore.model_validate(dict(r))
        if r["program_id"] == home_id:
            home.append(stat)
        elif r["program_id"] == away_id:
            away.append(stat)
    return GameBoxscore(home=home, away=away)


async def _live_boxscore(
    game_id: int,
    home_program_id: int,
    away_program_id: int,
    replay_started_at: datetime,
    db: AsyncSession,
) -> GameBoxscore:
    elapsed = (datetime.now(timezone.utc) - replay_started_at).total_seconds()
    max_play = max(0, int(elapsed / EMIT_INTERVAL))

    # Rush stats
    rush_rows = (
        await db.execute(
            text("""
        SELECT pll.primary_player_id,
               pl.last_name AS name, pl.position, pl.program_id,
               SUM(CASE WHEN pll.play_type='RUSH' THEN COALESCE(pll.yards_gained,0) ELSE 0 END)::int AS rush_yards,
               COUNT(CASE WHEN pll.play_type='RUSH' THEN 1 END)::int AS rush_attempts
        FROM play_log pll
        JOIN players pl ON pl.id = pll.primary_player_id
        WHERE pll.game_id = :gid
          AND pll.play_type IN ('RUSH','TACKLE_FOR_LOSS')
          AND pll.play_number <= :max_play
        GROUP BY pll.primary_player_id, pl.last_name, pl.position, pl.program_id
    """),
            {"gid": game_id, "max_play": max_play},
        )
    ).mappings().all()

    # Receiving stats
    rec_rows = (
        await db.execute(
            text("""
        SELECT pll.primary_player_id,
               pl.last_name AS name, pl.position, pl.program_id,
               SUM(CASE WHEN pll.play_type='PASS_COMPLETE' THEN COALESCE(pll.yards_gained,0) ELSE 0 END)::int AS receiving_yards,
               COUNT(CASE WHEN pll.play_type='PASS_COMPLETE' THEN 1 END)::int AS receptions,
               COUNT(*)::int AS targets
        FROM play_log pll
        JOIN players pl ON pl.id = pll.primary_player_id
        WHERE pll.game_id = :gid
          AND pll.play_type IN ('PASS_COMPLETE','PASS_INCOMPLETE','PASS_DEFLECTION')
          AND pll.play_number <= :max_play
        GROUP BY pll.primary_player_id, pl.last_name, pl.position, pl.program_id
    """),
            {"gid": game_id, "max_play": max_play},
        )
    ).mappings().all()

    # Build per-player stat map, merge rush + rec
    stats: dict[int, dict] = {}
    for r in rush_rows:
        pid = r["primary_player_id"]
        stats[pid] = {
            "player_id": pid, "name": r["name"], "position": r["position"],
            "program_id": r["program_id"],
            "rush_yards": r["rush_yards"], "rush_attempts": r["rush_attempts"],
            "rush_tds": 0,
            "receiving_yards": 0, "receptions": 0, "targets": 0, "receiving_tds": 0,
            "pass_yards": 0, "pass_attempts": 0, "pass_completions": 0, "pass_tds": 0,
            "sacks": 0, "ints_def": 0,
        }
    for r in rec_rows:
        pid = r["primary_player_id"]
        if pid not in stats:
            stats[pid] = {
                "player_id": pid, "name": r["name"], "position": r["position"],
                "program_id": r["program_id"],
                "rush_yards": 0, "rush_attempts": 0, "rush_tds": 0,
                "pass_yards": 0, "pass_attempts": 0, "pass_completions": 0, "pass_tds": 0,
                "sacks": 0, "ints_def": 0,
            }
        stats[pid]["receiving_yards"] = r["receiving_yards"]
        stats[pid]["receptions"] = r["receptions"]
        stats[pid]["targets"] = r["targets"]
        stats[pid]["receiving_tds"] = 0

    # Passing stats: top QB per team credited with team's total pass production
    for prog_id in (home_program_id, away_program_id):
        qb_row = (
            await db.execute(
                text("""
            SELECT id AS qb_id, last_name FROM players
            WHERE program_id = :pid AND position = 'QB'
            ORDER BY alpha DESC LIMIT 1
        """),
                {"pid": prog_id},
            )
        ).mappings().one_or_none()
        if qb_row is None:
            continue
        pass_agg = (
            await db.execute(
                text("""
            SELECT COUNT(CASE WHEN pll.play_type='PASS_COMPLETE' THEN 1 END)::int AS pass_completions,
                   COUNT(*)::int AS pass_attempts,
                   SUM(CASE WHEN pll.play_type='PASS_COMPLETE' THEN COALESCE(pll.yards_gained,0) ELSE 0 END)::int AS pass_yards
            FROM play_log pll
            JOIN players pl ON pl.id = pll.primary_player_id
            WHERE pll.game_id = :gid
              AND pll.play_type IN ('PASS_COMPLETE','PASS_INCOMPLETE','PASS_DEFLECTION')
              AND pll.play_number <= :max_play
              AND pl.program_id = :pid
        """),
                {"gid": game_id, "pid": prog_id, "max_play": max_play},
            )
        ).mappings().one_or_none()
        if pass_agg is None or pass_agg["pass_attempts"] == 0:
            continue
        qb_id = qb_row["qb_id"]
        if qb_id not in stats:
            stats[qb_id] = {
                "player_id": qb_id, "name": qb_row["last_name"], "position": "QB",
                "program_id": prog_id,
                "rush_yards": 0, "rush_attempts": 0, "rush_tds": 0,
                "receiving_yards": 0, "receptions": 0, "targets": 0, "receiving_tds": 0,
                "sacks": 0, "ints_def": 0,
            }
        stats[qb_id]["pass_yards"] = pass_agg["pass_yards"]
        stats[qb_id]["pass_completions"] = pass_agg["pass_completions"]
        stats[qb_id]["pass_attempts"] = pass_agg["pass_attempts"]
        stats[qb_id]["pass_tds"] = 0

    home: list[PlayerBoxscore] = []
    away: list[PlayerBoxscore] = []
    for s in stats.values():
        # skip players with no meaningful stats yet
        if not any(s.get(k, 0) for k in ("rush_yards", "receiving_yards", "pass_yards")):
            continue
        stat = PlayerBoxscore.model_validate(s)
        if s["program_id"] == home_program_id:
            home.append(stat)
        else:
            away.append(stat)
    return GameBoxscore(home=home, away=away)
