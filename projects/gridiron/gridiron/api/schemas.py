from __future__ import annotations

from pydantic import BaseModel, ConfigDict

_ORM = ConfigDict(from_attributes=True)


class ConglomerateOut(BaseModel):
    model_config = _ORM
    id: int
    code: str
    full_name: str
    network: str
    region: str
    primary_color: str
    secondary_color: str


class ProgramStanding(BaseModel):
    id: int
    name: str
    emoji: str
    city: str
    elo: float
    wins: int
    losses: int


class ConglomerateStandings(BaseModel):
    conglomerate: ConglomerateOut
    tier1: list[ProgramStanding]
    tier2: list[ProgramStanding]


class ProgramSummary(BaseModel):
    id: int
    name: str
    emoji: str
    city: str
    tier: int
    conglomerate_code: str
    elo: float
    wins: int
    losses: int


class ProgramDetail(BaseModel):
    id: int
    name: str
    emoji: str
    city: str
    mascot: str
    tier: int
    elo: float
    wins: int
    losses: int
    primary_color: str
    secondary_color: str
    conglomerate_id: int
    conglomerate_code: str


class ProgramScheduleGame(BaseModel):
    game_id: int
    week: int
    broadcast_slot: str
    is_home: bool
    opponent_name: str
    opponent_emoji: str
    status: str
    home_score: int | None
    away_score: int | None


class PlayerRoster(BaseModel):
    player_id: int
    first_name: str
    last_name: str
    position: str
    year: int
    jersey_num: int


class StatLeader(BaseModel):
    player_id: int
    name: str
    total_yards: int
    tds: int
    games_played: int


class ProgramStats(BaseModel):
    passers: list[StatLeader]
    rushers: list[StatLeader]
    receivers: list[StatLeader]


class ScheduleGame(BaseModel):
    game_id: int
    week: int
    broadcast_slot: str
    home_program_id: int
    home_name: str
    home_emoji: str
    away_program_id: int
    away_name: str
    away_emoji: str
    status: str
    home_score: int | None
    away_score: int | None


class WeekSchedule(BaseModel):
    week: int
    games: list[ScheduleGame]


class GameSummary(BaseModel):
    game_id: int
    week: int
    broadcast_slot: str
    status: str
    home_name: str
    away_name: str
    home_score: int | None
    away_score: int | None


class GameList(BaseModel):
    total: int
    games: list[GameSummary]


class ProgramRef(BaseModel):
    program_id: int
    name: str
    emoji: str
    city: str
    elo_pre: float | None
    elo_post: float | None


class GameDetail(BaseModel):
    id: int
    week: int
    broadcast_slot: str
    status: str
    is_rivalry: bool
    is_postseason: bool
    elo_tiebreak: bool
    home_score: int | None
    away_score: int | None
    home: ProgramRef
    away: ProgramRef


class PlayerBoxscore(BaseModel):
    player_id: int
    name: str
    position: str
    pass_yards: int
    pass_tds: int
    pass_attempts: int
    pass_completions: int
    rush_yards: int
    rush_tds: int
    rush_attempts: int
    receiving_yards: int
    receiving_tds: int
    receptions: int
    targets: int
    sacks: int
    ints_def: int


class GameBoxscore(BaseModel):
    home: list[PlayerBoxscore]
    away: list[PlayerBoxscore]


class LeaderboardEntry(BaseModel):
    player_id: int
    name: str
    program_name: str
    total_yards: int
    tds: int
    games_played: int


class Leaderboards(BaseModel):
    passers: list[LeaderboardEntry]
    rushers: list[LeaderboardEntry]
    receivers: list[LeaderboardEntry]
